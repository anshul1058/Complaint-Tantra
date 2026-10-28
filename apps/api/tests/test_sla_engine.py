"""SLA math tests (backend-guide DoD: pytest for SLA math)."""

from datetime import datetime, timedelta, timezone

from services.priority import compute_priority, emotion_weighted, overlap_bonus
from services.sla_engine import (
    age_factor,
    days_left,
    expected_disposal,
    is_overdue,
    sla_status,
    time_pressure,
)

NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)


def test_expected_disposal():
    got = expected_disposal(datetime(2026, 6, 1, tzinfo=timezone.utc), 14)
    assert got == datetime(2026, 6, 15, tzinfo=timezone.utc)


def test_overdue_computed_not_stored():
    past = NOW - timedelta(days=1)
    assert is_overdue(NOW, past, "UnderProcess") is True
    assert is_overdue(NOW, past, "Disposed") is False  # disposed never overdue
    assert is_overdue(NOW, None, "UnderProcess") is False
    assert is_overdue(NOW, NOW + timedelta(days=1), "Received") is False


def test_time_pressure_grows_as_deadline_nears():
    received = NOW - timedelta(days=9)
    far = time_pressure(NOW, received, received + timedelta(days=30), 30)
    near = time_pressure(NOW, received, NOW + timedelta(days=1), 30)
    assert 0 <= far < near <= 1.0


def test_time_pressure_overdue_caps_at_1_5():
    received = NOW - timedelta(days=60)
    expected = NOW - timedelta(days=30)
    tp = time_pressure(NOW, received, expected, 30)
    assert tp == 1.5  # 1 + min(30/30, 0.5) = 1.5


def test_age_factor_caps_at_1():
    assert age_factor(NOW, NOW - timedelta(days=100)) == 1.0
    assert age_factor(NOW, NOW - timedelta(days=45)) == 0.5


def test_days_left():
    assert days_left(NOW, NOW + timedelta(days=5)) == 5
    assert days_left(NOW, None) is None


def test_sla_status_buckets():
    received = NOW - timedelta(days=10)
    assert sla_status(NOW, received, NOW - timedelta(days=1), "UnderProcess") == "overdue"
    assert sla_status(NOW, received, NOW + timedelta(days=2), "UnderProcess") == "due_soon"
    assert sla_status(NOW, received, NOW + timedelta(days=20), "UnderProcess",
                      last_action_at=NOW) == "ok"
    # stuck: no action in 7+ days, not yet due
    stale = NOW - timedelta(days=8)
    assert sla_status(NOW, received, NOW + timedelta(days=25), "UnderProcess",
                      last_action_at=stale) == "stuck"
    assert sla_status(NOW, received, NOW - timedelta(days=1), "Disposed") == "ok"


def test_priority_formula_shape():
    score, reasons = compute_priority(
        criticality="C1", emotion_label="fear", emotion_intensity=0.8,
        time_pressure=0.9, institution_risk_index=50, links=[{"tier": "T1", "decision": "pending"}],
    )
    assert 0 <= score <= 100
    assert reasons["components"].keys() == {"criticality", "emotion", "time", "risk", "overlap"}
    assert reasons["reasons"]


def test_priority_safety_flag_bypasses():
    score, reasons = compute_priority(
        criticality="C4", emotion_label="neutral", emotion_intensity=0.1,
        time_pressure=0.0, institution_risk_index=0, safety_flag=True,
    )
    assert score == 100.0
    assert "SAFETY FLAG" in reasons["reasons"][0]


def test_emotion_and_overlap_helpers():
    assert emotion_weighted("fear", 1.0) == 1.0
    assert emotion_weighted("hopeful", 1.0) == 0.0
    assert emotion_weighted(None, None) == 0.0
    assert overlap_bonus([{"tier": "T1", "decision": "pending"}]) == 1.0
    assert overlap_bonus([{"tier": "T3", "decision": "pending"}]) == 0.5
    assert overlap_bonus([{"tier": "T1", "decision": "rejected"}]) == 0.0
    assert overlap_bonus([]) == 0.0
