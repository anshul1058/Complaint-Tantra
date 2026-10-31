import json
import os
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.llm import complete_json
from agents.schemas import WebIntelOutput

FIXTURES_DIR = Path(__file__).parent.parent / "data" / "web_fixtures"
MAX_FETCHES = 12
MAX_RESULTS_PER_QUERY = 6


WEB_PROMPT = """You are the Web Intelligence Agent. Goal: build a factual, cited public track record for ONE institution.
Plan 3-6 searches mixing: "<name> <city> news", "<name> complaint / fee / fraud / ragging / affiliation / court", "<Permanent ID>", AICTE/UGC/state-regulator notices, "<name> placement/accreditation" (for positives).
For each result: verify it is the SAME institution (name + city/state). If unsure, refine the query (add state/city) or discard.
Classify topic, sentiment (negative/neutral/positive), emotion tone, severity 0..1. Never state a claim without a URL and publish date.
Prefer official/regulator sources and reputed outlets; treat social posts/forums as low-weight "signals".
Stop after at most 3 refinement rounds. Report what you could NOT verify.
Return JSON: {"findings":[...], "reputation_summary": "...", "reputation_risk": 0..100, "unverified":[...]}
"""

TOPIC_KEYWORDS = {
    "fees": ["fee", "refund", "capitation", "tuition"],
    "safety": ["ragging", "harassment", "assault", "safety", "hostel"],
    "accreditation": ["accredit", "naac", "nba", "affiliation", "approval", "eoa"],
    "faculty": ["faculty", "teacher", "staff", "professor"],
    "fraud": ["fraud", "fake", "forged", "scam", "cheat"],
    "placement": ["placement", "recruit", "package", "job"],
    "court": ["court", "high court", "supreme court", "verdict", "petition"],
}
NEGATIVE_KEYWORDS = ["fraud", "fake", "ragging", "harassment", "court", "scam", "protest", "violation", "penalty", "notice"]
POSITIVE_KEYWORDS = ["award", "rank", "accredit", "placement", "success", "launch"]


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 2}


def _same_institution(name: str, city: str, result: dict) -> float:
    """Cheap guard against wrong-institution news (§6.5)."""
    hay = f"{result.get('title') or ''} {result.get('content') or ''}".lower()
    name_tokens = _tokens(name)
    if not name_tokens:
        return 0.0
    name_hit = len(name_tokens & _tokens(hay)) / len(name_tokens)
    city_hit = 1.0 if city and city.lower() in hay else 0.0
    return min(1.0, 0.6 * name_hit + 0.25 * city_hit + 0.15)


def _classify(text: str) -> dict:
    t = (text or "").lower()
    topic = "other"
    for label, words in TOPIC_KEYWORDS.items():
        if any(w in t for w in words):
            topic = label
            break
    neg = sum(1 for w in NEGATIVE_KEYWORDS if w in t)
    pos = sum(1 for w in POSITIVE_KEYWORDS if w in t)
    sentiment = "negative" if neg > pos else "positive" if pos > neg else "neutral"
    severity = min(1.0, 0.35 + 0.15 * neg) if sentiment == "negative" else 0.05
    return {"topic": topic, "sentiment": sentiment, "severity": round(severity, 2)}


def _tavily_search(query: str, max_results: int = MAX_RESULTS_PER_QUERY) -> list[dict]:
    """Call Tavily over plain HTTP so no extra dependency is needed."""
    import urllib.request

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []
    body = json.dumps({
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
    }).encode()
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data.get("results") or []
    except Exception:
        return []


def _search_queries(inst: dict) -> list[str]:
    name = inst.get("name") or inst.get("name_normalized") or ""
    city = inst.get("city") or ""
    state = inst.get("state") or ""
    place = ", ".join(p for p in (city, state) if p)
    queries = [
        f"{name} {place} news",
        f"{name} complaint fee fraud ragging affiliation",
        f"{name} AICTE UGC notice accreditation",
    ]
    if inst.get("permanent_id"):
        queries.append(f'"{inst["permanent_id"]}"')
    return queries


def _live_intel(inst: dict) -> dict | None:
    queries = _search_queries(inst)
    seen: set[str] = set()
    findings: list[dict] = []
    for query in queries:
        for result in _tavily_search(query):
            url = result.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            if len(findings) >= MAX_FETCHES:
                break
            conf = _same_institution(inst.get("name", ""), inst.get("city", ""), result)
            if conf < 0.6:
                continue
            text = f"{result.get('title') or ''} {result.get('content') or ''}"
            cls = _classify(text)
            findings.append({
                "url": url,
                "title": result.get("title"),
                "source_name": urlparse(url).netloc,
                "published_at": result.get("published_date"),
                "summary": (result.get("content") or "")[:500] or None,
                "topic": cls["topic"],
                "sentiment": cls["sentiment"],
                "severity": cls["severity"],
                "match_confidence": round(conf, 2),
            })
        if len(findings) >= MAX_FETCHES:
            break
    if not findings:
        return None
    negative = [f for f in findings if f["sentiment"] == "negative"]
    risk = min(100.0, 25.0 * len(negative) + 10.0 * sum(f["severity"] for f in negative))
    return {
        "findings": findings,
        "reputation_summary": f"{len(findings)} public findings; {len(negative)} negative.",
        "reputation_risk": round(risk, 1),
        "unverified": [],
        "source": "tavily",
        "needs_review": False,
    }


def _fixture(inst: dict) -> dict | None:
    name = (inst.get("name_normalized") or inst.get("name") or "").replace(" ", "_").lower()
    fix = FIXTURES_DIR / f"{name}.json"
    if not fix.exists():
        return None
    try:
        data = json.loads(fix.read_text(encoding="utf-8"))
        data["source"] = "fixtures"
        data["needs_review"] = False
        return data
    except Exception:
        return None


def run_web_intel(institution: dict, cached: bool = True) -> dict:
    if cached:
        data = _fixture(institution)
        if data is not None:
            return data

    if os.getenv("TAVILY_API_KEY"):
        data = _live_intel(institution)
        if data is not None:
            return data

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
    from datetime import date

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
