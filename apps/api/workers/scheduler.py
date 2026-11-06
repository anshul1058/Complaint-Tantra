"""APScheduler jobs (demo mode) — hourly SLA alerts, nightly MV + risk refresh."""

import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import func, select, text

from db import SessionLocal
from models import Alert, Case, Institution, InstitutionRisk, SlaConfig
from services.sla_engine import sla_status

scheduler = AsyncIOScheduler()


async def sla_check() -> None:
    """Hourly: due soon / overdue / stuck → alerts, deduped per case/day (§9)."""
    now = datetime.now(timezone.utc)
    today = now.date()
    async with SessionLocal() as db:
        configs = {r.category: r for r in (await db.execute(select(SlaConfig))).scalars()}
        # Do not hydrate full Case entities: complaint text, JSON reasons, and
        # the 1024-dimension embedding are not needed by the SLA check.
        cases = (await db.execute(
            select(
                Case.id,
                Case.case_no,
                Case.category,
                Case.received_at,
                Case.expected_disposal,
                Case.status,
                Case.last_action_at,
                Case.assigned_officer,
            ).where(Case.status.notin_(("Disposed",)))
        )).mappings().all()
        existing = {
            (a.case_id, a.kind)
            for a in (await db.execute(
                select(Alert).where(Alert.created_at >= datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc))
            )).scalars()
        }
        for case in cases:
            cfg = configs.get(case.category)
            warn = cfg.warn_before_days if cfg else 3
            state = sla_status(
                now, case.received_at, case.expected_disposal, case.status,
                warn_before_days=warn, last_action_at=case.last_action_at,
            )
            if state == "ok":
                continue
            if (case.id, state) in existing:
                continue
            msg = {
                "overdue": f"{case.case_no} is overdue",
                "due_soon": f"{case.case_no} due within {warn} days",
                "stuck": f"{case.case_no} has had no action recently",
            }[state]
            db.add(Alert(
                kind=state, case_id=case.id, severity={"overdue": "high", "due_soon": "medium", "stuck": "low"}[state],
                message=msg, target_role="officer", target_user=case.assigned_officer,
            ))
        await db.commit()


async def nightly_refresh() -> None:
    """Refresh materialized view + recompute risk indices (§9 beat jobs)."""
    async with SessionLocal() as db:
        await db.execute(text("REFRESH MATERIALIZED VIEW mv_dashboard_counts"))
        from services.risk import compute_risk

        inst_ids = (await db.execute(select(Institution.id))).scalars().all()
        for iid in inst_ids:
            await compute_risk(db, iid)
        await db.commit()


async def reputation_refresh() -> None:
    """Every 6h: refresh web intel for active institutions and alert on risk spikes."""
    if not any(os.getenv(k) for k in ("TAVILY_API_KEY", "BRAVE_API_KEY")) and os.getenv(
        "WEB_INTEL_LIVE", "0"
    ) != "1":
        return
    from agents.web_intel import refresh as web_refresh
    from services.risk import compute_risk

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(Case.institution_id, func.count())
            .where(Case.received_at >= cutoff, Case.institution_id.is_not(None))
            .group_by(Case.institution_id)
            .order_by(func.count().desc())
            .limit(50)
        )).all()
        for institution_id, _ in rows:
            before = await db.get(InstitutionRisk, institution_id)
            old = before.risk_index if before else 0.0
            await web_refresh(db, institution_id, force=True)
            after = await compute_risk(db, institution_id)
            if after.risk_index is not None and old is not None and after.risk_index - old >= 10:
                since = datetime.now(timezone.utc) - timedelta(hours=24)
                exists = (await db.execute(
                    select(Alert).where(
                        Alert.kind == "reputation",
                        Alert.institution_id == institution_id,
                        Alert.created_at >= since,
                    )
                )).first()
                if not exists:
                    db.add(Alert(
                        kind="reputation",
                        institution_id=institution_id,
                        severity="high",
                        message=f"Reputation risk rose {after.risk_index - old:.0f} points",
                        target_role="authority",
                    ))
        await db.commit()


async def daily_digest() -> None:
    """Daily: one scoped summary alert per role (deduped per day)."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)
    async with SessionLocal() as db:
        existing = (await db.execute(
            select(Alert).where(Alert.kind == "digest", Alert.created_at >= since)
        )).first()
        if existing:
            return
        total_open, overdue = (await db.execute(
            select(
                func.count(),
                func.count().filter(
                    Case.expected_disposal.is_not(None),
                    Case.expected_disposal < now,
                ),
            ).where(Case.status.notin_(("Disposed",)))
        )).one()
        new = (await db.execute(
            select(func.count()).select_from(Case).where(Case.received_at >= since)
        )).scalar() or 0
        db.add(Alert(
            kind="digest",
            severity="low",
            message=f"Daily digest: {total_open} open, {overdue} overdue, {new} new",
            target_role=None,
        ))
        await db.commit()


def start_scheduler() -> None:
    scheduler.add_job(sla_check, "interval", hours=1, id="sla_check", replace_existing=True)
    scheduler.add_job(reputation_refresh, "interval", hours=6, id="web_intel", replace_existing=True)
    scheduler.add_job(daily_digest, "cron", hour=8, id="digest", replace_existing=True)
    scheduler.add_job(nightly_refresh, "interval", hours=24, id="nightly", replace_existing=True)
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
