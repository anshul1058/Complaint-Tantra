from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_AUTHORITY, ROLE_SENIOR, get_current_user, require_roles
from db import get_db
from models import Alert, Case, Institution, User
from schemas import DashboardSummaryOut, HeatmapRow, WorkloadRow

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

OPEN_STATUSES = ("Received", "UnderProcess", "Transferred", "Escalated", "Reopened")


def _scoped(stmt, user: User):
    if user.role in ("officer", "regional"):
        if user.role == "officer":
            return stmt.where((Case.assigned_bureau == user.bureau) | (Case.source_bureau == "PUBLIC"))
        return stmt.where(Case.assigned_bureau == user.bureau)
    return stmt


def _overdue(case: Case, now: datetime) -> bool:
    return (
        case.status != "Disposed"
        and case.expected_disposal is not None
        and case.expected_disposal < now
    )


@router.get("/summary", response_model=DashboardSummaryOut)
async def summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DashboardSummaryOut:
    """KPI counts — numbers from SQL only (§7, §6.6)."""
    now = datetime.now(timezone.utc)
    # Keep the aggregate subquery narrow. Selecting the ORM entity here also
    # pulls large text/embedding columns into the database workset even though
    # the dashboard only needs these five scalar fields.
    scoped = _scoped(select(
        Case.id,
        Case.status,
        Case.expected_disposal,
        Case.priority_score,
        Case.assigned_bureau,
    ), user).subquery()
    total, overdue, due_soon, avg_priority = (await db.execute(
        select(
            func.count(scoped.c.id),
            func.count().filter(and_(
                scoped.c.status != "Disposed",
                scoped.c.expected_disposal.is_not(None),
                scoped.c.expected_disposal < now,
            )),
            func.count().filter(and_(
                scoped.c.status != "Disposed",
                scoped.c.expected_disposal.is_not(None),
                scoped.c.expected_disposal >= now,
                scoped.c.expected_disposal <= now + timedelta(days=3),
            )),
            func.avg(scoped.c.priority_score),
        )
    )).one()

    status_rows = (await db.execute(
        select(scoped.c.status, func.count()).group_by(scoped.c.status)
    )).all()
    status_counts = {status: count for status, count in status_rows}
    bureau_rows = (await db.execute(
        select(scoped.c.assigned_bureau, func.count()).group_by(scoped.c.assigned_bureau)
    )).all()
    bureau_counts = {bureau: count for bureau, count in bureau_rows}

    safety_stmt = select(func.count(func.distinct(Alert.case_id))).where(
        Alert.kind.in_(("safety", "safety_flag"))
    )
    safety_flagged = (await db.execute(safety_stmt)).scalar() or 0

    return DashboardSummaryOut(
        total=total or 0,
        pending=status_counts.get("Received", 0),
        under_process=status_counts.get("UnderProcess", 0),
        disposed=status_counts.get("Disposed", 0),
        transferred=status_counts.get("Transferred", 0),
        escalated=status_counts.get("Escalated", 0),
        reopened=status_counts.get("Reopened", 0),
        overdue=overdue or 0,
        due_soon=due_soon or 0,
        safety_flagged=safety_flagged,
        open=sum(status_counts.get(s, 0) for s in OPEN_STATUSES),
        by_status=status_counts,
        by_bureau=bureau_counts,
        avg_priority=round(float(avg_priority), 1) if avg_priority is not None else None,
    )


@router.get("/workload", response_model=list[WorkloadRow])
async def workload(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, "admin"))],
) -> list[WorkloadRow]:
    now = datetime.now(timezone.utc)
    rows = (await db.execute(
        select(
            Case.assigned_bureau,
            func.count().label("total"),
            func.count().filter(Case.status == "Received").label("pending"),
            func.count().filter(Case.status == "UnderProcess").label("under_process"),
            func.count().filter(Case.status == "Disposed").label("disposed"),
            func.count().filter(Case.status == "Transferred").label("transferred"),
            func.count().filter(Case.status == "Escalated").label("escalated"),
            func.count().filter(Case.status == "Reopened").label("reopened"),
            func.count().filter(and_(
                Case.status != "Disposed",
                Case.expected_disposal.is_not(None),
                Case.expected_disposal < now,
            )).label("overdue"),
        ).group_by(Case.assigned_bureau)
    )).mappings().all()
    return [WorkloadRow(**row) for row in rows]


@router.get("/heatmap", response_model=list[HeatmapRow])
async def heatmap(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, "admin"))],
) -> list[HeatmapRow]:
    now = datetime.now(timezone.utc)
    rows = (await db.execute(
        select(
            func.coalesce(Institution.region, "Unknown").label("region"),
            func.coalesce(Institution.state, "Unspecified").label("state"),
            func.count().label("count"),
            func.count().filter(and_(
                Case.status != "Disposed",
                Case.expected_disposal.is_not(None),
                Case.expected_disposal < now,
            )).label("overdue"),
            func.count().filter(and_(
                Case.criticality == "C1",
                Case.status != "Disposed",
            )).label("critical"),
        )
        .join(Case, Case.institution_id == Institution.id)
        .group_by(Institution.region, Institution.state)
        .order_by(func.count().desc())
    )).mappings().all()
    return [HeatmapRow(**row) for row in rows]
