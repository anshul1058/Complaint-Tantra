import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_AUTHORITY, ROLE_OFFICER, ROLE_REGIONAL, ROLE_SENIOR, get_current_user, require_roles
from db import get_db
from models import Case, Institution, InstitutionRisk, User, WebFinding
from schemas import InstitutionProfileOut, IntelRefreshOut, RiskOut, WebFindingOut

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/{institution_id}", response_model=InstitutionProfileOut)
async def institution_profile(
    institution_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> InstitutionProfileOut:
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
    risk = await db.get(InstitutionRisk, institution_id)
    risk_dict = None
    if risk:
        risk_dict = {
            "complaint_load": risk.complaint_load,
            "repeat_offender": risk.repeat_offender,
            "web_reputation": risk.web_reputation,
            "overlap_density": risk.overlap_density,
            "risk_index": risk.risk_index,
            "computed_at": risk.computed_at.isoformat() if risk.computed_at else None,
        }
    out = InstitutionProfileOut.model_validate(inst)
    out.risk = risk_dict
    out.case_count = total
    out.open_count = open_n
    return out


@router.get("/{institution_id}/risk", response_model=RiskOut)
async def institution_risk(
    institution_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> RiskOut:
    if await db.get(Institution, institution_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institution not found")
    risk = await db.get(InstitutionRisk, institution_id)
    if risk is None:
        from services.risk import compute_risk

        risk = await compute_risk(db, institution_id)
    return RiskOut.model_validate(risk)


@router.get("/{institution_id}/intel", response_model=list[WebFindingOut])
async def institution_intel(
    institution_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[WebFindingOut]:
    if await db.get(Institution, institution_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institution not found")
    # match_confidence < 0.6 hidden by default (§6.5 guardrails)
    rows = (await db.execute(
        select(WebFinding)
        .where(
            WebFinding.institution_id == institution_id,
            WebFinding.dismissed_at.is_(None),
        )
        .order_by(WebFinding.retrieved_at.desc())
    )).scalars().all()
    return [WebFindingOut.model_validate(f) for f in rows if (f.match_confidence or 0) >= 0.6]


@router.post("/{institution_id}/intel/{finding_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_finding(
    institution_id: uuid.UUID,
    finding_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_roles(ROLE_OFFICER, ROLE_REGIONAL, ROLE_SENIOR, ROLE_AUTHORITY))],
) -> None:
    finding = await db.get(WebFinding, finding_id)
    if finding is None or finding.institution_id != institution_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found")
    from datetime import datetime, timezone

    finding.dismissed_at = datetime.now(timezone.utc)
    finding.dismissed_by = user.id
    await db.commit()


@router.post("/{institution_id}/intel/refresh", response_model=IntelRefreshOut)
async def refresh_intel(
    institution_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(ROLE_OFFICER, ROLE_REGIONAL, ROLE_SENIOR, ROLE_AUTHORITY))],
    force: bool = Query(False),
) -> IntelRefreshOut:
    if await db.get(Institution, institution_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Institution not found")
    try:
        from agents.web_intel import refresh as web_refresh

        return await web_refresh(db, institution_id, force=force)
    except ImportError:
        return IntelRefreshOut(
            detail="Web intelligence agent not installed yet (AI member scope)",
            needs_review=True,
        )
