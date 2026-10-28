"""Case create/action helpers — every transition writes a case_actions row (§3)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Case, CaseAction, Institution, SlaConfig, User
from services import sla_engine
from services.state_machine import TransitionError, allowed_actions, next_status

DEFAULT_SLA_DAYS = 30


async def sla_days_for(db: AsyncSession, category: str | None) -> tuple[int, int]:
    if category:
        row = await db.get(SlaConfig, category)
        if row:
            return row.days_to_dispose, row.warn_before_days
    return DEFAULT_SLA_DAYS, sla_engine.DEFAULT_WARN_DAYS


async def create_case(db: AsyncSession, data: dict, actor: User | None = None) -> Case:
    now = datetime.now(timezone.utc)
    received = data.get("received_at") or now
    if received.tzinfo is None:
        received = received.replace(tzinfo=timezone.utc)
    days, _ = await sla_days_for(db, data.get("category"))
    case = Case(
        case_no=data.get("case_no") or f"CT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
        source_bureau=data.get("source_bureau") or "RB",
        assigned_bureau=data.get("assigned_bureau") or data.get("source_bureau") or "RB",
        raw_institution=data.get("raw_institution") or data.get("institution_name"),
        complainant_type=data.get("complainant_type"),
        category=data.get("category"),
        subcategory=data.get("subcategory"),
        text_original=data.get("text_original"),
        text_english=data.get("text_english") or data.get("text_original"),
        language=data.get("language"),
        status="Received",
        received_at=received,
        expected_disposal=sla_engine.expected_disposal(received, days),
        last_action_at=now,
        next_action="assign",
    )
    db.add(case)
    await db.flush()
    db.add(
        CaseAction(
            case_id=case.id,
            actor_id=actor.id if actor else None,
            actor_type="user" if actor else "system",
            action="created",
            from_state=None,
            to_state="Received",
        )
    )
    await db.commit()
    await db.refresh(case)
    return case


async def apply_action(
    db: AsyncSession,
    case: Case,
    action: str,
    *,
    actor: User,
    remarks: str | None = None,
    payload: dict | None = None,
) -> Case:
    to_state = next_status(case.status, action)  # raises TransitionError if invalid
    now = datetime.now(timezone.utc)
    if action == "reopened" and not remarks:
        raise TransitionError("reopen requires a reason")
    if action == "assigned" and payload and payload.get("officer_id"):
        case.assigned_officer = uuid.UUID(str(payload["officer_id"]))
    if action == "transferred" and payload and payload.get("to_bureau"):
        case.assigned_bureau = str(payload["to_bureau"])

    from_state = case.status
    if to_state:
        case.status = to_state
    case.last_action_at = now
    if to_state == "UnderProcess":
        case.next_action = "process"
    elif to_state == "Disposed":
        case.next_action = None
    elif to_state == "Escalated":
        case.next_action = "authority_review"
    elif to_state == "Transferred":
        case.next_action = "accept_transfer"
    elif to_state == "Reopened":
        case.next_action = "assign"
    elif to_state is None:
        case.next_action = case.next_action

    db.add(
        CaseAction(
            case_id=case.id,
            actor_id=actor.id,
            actor_type="user",
            action=action,
            from_state=from_state,
            to_state=to_state,
            remarks=remarks,
            payload=payload,
        )
    )
    await db.commit()
    await db.refresh(case)
    return case


async def record_agent_action(
    db: AsyncSession,
    case: Case,
    action: str,
    *,
    remarks: str | None = None,
    payload: dict | None = None,
) -> None:
    """System/agent-authored action log entry (no status change unless specified)."""
    to_state = next_status(case.status, action) if action in ("assigned",) else None
    if to_state:
        case.status = to_state
        case.last_action_at = datetime.now(timezone.utc)
    db.add(
        CaseAction(
            case_id=case.id,
            actor_id=None,
            actor_type="system",
            action=action,
            from_state=None,
            to_state=to_state,
            remarks=remarks,
            payload=payload,
        )
    )


def case_flags(case: Case, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    return {
        "overdue": sla_engine.is_overdue(now, case.expected_disposal, case.status),
        "allowed_actions": allowed_actions(case.status),
    }


async def resolve_institution(
    db: AsyncSession,
    *,
    name: str,
    address: str | None = None,
    city: str | None = None,
    state: str | None = None,
    permanent_id: str | None = None,
) -> tuple[Institution | None, float]:
    """§5 thresholds: ≥0.90 auto-link, 0.70–0.90 confirm, <0.70 new."""
    from services.entity_resolution import match_score, normalize_name, verdict

    if permanent_id:
        inst = await db.execute(select(Institution).where(Institution.permanent_id == permanent_id))
        row = inst.scalar_one_or_none()
        if row:
            return row, 1.0

    norm = normalize_name(name)
    cands = await db.execute(
        select(Institution).where(Institution.name_normalized.ilike(f"%{norm}%")).limit(20)
    )
    best, best_score = None, 0.0
    for cand in cands.scalars():
        s = match_score(
            {"name_normalized": cand.name_normalized, "address": cand.address,
             "city": cand.city, "state": cand.state},
            name=name, address=address, city=city, state=state,
        )
        if s > best_score:
            best, best_score = cand, s

    if best is not None and verdict(best_score) in ("auto", "confirm"):
        return best, best_score
    if best_score >= 0.70:
        return best, best_score
    return None, best_score
