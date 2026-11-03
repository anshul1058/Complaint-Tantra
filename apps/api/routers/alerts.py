from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import WIDE_ROLES, get_current_user
from db import get_db
from models import Alert, Case, Institution, User
from schemas import AlertOut, AlertSnoozeIn, DigestOut

router = APIRouter(prefix="/alerts", tags=["alerts"])

OPEN_STATUSES = ("Received", "UnderProcess", "Transferred", "Escalated", "Reopened")


def _scope(user: User, stmt):
    if user.role in WIDE_ROLES:
        return stmt
    return stmt.where(Case.assigned_bureau == user.bureau)


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    kind: str | None = None,
    limit: int = Query(50, le=200),
) -> list[AlertOut]:
    """Scoped: alerts targeted at this user/role, or for cases in their bureau."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(Alert)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .where(or_(Alert.snoozed_until.is_(None), Alert.snoozed_until <= now))
    )
    conds = [
        Alert.target_user == user.id,
        Alert.target_role == user.role,
        Alert.target_role.is_(None),
        Alert.case_id.in_(
            _scope(user, select(Case.id)).where(Case.assigned_bureau == user.bureau)
        ),
    ]
    stmt = stmt.where(or_(*conds))
    if kind:
        stmt = stmt.where(Alert.kind == kind)
    rows = (await db.execute(stmt)).scalars().all()

    case_ids = {a.case_id for a in rows if a.case_id}
    inst_ids = {a.institution_id for a in rows if a.institution_id}
    cases = {
        c.id: c for c in (await db.execute(select(Case).where(Case.id.in_(case_ids)))).scalars()
    } if case_ids else {}
    insts = {
        i.id: i for i in (await db.execute(
            select(Institution).where(Institution.id.in_(inst_ids))
        )).scalars()
    } if inst_ids else {}

    out = []
    for alert in rows:
        a = AlertOut.model_validate(alert)
        case = cases.get(alert.case_id)
        if case:
            a.case_no = case.case_no
            a.institution_id = a.institution_id or case.institution_id
        inst = insts.get(a.institution_id)
        if inst:
            a.institution_name = inst.name
        out.append(a)
    return out


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge(
    alert_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AlertOut:
    import uuid as _uuid

    try:
        alert = await db.get(Alert, _uuid.UUID(alert_id))
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.post("/{alert_id}/snooze", response_model=AlertOut)
async def snooze(
    alert_id: str,
    body: AlertSnoozeIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AlertOut:
    import uuid as _uuid

    try:
        alert = await db.get(Alert, _uuid.UUID(alert_id))
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    hours = max(1, min(body.hours, 24 * 30))
    alert.snoozed_until = datetime.now(timezone.utc) + timedelta(hours=hours)
    await db.commit()
    await db.refresh(alert)
    return AlertOut.model_validate(alert)


@router.get("/digest", response_model=DigestOut)
async def digest(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    hours: int = Query(24, ge=1, le=168),
) -> DigestOut:
    import asyncio

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    now = datetime.now(timezone.utc)
    cases = (await db.execute(_scope(user, select(Case)))).scalars().all()
    open_cases = [c for c in cases if c.status in OPEN_STATUSES]
    overdue = [c for c in open_cases if c.expected_disposal and c.expected_disposal < now]
    new_cases = [c for c in cases if c.received_at and c.received_at >= since]
    safety = [a for a in (await db.execute(
        select(Alert).where(Alert.kind.in_(("safety", "safety_flag")), Alert.created_at >= since)
    )).scalars()]
    high = sorted(
        [c for c in open_cases if (c.priority_score or 0) >= 60],
        key=lambda c: c.priority_score or 0,
        reverse=True,
    )[:10]
    narrative = (
        f"{len(open_cases)} open cases, {len(overdue)} overdue, "
        f"{len(new_cases)} received in the last {hours}h, {len(safety)} safety flags."
    )
    try:
        from agents.llm import complete_json

        out, _ = await asyncio.to_thread(
            complete_json,
            "Summarise this operational digest for an AICTE officer in 2 sentences. "
            f"Facts: {narrative}",
            None,
        )
        narrative = out.get("summary") or out.get("text") or narrative
    except Exception:
        pass
    return DigestOut(
        since=since,
        total_open=len(open_cases),
        overdue=len(overdue),
        safety_flagged=len(safety),
        new_cases=len(new_cases),
        high_priority=[
            {"id": str(c.id), "case_no": c.case_no, "priority_score": c.priority_score}
            for c in high
        ],
        narrative=narrative,
    )
