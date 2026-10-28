import json
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.llm import complete_json
from agents.schemas import WebIntelOutput


FIXTURES_DIR = Path(__file__).parent.parent / "data" / "web_fixtures"


WEB_PROMPT = """You are the Web Intelligence Agent. Goal: build a factual, cited public track record for ONE institution.
Plan 3-6 searches mixing: "<name> <city> news", "<name> complaint / fee / fraud / ragging / affiliation / court", "<Permanent ID>", AICTE/UGC/state-regulator notices, "<name> placement/accreditation" (for positives).
For each result: verify it is the SAME institution (name + city/state). If unsure, refine the query (add state/city) or discard.
Classify topic, sentiment (negative/neutral/positive), emotion tone, severity 0..1. Never state a claim without a URL and publish date.
Prefer official/regulator sources and reputed outlets; treat social posts/forums as low-weight "signals".
Stop after at most 3 refinement rounds. Report what you could NOT verify.
Return JSON: {"findings":[...], "reputation_summary": "...", "reputation_risk": 0..100, "unverified":[...]}
"""


def run_web_intel(institution: dict, cached: bool = True) -> dict:
    if cached:
        # Try fixtures for demo/offline
        name = (institution.get("name_normalized") or institution.get("name") or "").replace(" ", "_").lower()
        fix = FIXTURES_DIR / f"{name}.json"
        if fix.exists():
            try:
                data = json.loads(fix.read_text(encoding="utf-8"))
                data["source"] = "fixtures"
                data["needs_review"] = False
                return data
            except Exception:
                pass

    try:
        full = WEB_PROMPT + "\n\nINSTITUTION:\n" + str(institution) + "\n"
        out, meta = complete_json(full, WebIntelOutput)
        out["model"] = meta.get("model")
        out["prompt_version"] = meta.get("prompt_version")
        out["source"] = "llm"
        out["needs_review"] = False
        return out
    except Exception:
        return {
            "findings": [],
            "reputation_summary": None,
            "reputation_risk": 0.0,
            "unverified": ["web_intel_unavailable"],
            "needs_review": True,
            "source": "rules",
        }


async def refresh(db: AsyncSession, institution_id: uuid.UUID) -> dict:
    """Called by POST /institutions/{id}/intel/refresh (routers/institutions.py).

    Runs web intel for the institution and persists findings into web_findings.
    Returns dict shaped like IntelRefreshOut.
    """
    from datetime import date, datetime, timezone

    from models import Institution, WebFinding

    inst = await db.get(Institution, institution_id)
    if inst is None:
        return {"findings_created": 0, "reputation_risk": None, "needs_review": True, "detail": "institution not found"}

    inst_dict = {
        "id": str(inst.id),
        "name": inst.name,
        "name_normalized": inst.name_normalized,
        "city": inst.city,
        "state": inst.state,
        "permanent_id": inst.permanent_id,
    }
    out = run_web_intel(inst_dict, cached=True)

    created = 0
    for f in out.get("findings", []):
        if (f.get("match_confidence") or 0) < 0.6:
            continue
        url = f.get("url")
        if not url:
            continue
        existing = await db.execute(
            select(WebFinding).where(WebFinding.institution_id == institution_id, WebFinding.url == url)
        )
        if existing.first():
            continue
        pub = None
        if f.get("published_at"):
            try:
                pub = date.fromisoformat(str(f["published_at"])[:10])
            except Exception:
                pub = None
        db.add(WebFinding(
            institution_id=institution_id,
            url=url,
            title=f.get("title"),
            source_name=f.get("source_name"),
            published_at=pub,
            summary=f.get("summary"),
            topic=f.get("topic"),
            sentiment=f.get("sentiment"),
            emotion_label=f.get("emotion_label"),
            severity=f.get("severity"),
            match_confidence=f.get("match_confidence"),
        ))
        created += 1
    await db.commit()

    return {
        "findings_created": created,
        "reputation_risk": out.get("reputation_risk"),
        "needs_review": bool(out.get("needs_review")),
        "detail": f"source={out.get('source')}",
    }
