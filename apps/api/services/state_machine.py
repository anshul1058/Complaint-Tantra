"""Case state machine (system.md §3). Overdue is computed, never stored."""

STATUSES = [
    "Received",
    "UnderProcess",
    "Transferred",
    "Escalated",
    "Disposed",
    "Reopened",
]

# action -> {from_status: to_status}
TRANSITIONS: dict[str, dict[str, str]] = {
    "assigned": {"Received": "UnderProcess", "Reopened": "UnderProcess"},
    "transferred": {"UnderProcess": "Transferred"},
    "accepted": {"Transferred": "UnderProcess"},
    "escalated": {"UnderProcess": "Escalated"},
    "deescalated": {"Escalated": "UnderProcess"},
    "disposed": {"UnderProcess": "Disposed", "Escalated": "Disposed"},
    "reopened": {"Disposed": "Reopened"},
}

# Actions that never change status
NO_STATE_CHANGE = {"remark", "doc_added"}

REOPEN_REASON_REQUIRED = True


class TransitionError(ValueError):
    pass


def next_status(current: str, action: str) -> str | None:
    """Return the new status, None if action doesn't change status, or raise TransitionError."""
    if action in NO_STATE_CHANGE:
        return None
    if action not in TRANSITIONS:
        raise TransitionError(f"Unknown action: {action}")
    target = TRANSITIONS[action].get(current)
    if target is None:
        raise TransitionError(f"Action '{action}' not valid from status '{current}'")
    return target


def allowed_actions(current: str) -> list[str]:
    """Statuses the UI uses to drive buttons (frontend must not compute transitions)."""
    actions = [a for a, m in TRANSITIONS.items() if current in m]
    return sorted(set(actions) | NO_STATE_CHANGE)
