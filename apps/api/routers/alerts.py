from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from db import get_db
from models import Alert, Case, User
from schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    kind: str | None = None,
    limit: int = Query(50, le=200),
) -> list[AlertOut]:
    """Scoped: alerts targeted at this user/role, or for cases in their bureau."""
    stmt = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
    conds = [
        Alert.target_user == user.id,
        Alert.target_role == user.role,
        Alert.target_role.is_(None),
        Alert.case_id.in_(select(Case.id).where(Case.assigned_bureau == user.bureau)),
    ]
    stmt = stmt.where(or_(*conds))
    if kind:
        stmt = stmt.where(Alert.kind == kind)
    rows = (await db.execute(stmt)).scalars().all()
    return [AlertOut.model_validate(a) for a in rows]
