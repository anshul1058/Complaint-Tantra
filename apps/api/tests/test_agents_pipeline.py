"""Agent pipeline tests — offline/rules path (no LLM, no DB required)."""

from datetime import datetime, timezone

from agents import _rule_intake, _rule_triage
from agents.schemas import IntakeOutput, OverlapJudge, TriageOutput, WebIntelOutput
from services.priority import compute_priority
from services.sla_engine import time_pressure


CASE = {
    "case_no": "TEST-001",
    "raw_institution": "MIT College of Engineering, Pune",
    "text_original": "My fee refund was denied. This is unfair and corrupt.",
    "text_english": None,
    "language": None,
    "category": None,
    "complainant_type": "student",
}


def test_rule_intake_shape():
    out = _rule_intake(CASE)
    parsed = IntakeOutput.model_validate(out)
    assert parsed.category is not None
    assert parsed.needs_review is True
    assert parsed.source == "rules"


def test_rule_triage_shape():
    intake = _rule_intake(CASE)
    out = _rule_triage(CASE, intake)
    parsed = TriageOutput.model_validate(out)
    assert parsed.criticality in ("C1", "C2", "C3", "C4")
    assert 0.0 <= parsed.emotion.intensity <= 1.0


def test_rule_triage_safety_flag():
    case = {**CASE, "text_original": "I want to kill myself if this continues. Ragging and threats."}
    intake = _rule_intake(case)
    out = _rule_triage(case, intake)
    parsed = TriageOutput.model_validate(out)
    assert parsed.safety_flag is True
    assert parsed.flag_reason is not None


def test_intake_to_priority_chain():
    intake = _rule_intake(CASE)
    triage = _rule_triage(CASE, intake)
    now = datetime.now(timezone.utc)
    tp = time_pressure(now, now, None, 14)
    score, reasons = compute_priority(
        criticality=triage["criticality"],
        emotion_label=triage["emotion"]["label"],
        emotion_intensity=triage["emotion"]["intensity"],
        time_pressure=tp,
        institution_risk_index=None,
        links=[],
        safety_flag=triage["safety_flag"],
    )
    assert 0 <= score <= 100
    assert reasons["components"].keys() == {"criticality", "emotion", "time", "risk", "overlap"}


def test_web_intel_fixture_path():
    from agents.web_intel import run_web_intel

    out = run_web_intel({"name": "Sample Institute", "name_normalized": "sample_institute"}, cached=True)
    parsed = WebIntelOutput.model_validate(out)
    assert parsed.source == "fixtures"
    assert len(parsed.findings) >= 1


def test_web_intel_offline_fallback_when_no_fixture():
    from agents.web_intel import run_web_intel

    out = run_web_intel({"name": "Unknown College", "name_normalized": "unknown_college"}, cached=False)
    # no LLM running -> should degrade to rules fallback, not raise
    assert out["needs_review"] is True
    assert out["source"] == "rules"


def test_overlap_judge_schema():
    v = OverlapJudge.model_validate(
        {"same_institution": True, "same_issue": True, "related": "same_issue", "confidence": 0.8, "reason": "both about fee refund"}
    )
    assert v.related == "same_issue"


def test_llm_config_defaults():
    from agents.llm import CONFIG

    assert CONFIG.provider in ("ollama", "openai-free", "anthropic", "gemini")
    assert CONFIG.model


def test_graph_builds_offline():
    from agents.graph import build_graph

    g = build_graph()  # must not raise even if langgraph is missing — only compiled lazily
    assert g is not None
