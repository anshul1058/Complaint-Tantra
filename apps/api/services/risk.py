"""Institution risk index (system.md §4.5) — SQL aggregates only."""

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Case, CaseLink, Institution, InstitutionRisk, WebFinding

RISK_WEIGHTS = {"load": 0.35, "repeat": 0.25, "web": 0.25, "overlap": 0.15}


def _p90(values: list[int]) -> int:
    if not values:
        return 0
    values = sorted(values)
    return values[min(len(values) - 1, int(0.9 * (len(values) - 1)))]


async def compute_risk(db: AsyncSession, institution_id) -> InstitutionRisk:
    now = datetime.now(timezone.utc)
    year_ago = now - timedelta(days=365)
    web_since = now - timedelta(days=180)
    inst = await db.get(Institution, institution_id)

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
            Case.institution_id == institution_id,
            Case.status == "Reopened",
            Case.received_at >= year_ago,
        )
    )).scalar() or 0

    cat_rows = (await db.execute(
        select(Case.category, func.count())
        .where(Case.institution_id == institution_id, Case.received_at >= year_ago)
        .group_by(Case.category)
    )).all()
    top_category = max((n for _, n in cat_rows), default=0)

    peer_load = open_n
    if inst and inst.state:
        peer_rows = (await db.execute(
            select(Case.institution_id, func.count())
            .join(Institution, Institution.id == Case.institution_id)
            .where(
                Institution.state == inst.state,
                Case.status.notin_(("Disposed",)),
                Case.received_at >= year_ago,
            )
            .group_by(Case.institution_id)
        )).all()
        peer_load = _p90([n for _, n in peer_rows]) or open_n

    web_rows = (await db.execute(
        select(WebFinding.severity, WebFinding.match_confidence, WebFinding.retrieved_at)
        .where(
            WebFinding.institution_id == institution_id,
            WebFinding.sentiment == "negative",
            WebFinding.match_confidence >= 0.6,
            WebFinding.retrieved_at >= web_since,
            WebFinding.dismissed_at.is_(None),
        )
    )).all()
    web_signal = 0.0
    for severity, confidence, retrieved_at in web_rows:
        age = max(0.0, (now - retrieved_at).total_seconds() / 86400) if retrieved_at else 0.0
        decay = math.exp(-age / 180)
        web_signal += (severity or 0.5) * (confidence or 0.6) * decay

    case_ids = select(Case.id).where(Case.institution_id == institution_id)
    overlaps = (await db.execute(
        select(func.count()).select_from(CaseLink).where(
            CaseLink.tier.in_(("T1", "T2")),
            or_(CaseLink.case_a.in_(case_ids), CaseLink.case_b.in_(case_ids)),
        )
    )).scalar() or 0

    load = min(open_n / max(peer_load, 1), 1.0)
    repeat = min(max(reopened / max(total, 1), top_category / max(total, 1)), 1.0)
    web = min(web_signal / 3.0, 1.0)
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
