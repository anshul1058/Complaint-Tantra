"""Agent wrappers (backend-guide §7): contract with AI member, don't change silently.

Each tries the AI member's implementation first; on ImportError/any failure falls
back to deterministic rules so ingest never blocks (aiml-guide offline path).
"""

import hashlib
import json
import re
import time

from models import AgentRun

PROMPT_VERSION = "v1"

CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("safety", ["ragging", "harassment", "threat", "assault", "safety", "unsafe"]),
    ("fraud", ["fake", "fraud", "forged", "unapproved", "affiliation", "illegal"]),
    ("fees", ["fee", "refund", "capitation", "charge", "payment", "tuition"]),
    ("faculty", ["faculty", "professor", "teacher", "staff shortage"]),
    ("examination", ["exam", "result", "marksheet", "grade", "revaluation"]),
    ("placement", ["placement", "job", "recruitment", "package"]),
    ("infrastructure", ["infrastructure", "lab", "hostel", "building", "library"]),
    ("certificate", ["certificate", "degree", "document", "transcript"]),
]

EMOTION_RULES = [
    ("fear", ["afraid", "threat", "terrified", "scared", "danger"]),
    ("distress", ["distress", "suffering", "anguish", "helpless"]),
    ("hopelessness", ["hopeless", "no point", "give up", "suicide"]),
    ("anger", ["angry", "outrage", "unacceptable", "corrupt"]),
    ("frustration", ["frustrat", "again and again", "ignored", "no response"]),
]


def _rule_intake(case: dict) -> dict:
    text = (case.get("text_english") or case.get("text_original") or "").lower()
    category, sub = "other", None
    for cat, kws in CATEGORY_RULES:
        if any(k in text for k in kws):
            category, sub = cat, next((k for k in kws if k in text), None)
            break
    lang = case.get("language")
    if not lang:
        lang = "hi" if re.search(r"[ऀ-ॿ]", case.get("text_original") or "") else "en"
    summary_src = (case.get("text_english") or case.get("text_original") or "").strip()
    sentences = re.split(r"(?<=[.!?])\s+", summary_src)
    return {
        "language": lang,
        "text_english": case.get("text_english") or case.get("text_original"),
        "category": category,
        "subcategory": sub,
        "entities": {
            "institution_name": case.get("raw_institution") or case.get("institution_name"),
            "city": None,
            "state": None,
            "people_roles": [],
            "amounts": [],
            "dates": [],
            "documents_mentioned": [],
        },
        "summary": " ".join(sentences[:2])[:400] or None,
        "needs_review": True,
        "source": "rules",
    }


def _rule_triage(case: dict, intake: dict) -> dict:
    text = (case.get("text_english") or case.get("text_original") or "").lower()
    cat = (intake or {}).get("category") or case.get("category")
    crit_map = {"safety": "C1", "fraud": "C1", "fees": "C2", "faculty": "C3",
                "examination": "C3", "placement": "C3", "infrastructure": "C3",
                "certificate": "C4", "other": "C4"}
    criticality = crit_map.get(cat or "other", "C4")
    label, intensity = "neutral", 0.2
    for lab, kws in EMOTION_RULES:
        if any(k in text for k in kws):
            label = lab
            intensity = 0.8 if lab in ("fear", "distress", "hopelessness") else 0.6
            break
    safety_kws = ["suicide", "self harm", "kill myself", "threat to life", "ragging", "assault"]
    safety = any(k in text for k in safety_kws)
    urgency = [k for k in ("exam", "admission", "deadline", "court", "today", "immediate") if k in text]
    return {
        "criticality": criticality,
        "criticality_reason": f"rule: category={cat}",
        "emotion": {"label": label, "intensity": intensity},
        "safety_flag": safety,
        "flag_reason": "keyword match" if safety else None,
        "urgency_cues": urgency,
        "needs_review": True,
        "source": "rules",
    }


def _record(db, case_id, agent: str, output: dict, t0: float, input_obj: dict) -> None:
    db.add(AgentRun(
        case_id=case_id,
        agent=agent,
        model=output.get("model") or "rules",
        prompt_version=PROMPT_VERSION,
        input_hash=hashlib.sha256(json.dumps(input_obj, sort_keys=True, default=str).encode()).hexdigest()[:16],
        output=output,
        latency_ms=int((time.time() - t0) * 1000),
    ))


async def run_intake(db, case_id, case: dict) -> dict:
    t0 = time.time()
    try:
        from agents.ai_member import run_intake as ai_run  # AI member drops implementation here
        out = ai_run(case)
        out.setdefault("source", "llm")
        out.setdefault("needs_review", False)
    except Exception:
        out = _rule_intake(case)
    _record(db, case_id, "intake", out, t0, case)
    await db.commit()
    return out


async def run_triage(db, case_id, case: dict, intake: dict | None) -> dict:
    t0 = time.time()
    try:
        from agents.ai_member import run_triage as ai_run
        out = ai_run(case, intake)
        out.setdefault("source", "llm")
        out.setdefault("needs_review", False)
    except Exception:
        out = _rule_triage(case, intake)
    _record(db, case_id, "triage", out, t0, case)
    await db.commit()
    return out


async def detect_overlaps(db, case) -> list:
    """Thin wrapper over services.overlap (deterministic §5); AI judge optional later."""
    t0 = time.time()
    from services.overlap import detect_overlaps as _detect
    links = await _detect(db, case)
    out = [{"id": str(l.id), "tier": l.tier, "confidence": l.confidence} for l in links]
    _record(db, case.id, "overlap", {"links": out, "source": "rules"}, t0, {"case_id": str(case.id)})
    await db.commit()
    return out
