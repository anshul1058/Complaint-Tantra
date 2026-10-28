from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_AUTHORITY, ROLE_SENIOR, get_current_user, require_roles
from db import get_db
from models import Case, Institution, User
from schemas import AlertOut, DashboardSummaryOut, HeatmapRow, WorkloadRow

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _scoped(stmt, user: User):
    if user.role in ("officer", "regional"):
        return stmt.where(Case.assigned_bureau == user.bureau)
    return stmt


@router.get("/summary", response_model=DashboardSummaryOut)
async def summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> DashboardSummaryOut:
    """KPI counts — numbers from SQL only (§7, §6.6)."""
    now = datetime.now(timezone.utc)

    total = (await db.execute(_scoped(select(func.count()).select_from(Case), user))).scalar() or 0

    status_rows = (await db.execute(
        _scoped(
            select(Case.status, func.count()).where(Case.status.notin_(("Disposed",))),
            user,
        ).group_by(Case.status)
    )).all()

    overdue = (await db.execute(_scoped(
        select(func.count()).select_from(Case).where(
            Case.status.notin_(("Disposed",)),
            Case.expected_disposal.is_not(None),
            Case.expected_disposal < now,
        ),
        user,
    ))).scalar() or 0

    due_soon = (await db.execute(_scoped(
        select(func.count()).select_from(Case).where(
            Case.status.notin_(("Disposed",)),
            Case.expected_disposal.is_not(None),
            Case.expected_disposal >= now,
            Case.expected_disposal <= now + timedelta(days=3),
        ),
        user,
    ))).scalar() or 0

    bureau_rows = (await db.execute(_scoped(
        select(Case.assigned_bureau, func.count()).group_by(Case.assigned_bureau),
        user,
    ))).all()
    avg_p = (await db.execute(_scoped(select(func.avg(Case.priority_score)), user))).scalar()

    return DashboardSummaryOut(
        total=total,
        open=sum(n for _, n in status_rows),
        overdue=overdue,
        due_soon=due_soon,
        by_status={s: n for s, n in status_rows},
        by_bureau={b: n for b, n in bureau_rows},
        avg_priority=round(float(avg_p), 1) if avg_p is not None else None,
    )


@router.get("/workload", response_model=list[WorkloadRow])
async def workload(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, "admin"))],
) -> list[WorkloadRow]:
    rows = (await db.execute(
        select(Case.assigned_bureau, Case.status, func.count())
        .group_by(Case.assigned_bureau, Case.status)
    )).all()
    return [WorkloadRow(bureau=b, status=s, n=n) for b, s, n in rows]


@router.get("/heatmap", response_model=list[HeatmapRow])
async def heatmap(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, "admin"))],
) -> list[HeatmapRow]:
    rows = (await db.execute(
        select(Institution.region, func.count())
        .join(Case, Case.institution_id == Institution.id)
        .group_by(Institution.region)
    )).all()
    return [HeatmapRow(region=r or "Unknown", n=n) for r, n in rows]
