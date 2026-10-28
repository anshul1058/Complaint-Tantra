"""APScheduler jobs (demo mode) — hourly SLA alerts, nightly MV + risk refresh."""

from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, text

from db import SessionLocal
from models import Alert, Case, Institution, SlaConfig
from services.sla_engine import sla_status

scheduler = AsyncIOScheduler()


async def sla_check() -> None:
    """Hourly: due soon / overdue / stuck → alerts, deduped per case/day (§9)."""
    now = datetime.now(timezone.utc)
    today = now.date()
    async with SessionLocal() as db:
        configs = {r.category: r for r in (await db.execute(select(SlaConfig))).scalars()}
        cases = (await db.execute(
            select(Case).where(Case.status.notin_(("Disposed",)))
        )).scalars().all()
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


def start_scheduler() -> None:
    scheduler.add_job(sla_check, "interval", hours=1, id="sla_check", replace_existing=True)
    scheduler.add_job(nightly_refresh, "interval", hours=24, id="nightly", replace_existing=True)
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
