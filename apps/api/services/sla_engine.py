"""Deterministic SLA math (system.md §4.3, §9). Pure functions — no DB."""

from datetime import datetime, timedelta

from services.state_machine import STATUSES  # noqa: F401  (re-export for convenience)

DEFAULT_DAYS = 30
DEFAULT_WARN_DAYS = 3


def expected_disposal(received_at: datetime, days: int) -> datetime:
    return received_at + timedelta(days=days)


def is_overdue(now: datetime, expected_disposal_at: datetime | None, status: str) -> bool:
    """Overdue is a computed flag, never a stored status (§3)."""
    if status == "Disposed" or expected_disposal_at is None:
        return False
    return now > expected_disposal_at


def days_left(now: datetime, expected_disposal_at: datetime | None) -> int | None:
    if expected_disposal_at is None:
        return None
    return (expected_disposal_at - now).days


def time_pressure(
    now: datetime,
    received_at: datetime,
    expected_disposal_at: datetime | None,
    sla_days: int,
) -> float:
    """system.md §4.3."""
    if sla_days <= 0:
        sla_days = DEFAULT_DAYS
    if expected_disposal_at is None:
        expected_disposal_at = expected_disposal(received_at, sla_days)
    age_days = max((now - received_at).total_seconds() / 86400, 0.0)
    if now > expected_disposal_at:
        days_overdue = (now - expected_disposal_at).total_seconds() / 86400
        return 1.0 + min(days_overdue / 30, 0.5)  # up to 1.5, capped by caller
    left = (expected_disposal_at - now).total_seconds() / 86400
    return max(0.0, min(1.0, 1.0 - (left / sla_days))) if sla_days else 0.0


def age_factor(now: datetime, received_at: datetime) -> float:
    age_days = max((now - received_at).total_seconds() / 86400, 0.0)
    return min(age_days / 90, 1.0)


def sla_status(
    now: datetime,
    received_at: datetime,
    expected_disposal_at: datetime | None,
    status: str,
    warn_before_days: int = DEFAULT_WARN_DAYS,
    last_action_at: datetime | None = None,
    stuck_days: int = 7,
) -> str:
    """One of: overdue | due_soon | stuck | ok (alert categories §9)."""
    if status == "Disposed":
        return "ok"
    if is_overdue(now, expected_disposal_at, status):
        return "overdue"
    left = days_left(now, expected_disposal_at)
    if left is not None and left <= warn_before_days:
        return "due_soon"
    ref = last_action_at or received_at
    if status not in ("Disposed",) and (now - ref).days >= stuck_days:
        return "stuck"
    return "ok"
