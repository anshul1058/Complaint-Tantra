"""Per-user saved case filters (FR-21)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from db import get_db
from models import SavedFilter, User
from schemas import SavedFilterIn, SavedFilterOut

router = APIRouter(prefix="/saved-filters", tags=["saved-filters"])


@router.get("", response_model=list[SavedFilterOut])
async def list_filters(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[SavedFilterOut]:
    rows = (await db.execute(
        select(SavedFilter).where(SavedFilter.user_id == user.id).order_by(SavedFilter.created_at)
    )).scalars().all()
    return [SavedFilterOut.model_validate(r) for r in rows]


@router.post("", response_model=SavedFilterOut, status_code=status.HTTP_201_CREATED)
async def create_filter(
    body: SavedFilterIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> SavedFilterOut:
    row = SavedFilter(user_id=user.id, name=body.name, filters=body.filters)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return SavedFilterOut.model_validate(row)


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(
    filter_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    row = await db.get(SavedFilter, filter_id)
    if row is None or row.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Filter not found")
    await db.delete(row)
    await db.commit()
