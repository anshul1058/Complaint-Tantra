import asyncio
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_ADMIN, ROLE_AUTHORITY, ROLE_SENIOR, require_roles
from db import get_db
from models import Case, CaseLink, Institution, InstitutionRisk, User, WebFinding
from routers.ingest import _post_ingest
from schemas import DossierOut, ReplayOut

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/replay/{case_id}", response_model=ReplayOut)
async def replay(
    case_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_ADMIN))],
) -> ReplayOut:
    """Re-run agents for reproducibility (§12). Stored in agent_runs."""
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    await _post_ingest(db, case)
    await db.refresh(case)
    links = (await db.execute(
        select(CaseLink).where(CaseLink.case_a == case.id)
    )).scalars().all()
    return ReplayOut(
        case_id=case.id,
        intake={"category": case.category, "summary": case.ai_summary},
        triage={"criticality": case.criticality,
                "emotion": {"label": case.emotion_label, "intensity": case.emotion_intensity}},
        overlaps=[{"id": str(l.id), "tier": l.tier, "confidence": l.confidence} for l in links],
        priority_score=case.priority_score,
        needs_review=case.priority_reasons is None,
    )


@router.get("/dossiers/{institution_id}", response_model=DossierOut)
async def dossier(
    institution_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_SENIOR, ROLE_AUTHORITY, ROLE_ADMIN))],
) -> DossierOut:
    inst = await db.get(Institution, institution_id)
    if inst is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institution not found")
    total = (await db.execute(
        select(func.count()).select_from(Case).where(Case.institution_id == institution_id)
    )).scalar() or 0
    open_n = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.institution_id == institution_id, Case.status.notin_(("Disposed",))
        )
    )).scalar() or 0
    findings = (await db.execute(
        select(WebFinding)
        .where(WebFinding.institution_id == institution_id, WebFinding.dismissed_at.is_(None))
        .order_by(WebFinding.retrieved_at.desc())
        .limit(20)
    )).scalars().all()
    risk = await db.get(InstitutionRisk, institution_id)
    facts = {
        "institution": inst.name,
        "district": inst.city,
        "state": inst.state,
        "cases_total": total,
        "cases_open": open_n,
        "risk_index": risk.risk_index if risk else None,
        "negative_findings": sum(1 for f in findings if f.sentiment == "negative"),
    }
    narrative = None
    generated = False
    try:
        from agents.llm import complete_json

        out, _meta = await asyncio.to_thread(
            complete_json,
            "Write a factual institution dossier narrative using only these SQL facts: "
            f"{facts}",
            None,
        )
        narrative = out.get("narrative") or out.get("summary") or out.get("text")
        generated = bool(narrative)
    except Exception:
        pass
    if not narrative:
        narrative = (
            f"{inst.name}: {total} complaints on record, {open_n} open, "
            f"risk index {facts['risk_index']}."
        )
    return DossierOut(
        institution_id=inst.id,
        institution_name=inst.name,
        risk={k: getattr(risk, k) for k in (
            "complaint_load", "repeat_offender", "web_reputation",
            "overlap_density", "risk_index",
        )} if risk else None,
        counts={"total": total, "open": open_n},
        findings=[{"url": f.url, "title": f.title, "sentiment": f.sentiment,
                   "severity": f.severity} for f in findings],
        narrative=narrative,
        source="llm" if generated else "rules",
    )
