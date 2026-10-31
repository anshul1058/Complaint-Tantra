from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_AUTHORITY, ROLE_SENIOR, get_current_user, require_roles
from db import get_db
from models import Alert, Case, Institution, User
from schemas import DashboardSummaryOut, HeatmapRow, WorkloadRow

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

OPEN_STATUSES = ("Received", "UnderProcess", "Transferred", "Escalated", "Reopened")


def _scoped(stmt, user: User):
    if user.role in ("officer", "regional"):
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
    rows = (await db.execute(_scoped(select(Case), user))).scalars().all()

    status_counts: dict[str, int] = {}
    bureau_counts: dict[str, int] = {}
    scores = []
    overdue = due_soon = 0
    for case in rows:
        status_counts[case.status] = status_counts.get(case.status, 0) + 1
        bureau_counts[case.assigned_bureau] = bureau_counts.get(case.assigned_bureau, 0) + 1
        if case.priority_score is not None:
            scores.append(case.priority_score)
        if _overdue(case, now):
            overdue += 1
        elif (
            case.status != "Disposed"
            and case.expected_disposal is not None
            and case.expected_disposal <= now + timedelta(days=3)
        ):
            due_soon += 1

    safety_stmt = select(func.count(func.distinct(Alert.case_id))).where(
        Alert.kind.in_(("safety", "safety_flag"))
    )
    safety_flagged = (await db.execute(safety_stmt)).scalar() or 0

    return DashboardSummaryOut(
        total=len(rows),
        pending=status_counts.get("Received", 0),
        under_process=status_counts.get("UnderProcess", 0),
        disposed=status_counts.get("Disposed", 0),
        transferred=status_counts.get("Transferred", 0),
        escalated=status_counts.get("Escalated", 0),
        reopened=status_counts.get("Reopened", 0),
        overdue=overdue,
        due_soon=due_soon,
        safety_flagged=safety_flagged,
        open=sum(status_counts.get(s, 0) for s in OPEN_STATUSES),
        by_status=status_counts,
        by_bureau=bureau_counts,
        avg_priority=round(sum(scores) / len(scores), 1) if scores else None,
    )


@router.get("/workload", response_model=list[WorkloadRow])
async def workload(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, "admin"))],
) -> list[WorkloadRow]:
    now = datetime.now(timezone.utc)
    rows = (await db.execute(select(Case))).scalars().all()
    agg: dict[str, dict] = {}
    for case in rows:
        a = agg.setdefault(case.assigned_bureau, {
            "pending": 0, "under_process": 0, "disposed": 0, "transferred": 0,
            "escalated": 0, "reopened": 0, "overdue": 0, "total": 0,
        })
        a["total"] += 1
        key = {
            "Received": "pending",
            "UnderProcess": "under_process",
            "Disposed": "disposed",
            "Transferred": "transferred",
            "Escalated": "escalated",
            "Reopened": "reopened",
        }.get(case.status)
        if key:
            a[key] += 1
        if _overdue(case, now):
            a["overdue"] += 1
    return [WorkloadRow(bureau=b, **a) for b, a in sorted(agg.items())]


@router.get("/heatmap", response_model=list[HeatmapRow])
async def heatmap(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, "admin"))],
) -> list[HeatmapRow]:
    now = datetime.now(timezone.utc)
    rows = (await db.execute(
        select(Institution.region, Institution.state, Case)
        .join(Case, Case.institution_id == Institution.id)
    )).all()
    agg: dict[tuple[str, str], dict] = {}
    for region, state, case in rows:
        key = (region or "Unknown", state or "Unspecified")
        a = agg.setdefault(key, {"count": 0, "overdue": 0, "critical": 0})
        a["count"] += 1
        if _overdue(case, now):
            a["overdue"] += 1
        if case.criticality == "C1" and case.status != "Disposed":
            a["critical"] += 1
    out = [HeatmapRow(region=r, state=s, **a) for (r, s), a in agg.items()]
    return sorted(out, key=lambda x: x.count, reverse=True)
