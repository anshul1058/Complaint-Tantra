import asyncio
import json
import os
import re
import uuid
from datetime import datetime
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

    from services.sentiment import analyze_sentiment

    model_sent = analyze_sentiment(text)
    if model_sent:
        sentiment = model_sent["label"]
        if sentiment == "negative":
            severity = max(severity, model_sent["score"])
        elif sentiment == "positive":
            severity = 0.05
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


def _brave_search(query: str, max_results: int = MAX_RESULTS_PER_QUERY) -> list[dict]:
    import urllib.parse
    import urllib.request

    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return []
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
        {"q": query, "count": max_results}
    )
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "X-Subscription-Token": api_key}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return [
            {
                "url": r.get("url"),
                "title": r.get("title"),
                "content": r.get("description") or r.get("title"),
                "published_date": r.get("age"),
            }
            for r in (data.get("web", {}).get("results") or [])
        ]
    except Exception:
        return []


def _gdelt_search(query: str, max_results: int = MAX_RESULTS_PER_QUERY) -> list[dict]:
    """Free, keyless news index used when no paid search key is configured."""
    import urllib.parse
    import urllib.request

    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(
        {"query": query, "mode": "artlist", "format": "json",
         "maxrecords": max_results, "timespan": "18m"}
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []
    return [
        {
            "url": a.get("url"),
            "title": a.get("title"),
            "content": a.get("title"),
            "published_date": a.get("seendate"),
        }
        for a in (data.get("articles") or [])
    ]


def _fetch_article(url: str) -> str | None:
    """Full article text via trafilatura when available (system.md §6.5)."""
    try:
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        return trafilatura.extract(downloaded) if downloaded else None
    except Exception:
        return None


def _google_news(query: str) -> list[dict]:
    """Free fallback search: Google News RSS, no API key (aiml-guide §7)."""
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET

    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=en-IN&gl=IN&ceid=IN:en"
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            root = ET.fromstring(resp.read())
    except Exception:
        return []
    out = []
    for item in root.iter("item"):
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        if link and title:
            out.append({
                "url": link,
                "title": title,
                "content": item.findtext("description") or title,
                "published_date": item.findtext("pubDate"),
            })
    return out


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


def _search(query: str) -> list[dict]:
    return (
        _tavily_search(query)
        or _brave_search(query)
        or _gdelt_search(query)
        or _google_news(query)
    )


def _live_intel(inst: dict) -> dict | None:
    if not any(os.getenv(k) for k in ("TAVILY_API_KEY", "BRAVE_API_KEY")) and os.getenv(
        "WEB_INTEL_LIVE", "0"
    ) != "1":
        return None
    name = inst.get("name") or ""
    state = inst.get("state") or ""
    queries = _search_queries(inst)
    seen: set[str] = set()
    findings: list[dict] = []
    for _round in range(3):
        for query in queries:
            for result in _search(query):
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
                if len(text) < 400:
                    text = f"{text} {_fetch_article(url) or ''}".strip()
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
        if findings:
            break
        queries = [
            f"{name} {state} news",
            f"{name} court fee ragging",
            f"{name} AICTE UGC action",
        ]
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

    if any(os.getenv(k) for k in ("TAVILY_API_KEY", "BRAVE_API_KEY")) or os.getenv(
        "WEB_INTEL_LIVE", "0"
    ) == "1":
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


async def refresh(db: AsyncSession, institution_id: uuid.UUID, force: bool = False) -> dict:
    """Called by POST /institutions/{id}/intel/refresh (routers/institutions.py).

    Runs web intel for the institution and persists findings into web_findings.
    Returns dict shaped like IntelRefreshOut.
    """
    from datetime import date

    from models import Institution, WebFinding

    inst = await db.get(Institution, institution_id)
    if inst is None:
        return {"findings_created": 0, "reputation_risk": None, "needs_review": True, "detail": "institution not found"}

    if not force:
        latest = (await db.execute(
            select(WebFinding.retrieved_at)
            .where(WebFinding.institution_id == institution_id)
            .order_by(WebFinding.retrieved_at.desc())
            .limit(1)
        )).scalar()
        if latest:
            age = (datetime.now(latest.tzinfo) - latest).total_seconds()
            if age < 86400:
                return {"findings_created": 0, "reputation_risk": None,
                        "needs_review": False, "detail": "cached (<24h)"}

    inst_dict = {
        "id": str(inst.id),
        "name": inst.name,
        "name_normalized": inst.name_normalized,
        "city": inst.city,
        "state": inst.state,
        "permanent_id": inst.permanent_id,
    }
    out = await asyncio.to_thread(run_web_intel, inst_dict, True)

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
