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
        assigned_officer_name=officer.name if officer else None,
        officer_contact=officer.email if officer else None,
        summary=case.ai_summary,
        raw_institution=institution_name or case.raw_institution,
        text_english=case.ai_summary,
    )


_STATUS_ALIASES = {
    "under process": "UnderProcess",
    "under-process": "UnderProcess",
    "in process": "UnderProcess",
    "under_process": "UnderProcess",
}


def _canonical_status(value: str | None) -> str | None:
    if not value:
        return None
    return _STATUS_ALIASES.get(value.strip().lower(), value)


async def _enrich_cases(db: AsyncSession, rows: list[Case], now: datetime) -> list[CaseOut]:
    """Attach institution, officer, overlap and safety metadata for the frontend contract."""
    if not rows:
        return []

    inst_ids = {c.institution_id for c in rows if c.institution_id}
    officer_ids = {c.assigned_officer for c in rows if c.assigned_officer}
    insts = {
        i.id: i for i in (await db.execute(
            select(Institution).where(Institution.id.in_(inst_ids))
        )).scalars()
    } if inst_ids else {}
    officers = {
        u.id: u for u in (await db.execute(
            select(User).where(User.id.in_(officer_ids))
        )).scalars()
    } if officer_ids else {}

    case_ids = [c.id for c in rows]
    overlap_counts: dict[uuid.UUID, int] = {}
    links = (await db.execute(
        select(CaseLink).where(
            CaseLink.decision != "rejected",
            or_(CaseLink.case_a.in_(case_ids), CaseLink.case_b.in_(case_ids)),
        )
    )).scalars()
    for link in links:
        for cid in (link.case_a, link.case_b):
            if cid in case_ids:
                overlap_counts[cid] = overlap_counts.get(cid, 0) + 1

    out: list[CaseOut] = []
    for case in rows:
        inst = insts.get(case.institution_id)
        officer = officers.get(case.assigned_officer)
        reasons = case.priority_reasons or {}
        o = CaseOut.model_validate(case)
        o.institution_name = inst.name if inst else case.raw_institution
        o.institution_city = inst.city if inst else None
        o.institution_state = inst.state if inst else None
        o.assigned_officer_name = officer.name if officer else None
        o.criticality_reason = reasons.get("criticality_reason")
        o.safety_flag = bool(reasons.get("safety_flag"))
        o.safety_flag_reason = reasons.get("safety_flag_reason")
        o.overlap_count = overlap_counts.get(case.id, 0)
        flags = case_flags(case, now)
        o.overdue = flags["overdue"]
        o.allowed_actions = flags["allowed_actions"]
        out.append(o)
    return out


async def _link_case_summary(db: AsyncSession, case: Case) -> CaseRedactedOut:
    inst = await db.get(Institution, case.institution_id) if case.institution_id else None
    officer = await db.get(User, case.assigned_officer) if case.assigned_officer else None
    return _redacted(case, inst.name if inst else None, officer)


async def _enrich_actions(db: AsyncSession, actions: list[CaseAction]) -> list[ActionOut]:
    actor_ids = {a.actor_id for a in actions if a.actor_id}
    names = {
        u.id: u.name for u in (await db.execute(
            select(User).where(User.id.in_(actor_ids))
        )).scalars()
    } if actor_ids else {}
    out = []
    for a in actions:
        ao = ActionOut.model_validate(a)
        ao.actor_name = names.get(a.actor_id) or ("System" if a.actor_type == "system" else None)
        out.append(ao)
    return out


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
    search: str | None = None,
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
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(or_(
            Case.case_no.ilike(like),
            Case.raw_institution.ilike(like),
            Case.category.ilike(like),
            Case.subcategory.ilike(like),
            Case.text_original.ilike(like),
            Case.text_english.ilike(like),
            Institution.name.ilike(like),
        ))
    if bureau:
        stmt = stmt.where(Case.assigned_bureau == bureau)
    if region:
        stmt = stmt.where(Institution.region == region)
    if category:
        stmt = stmt.where(Case.category == category)
    if status_:
        stmt = stmt.where(Case.status == _canonical_status(status_))
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
    return await _enrich_cases(db, list(rows), datetime.now(timezone.utc))


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
    base = (await _enrich_cases(db, [case], datetime.now(timezone.utc)))[0]
    detail = CaseDetailOut(**base.model_dump())
    detail.timeline = await _enrich_actions(db, list(actions))
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


@router.get("/cases/{case_id}/actions", response_model=list[ActionOut])
async def case_actions(
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[ActionOut]:
    """Append-only audit timeline for a case."""
    await _get_scoped(db, case_id, user)
    actions = (await db.execute(
        select(CaseAction).where(CaseAction.case_id == case_id).order_by(CaseAction.created_at)
    )).scalars().all()
    return await _enrich_actions(db, list(actions))


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
    base = (await _enrich_cases(db, [case], datetime.now(timezone.utc)))[0]
    detail = CaseDetailOut(**base.model_dump())
    detail.timeline = await _enrich_actions(db, list(actions))
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
        lo.other_case = await _link_case_summary(db, other)
        lo.case_a_details = lo.other_case if link.case_a == other.id else await _link_case_summary(db, case)
        lo.case_b_details = lo.other_case if link.case_b == other.id else await _link_case_summary(db, case)
        out.append(lo)
    return out


@router.get("/overlaps", response_model=list[LinkOut])
async def all_overlaps(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    decision: str | None = None,
    tier: str | None = None,
    limit: int = Query(100, le=500),
) -> list[LinkOut]:
    """Every cross-bureau link visible to the user, with redacted case summaries (§8)."""
    stmt = select(CaseLink).order_by(CaseLink.confidence.desc().nullslast()).limit(limit * 4)
    if decision:
        stmt = stmt.where(CaseLink.decision == decision)
    if tier:
        stmt = stmt.where(CaseLink.tier == tier)
    out: list[LinkOut] = []
    for link in (await db.execute(stmt)).scalars():
        case_a = await db.get(Case, link.case_a)
        case_b = await db.get(Case, link.case_b)
        if case_a is None or case_b is None:
            continue
        if not (
            can_see_full_case(user, case_a.assigned_bureau)
            or can_see_full_case(user, case_b.assigned_bureau)
        ):
            continue
        lo = LinkOut.model_validate(link)
        lo.case_a_details = await _link_case_summary(db, case_a)
        lo.case_b_details = await _link_case_summary(db, case_b)
        lo.other_case = lo.case_b_details
        out.append(lo)
        if len(out) >= limit:
            break
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
    enriched = await _enrich_cases(db, list(rows), datetime.now(timezone.utc))
    return [QueueRow(**o.model_dump()) for o in enriched]
