import uuid
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    ROLE_AUTHORITY,
    ROLE_OFFICER,
    ROLE_REGIONAL,
    ROLE_SENIOR,
    WIDE_ROLES,
    can_act_on_case,
    can_see_full_case,
    get_current_user,
    require_roles,
)
from db import get_db
from models import Alert, Case, CaseAction, CaseLink, Institution, User
from schemas import (
    ActionOut,
    CaseActionRequest,
    CaseCreate,
    CaseDetailOut,
    CaseOut,
    CaseRedactedOut,
    LinkDecisionRequest,
    LinkOut,
    ManualLinkRequest,
    QueueRow,
)
from services.case_service import apply_action, case_flags
from services.state_machine import TransitionError

router = APIRouter(tags=["cases"])


def _redacted(case: Case, institution_name: str | None, officer: User | None) -> CaseRedactedOut:
    return CaseRedactedOut(
        id=case.id,
        case_no=case.case_no,
        institution_name=institution_name or case.raw_institution,
        category=case.category,
        status=case.status,
        assigned_bureau=case.assigned_bureau,
        assigned_officer=case.assigned_officer,
        officer_contact=officer.email if officer else None,
    )


def _scope_clause(user: User):
    """Every query scoped by bureau/region per RBAC §8."""
    if user.role in WIDE_ROLES:
        return None
    if user.role == ROLE_REGIONAL:
        clauses = [Case.assigned_bureau == user.bureau]
        if user.region:
            clauses.append(Institution.region == user.region)
        return or_(*clauses)
    return Case.assigned_bureau == user.bureau


async def _get_scoped(db: AsyncSession, case_id: uuid.UUID, user: User) -> tuple[Case, bool]:
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    full = can_see_full_case(user, case.assigned_bureau)
    if not full and user.role not in (ROLE_OFFICER, ROLE_REGIONAL):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Out of scope")
    if not full:
        # Officer of another bureau: allowed only as redacted view (§8)
        pass
    return case, full


@router.get("/cases", response_model=list[CaseOut])
async def list_cases(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    institution: uuid.UUID | None = None,
    case_no: str | None = None,
    bureau: str | None = None,
    region: str | None = None,
    category: str | None = None,
    status_: str | None = Query(None, alias="status"),
    received_from: datetime | None = None,
    received_to: datetime | None = None,
    sort: Literal["priority", "received", "status"] = "priority",
    limit: int = Query(50, le=200),
    offset: int = 0,
) -> list[CaseOut]:
    stmt = select(Case).outerjoin(Institution, Case.institution_id == Institution.id)
    clause = _scope_clause(user)
    if clause is not None:
        stmt = stmt.where(clause)
    if institution:
        stmt = stmt.where(Case.institution_id == institution)
    if case_no:
        stmt = stmt.where(Case.case_no.ilike(f"%{case_no}%"))
    if bureau:
        stmt = stmt.where(Case.assigned_bureau == bureau)
    if region:
        stmt = stmt.where(Institution.region == region)
    if category:
        stmt = stmt.where(Case.category == category)
    if status_:
        stmt = stmt.where(Case.status == status_)
    if received_from:
        stmt = stmt.where(Case.received_at >= received_from)
    if received_to:
        stmt = stmt.where(Case.received_at <= received_to)

    if sort == "priority":
        stmt = stmt.order_by(Case.priority_score.desc().nullslast(), Case.received_at.desc())
    elif sort == "received":
        stmt = stmt.order_by(Case.received_at.desc())
    else:
        stmt = stmt.order_by(Case.status, Case.received_at.desc())

    rows = (await db.execute(stmt.limit(limit).offset(offset))).scalars().all()
    now = datetime.now(timezone.utc)
    out = []
    for c in rows:
        o = CaseOut.model_validate(c)
        f = case_flags(c, now)
        o.overdue = f["overdue"]
        o.allowed_actions = f["allowed_actions"]
        out.append(o)
    return out


@router.get("/cases/{case_id}", response_model=CaseDetailOut | CaseRedactedOut)
async def get_case(
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    case, full = await _get_scoped(db, case_id, user)
    inst = await db.get(Institution, case.institution_id) if case.institution_id else None
    if not full:
        officer = await db.get(User, case.assigned_officer) if case.assigned_officer else None
        return _redacted(case, inst.name if inst else None, officer)

    actions = (await db.execute(
        select(CaseAction).where(CaseAction.case_id == case.id).order_by(CaseAction.created_at)
    )).scalars().all()
    officer = await db.get(User, case.assigned_officer) if case.assigned_officer else None
    detail = CaseDetailOut.model_validate(case)
    flags = case_flags(case)
    detail.overdue = flags["overdue"]
    detail.allowed_actions = flags["allowed_actions"]
    detail.timeline = [ActionOut.model_validate(a) for a in actions]
    detail.institution_name = inst.name if inst else case.raw_institution
    if not can_see_full_case(user, case.assigned_bureau):
        # redacted: strip text + AI internals
        detail.text_original = None
        detail.text_english = None
        detail.ai_summary = None
        detail.priority_reasons = None
        detail.case_brief = None
    else:
        try:
            from agents.briefing import write_brief

            ctx = {
                "priority_score": case.priority_score,
                "priority_reasons": case.priority_reasons,
                "overlaps": [],
                "institution_track_record": None,
            }
            detail.case_brief = write_brief(
                {
                    "case_no": case.case_no,
                    "category": case.category,
                    "criticality": case.criticality,
                    "ai_summary": case.ai_summary,
                    "status": case.status,
                },
                ctx,
            )
        except Exception:
            detail.case_brief = None
    return detail


@router.post("/cases/{case_id}/actions", response_model=CaseDetailOut)
async def post_action(
    case_id: uuid.UUID,
    body: CaseActionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(ROLE_OFFICER, ROLE_REGIONAL, ROLE_SENIOR, ROLE_AUTHORITY))],
) -> CaseDetailOut:
    case, full = await _get_scoped(db, case_id, user)
    if not can_act_on_case(user, case.assigned_bureau):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot act on this case")
    if body.action == "disposed" and case.status == "Escalated" and user.role in (ROLE_OFFICER, ROLE_REGIONAL):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dispose of escalated case requires senior+")
    try:
        case = await apply_action(db, case, body.action, actor=user,
                                  remarks=body.remarks, payload=body.payload)
    except TransitionError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))

    if body.action == "escalated":
        db.add(Alert(
            kind="escalation", case_id=case.id, severity="high",
            message=f"{case.case_no} escalated by {user.name}", target_role="senior",
        ))
        await db.commit()
    if body.action in ("assigned", "transferred") and not case.priority_score:
        case.priority_reasons = None

    inst = await db.get(Institution, case.institution_id) if case.institution_id else None
    actions = (await db.execute(
        select(CaseAction).where(CaseAction.case_id == case.id).order_by(CaseAction.created_at)
    )).scalars().all()
    detail = CaseDetailOut.model_validate(case)
    flags = case_flags(case)
    detail.overdue = flags["overdue"]
    detail.allowed_actions = flags["allowed_actions"]
    detail.timeline = [ActionOut.model_validate(a) for a in actions]
    detail.institution_name = inst.name if inst else case.raw_institution
    return detail


@router.get("/cases/{case_id}/overlaps", response_model=list[LinkOut])
async def case_overlaps(
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[LinkOut]:
    case, full = await _get_scoped(db, case_id, user)
    links = (await db.execute(
        select(CaseLink).where(or_(CaseLink.case_a == case.id, CaseLink.case_b == case.id))
    )).scalars().all()
    out = []
    for link in links:
        other_id = link.case_b if link.case_a == case.id else link.case_a
        other = await db.get(Case, other_id)
        if other is None:
            continue
        lo = LinkOut.model_validate(link)
        # Cross-bureau: redacted summary only (§8)
        if can_see_full_case(user, other.assigned_bureau):
            inst = await db.get(Institution, other.institution_id) if other.institution_id else None
            lo.other_case = _redacted(
                other,
                inst.name if inst else other.raw_institution,
                await db.get(User, other.assigned_officer) if other.assigned_officer else None,
            )
        else:
            inst = await db.get(Institution, other.institution_id) if other.institution_id else None
            lo.other_case = _redacted(
                other,
                inst.name if inst else other.raw_institution,
                await db.get(User, other.assigned_officer) if other.assigned_officer else None,
            )
        out.append(lo)
    return out


@router.post("/overlaps/{link_id}/decision", response_model=LinkOut)
async def overlap_decision(
    link_id: uuid.UUID,
    body: LinkDecisionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(ROLE_OFFICER, ROLE_REGIONAL, ROLE_SENIOR, ROLE_AUTHORITY))],
) -> LinkOut:
    if body.decision not in ("confirmed", "rejected"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "decision must be confirmed|rejected")
    link = await db.get(CaseLink, link_id)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")
    # Officer can decide if either side is in their scope (§8: confirm/reject overlap)
    case_a = await db.get(Case, link.case_a)
    case_b = await db.get(Case, link.case_b)
    in_scope = any(
        c is not None and can_act_on_case(user, c.assigned_bureau) for c in (case_a, case_b)
    )
    if not in_scope:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Out of scope")
    link.decision = body.decision
    link.decided_by = user.id
    link.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(link)
    return LinkOut.model_validate(link)


@router.post("/cases/{case_id}/link", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
async def manual_link(
    case_id: uuid.UUID,
    body: ManualLinkRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(ROLE_OFFICER, ROLE_REGIONAL, ROLE_SENIOR, ROLE_AUTHORITY))],
) -> LinkOut:
    case = await db.get(Case, case_id)
    other = await db.get(Case, body.case_b)
    if case is None or other is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    if not can_act_on_case(user, case.assigned_bureau):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Out of scope")
    a, b = sorted([str(case.id), str(other.id)])
    link = CaseLink(
        case_a=uuid.UUID(a), case_b=uuid.UUID(b),
        tier=body.tier, confidence=1.0, evidence=body.evidence or {"reasoning": "officer manual link"},
        detected_by="officer", decision="confirmed", decided_by=user.id,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return LinkOut.model_validate(link)


@router.get("/queue/priority", response_model=list[QueueRow])
async def priority_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, le=200),
) -> list[QueueRow]:
    stmt = select(Case).where(Case.status.notin_(("Disposed",)))
    clause = _scope_clause(user)
    if clause is not None:
        stmt = stmt.where(clause)
    stmt = stmt.order_by(Case.priority_score.desc().nullslast(), Case.received_at).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    now = datetime.now(timezone.utc)
    out = []
    for c in rows:
        o = QueueRow.model_validate(c)
        flags = case_flags(c, now)
        o.overdue = flags["overdue"]
        o.allowed_actions = flags["allowed_actions"]
        out.append(o)
    return out
