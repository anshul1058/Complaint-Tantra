"""Report queries — numbers always from SQL, never from the LLM (§6.6)."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import Case, Institution


async def ageing(db: AsyncSession) -> list[dict]:
    now = datetime.now(timezone.utc)
    buckets = [("0-7", 0, 7), ("8-30", 8, 30), ("31-90", 31, 90), ("90+", 91, 10_000)]
    out = []
    for label, lo, hi in buckets:
        rows = await db.execute(
            select(func.count()).select_from(Case).where(
                Case.status.notin_(("Disposed",)),
                func.extract("epoch", text("now() - received_at")) / 86400 >= lo,
                func.extract("epoch", text("now() - received_at")) / 86400 < hi,
            )
        )
        out.append({"bucket": label, "n": rows.scalar() or 0})
    return out


async def disposal(db: AsyncSession, days: int = 30) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = await db.execute(
        select(Case.assigned_bureau, func.count())
        .where(Case.status == "Disposed", Case.last_action_at >= since)
        .group_by(Case.assigned_bureau)
    )
    return [{"bureau": b, "disposed": n} for b, n in rows.all()]


async def by_bureau(db: AsyncSession) -> list[dict]:
    rows = await db.execute(
        select(Case.assigned_bureau, Case.status, func.count())
        .group_by(Case.assigned_bureau, Case.status)
    )
    return [{"bureau": b, "status": s, "n": n} for b, s, n in rows.all()]


async def by_region(db: AsyncSession) -> list[dict]:
    rows = await db.execute(
        select(Institution.region, func.count())
        .join(Case, Case.institution_id == Institution.id)
        .group_by(Institution.region)
    )
    return [{"region": r, "n": n} for r, n in rows.all()]


async def institution_leaderboard(db: AsyncSession, limit: int = 20) -> list[dict]:
    rows = await db.execute(
        select(
            Institution.id,
            Institution.name,
            Institution.city,
            Institution.state,
            func.count(Case.id).label("n"),
        )
        .join(Case, Case.institution_id == Institution.id)
        .group_by(Institution.id, Institution.name, Institution.city, Institution.state)
        .order_by(func.count(Case.id).desc())
        .limit(limit)
    )
    return [
        {"institution_id": str(i), "name": n, "city": c, "state": s, "cases": k}
        for i, n, c, s, k in rows.all()
    ]
