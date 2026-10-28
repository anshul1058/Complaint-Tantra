"""State machine tests — the only non-trivial transition logic (backend-guide DoD)."""

import pytest

from services.state_machine import TransitionError, allowed_actions, next_status


def test_happy_path_received_to_disposed():
    s = next_status("Received", "assigned")
    assert s == "UnderProcess"
    s = next_status(s, "disposed")
    assert s == "Disposed"


def test_transfer_roundtrip():
    assert next_status("UnderProcess", "transferred") == "Transferred"
    assert next_status("Transferred", "accepted") == "UnderProcess"


def test_escalate_deescalate():
    assert next_status("UnderProcess", "escalated") == "Escalated"
    assert next_status("Escalated", "deescalated") == "UnderProcess"
    assert next_status("Escalated", "disposed") == "Disposed"


def test_reopen_requires_valid_from():
    assert next_status("Disposed", "reopened") == "Reopened"
    assert next_status("Reopened", "assigned") == "UnderProcess"
    with pytest.raises(TransitionError):
        next_status("Received", "reopened")


def test_invalid_transitions_raise():
    with pytest.raises(TransitionError):
        next_status("Received", "disposed")
    with pytest.raises(TransitionError):
        next_status("Disposed", "escalated")
    with pytest.raises(TransitionError):
        next_status("Received", "nonsense")


def test_remark_never_changes_status():
    assert next_status("UnderProcess", "remark") is None
    assert next_status("Disposed", "doc_added") is None


def test_allowed_actions_for_ui():
    a = allowed_actions("UnderProcess")
    assert "escalated" in a
    assert "disposed" in a
    assert "transferred" in a
    assert "reopened" not in a
    assert "remark" in a
