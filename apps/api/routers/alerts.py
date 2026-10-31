from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from db import get_db
from models import Alert, Case, Institution, User
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

    case_ids = {a.case_id for a in rows if a.case_id}
    inst_ids = {a.institution_id for a in rows if a.institution_id}
    cases = {
        c.id: c for c in (await db.execute(select(Case).where(Case.id.in_(case_ids)))).scalars()
    } if case_ids else {}
    insts = {
        i.id: i for i in (await db.execute(
            select(Institution).where(Institution.id.in_(inst_ids))
        )).scalars()
    } if inst_ids else {}

    out = []
    for alert in rows:
        a = AlertOut.model_validate(alert)
        case = cases.get(alert.case_id)
        if case:
            a.case_no = case.case_no
            a.institution_id = a.institution_id or case.institution_id
        inst = insts.get(a.institution_id)
        if inst:
            a.institution_name = inst.name
        out.append(a)
    return out
