from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import create_token, get_current_user, verify_password
from db import get_db
from models import User
from schemas import LoginRequest, TokenResponse, UserOut
from services.audit import add_event

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    ip = request.client.host if request.client else None
    if user is None or not user.active or not verify_password(body.password, user.password_hash):
        add_event(db, action="login_failed", entity="user", entity_id=body.email, ip=ip)
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    add_event(db, action="login", user=user, entity="user", entity_id=str(user.id), ip=ip)
    await db.commit()
    return TokenResponse(access_token=create_token(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return UserOut.model_validate(user)
