import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_ADMIN, require_roles
from db import get_db
from models import Case, CaseLink, User
from routers.ingest import _post_ingest
from schemas import ReplayOut

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
