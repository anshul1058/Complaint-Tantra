"""Institution risk index (system.md §4.5) — SQL aggregates only."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Case, CaseLink, Institution, InstitutionRisk, WebFinding

RISK_WEIGHTS = {"load": 0.35, "repeat": 0.25, "web": 0.25, "overlap": 0.15}


async def compute_risk(db: AsyncSession, institution_id) -> InstitutionRisk:
    now = datetime.now(timezone.utc)
    year_ago = now - timedelta(days=365)

    total = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.institution_id == institution_id, Case.received_at >= year_ago
        )
    )).scalar() or 0
    open_n = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.institution_id == institution_id, Case.status.notin_(("Disposed",))
        )
    )).scalar() or 0
    reopened = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.institution_id == institution_id, Case.status == "Reopened"
        )
    )).scalar() or 0

    neg = (await db.execute(
        select(func.count()).select_from(WebFinding).where(
            WebFinding.institution_id == institution_id,
            WebFinding.sentiment == "negative",
            WebFinding.retrieved_at >= now - timedelta(days=180),
        )
    )).scalar() or 0

    overlaps = (await db.execute(
        select(func.count()).select_from(CaseLink)
        .join(Case, Case.id == CaseLink.case_a)
        .where(Case.institution_id == institution_id, CaseLink.tier == "T1")
    )).scalar() or 0

    load = min(open_n / 20, 1.0)
    repeat = min(reopened / max(total, 1), 1.0)
    web = min(neg / 10, 1.0)
    ovl = min(overlaps / 10, 1.0)
    risk_index = round(
        100
        * (
            RISK_WEIGHTS["load"] * load
            + RISK_WEIGHTS["repeat"] * repeat
            + RISK_WEIGHTS["web"] * web
            + RISK_WEIGHTS["overlap"] * ovl
        ),
        1,
    )

    row = await db.get(InstitutionRisk, institution_id)
    if row is None:
        row = InstitutionRisk(institution_id=institution_id)
        db.add(row)
    row.complaint_load = load
    row.repeat_offender = repeat
    row.web_reputation = web
    row.overlap_density = ovl
    row.risk_index = risk_index
    row.computed_at = now
    await db.commit()
    return row
