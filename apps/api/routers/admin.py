"""Admin console: users, SLA config, scoring weights, audit trail."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import ROLE_ADMIN, hash_password, require_roles
from db import get_db
from models import AuditLog, SlaConfig, User
from schemas import (
    SlaConfigIn,
    SlaConfigOut,
    UserAdminCreate,
    UserAdminOut,
    UserAdminUpdate,
    WeightsIn,
    WeightsOut,
)
from services import scoring_config

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles(ROLE_ADMIN))])


@router.get("/users", response_model=list[UserAdminOut])
async def list_users(db: Annotated[AsyncSession, Depends(get_db)]) -> list[UserAdminOut]:
    rows = (await db.execute(select(User).order_by(User.name))).scalars().all()
    return [UserAdminOut.model_validate(u) for u in rows]


@router.post("/users", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserAdminCreate, db: Annotated[AsyncSession, Depends(get_db)]
) -> UserAdminOut:
    exists = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")
    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        bureau=body.bureau,
        region=body.region,
        active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserAdminOut.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserAdminOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserAdminUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserAdminOut:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    data = body.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for key, value in data.items():
        setattr(user, key, value)
    if password:
        user.password_hash = hash_password(password)
    await db.commit()
    await db.refresh(user)
    return UserAdminOut.model_validate(user)


@router.get("/sla", response_model=list[SlaConfigOut])
async def list_sla(db: Annotated[AsyncSession, Depends(get_db)]) -> list[SlaConfigOut]:
    rows = (await db.execute(select(SlaConfig).order_by(SlaConfig.category))).scalars().all()
    return [SlaConfigOut.model_validate(r) for r in rows]


@router.put("/sla/{category}", response_model=SlaConfigOut)
async def upsert_sla(
    category: str,
    body: SlaConfigIn,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SlaConfigOut:
    row = await db.get(SlaConfig, category)
    if row is None:
        row = SlaConfig(category=category, days_to_dispose=body.days_to_dispose,
                        warn_before_days=body.warn_before_days)
        db.add(row)
    else:
        row.days_to_dispose = body.days_to_dispose
        row.warn_before_days = body.warn_before_days
    await db.commit()
    await db.refresh(row)
    return SlaConfigOut.model_validate(row)


@router.get("/weights", response_model=WeightsOut)
async def get_weights(db: Annotated[AsyncSession, Depends(get_db)]) -> WeightsOut:
    cfg = await scoring_config.load(db)
    return WeightsOut(**cfg)


@router.put("/weights", response_model=WeightsOut)
async def put_weights(
    body: WeightsIn, db: Annotated[AsyncSession, Depends(get_db)]
) -> WeightsOut:
    cfg = await scoring_config.save(db, body.model_dump())
    return WeightsOut(**cfg)


@router.get("/audit", response_model=list[dict])
async def audit_trail(
    db: Annotated[AsyncSession, Depends(get_db)],
    action: str | None = None,
    limit: int = Query(100, le=500),
) -> list[dict]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id,
            "user_id": str(r.user_id) if r.user_id else None,
            "action": r.action,
            "entity": r.entity,
            "entity_id": r.entity_id,
            "ip": r.ip,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
