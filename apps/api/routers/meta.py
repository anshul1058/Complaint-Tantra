from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ALL_ROLES, get_current_user
from db import get_db
from models import SlaConfig, User
from schemas import MetaOptionsOut
from services.state_machine import STATUSES, TRANSITIONS, allowed_actions

router = APIRouter(tags=["meta"])


@router.get("/meta/options", response_model=MetaOptionsOut)
async def meta_options(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MetaOptionsOut:
    """Frontend fetches all business lists here — never hardcodes them."""
    from sqlalchemy import select

    rows = (await db.execute(select(SlaConfig))).scalars().all()
    transitions = {s: allowed_actions(s) for s in STATUSES}
    return MetaOptionsOut(
        statuses=STATUSES,
        transitions=transitions,
        categories=[{"category": r.category, "days": r.days_to_dispose,
                     "warn_before_days": r.warn_before_days} for r in rows],
        criticalities=["C1", "C2", "C3", "C4"],
        roles=ALL_ROLES,
        bureaus=["RB", "PGRC", "OTHER"],
        complainant_types=["student", "faculty", "parent", "other", "suo-motu"],
    )
