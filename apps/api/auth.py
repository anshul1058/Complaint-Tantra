import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db import get_db
from models import User

bearer = HTTPBearer(auto_error=False)

ROLE_OFFICER = "officer"
ROLE_REGIONAL = "regional"
ROLE_SENIOR = "senior"
ROLE_AUTHORITY = "authority"
ROLE_ADMIN = "admin"
ALL_ROLES = [ROLE_OFFICER, ROLE_REGIONAL, ROLE_SENIOR, ROLE_AUTHORITY, ROLE_ADMIN]

# Roles that see every case (system.md §8)
WIDE_ROLES = {ROLE_SENIOR, ROLE_AUTHORITY, ROLE_ADMIN}


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed or "$" not in hashed:
        return False
    salt, digest_hex = hashed.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100_000)
    return hmac.compare_digest(digest.hex(), digest_hex)


def create_token(user: User) -> str:
    payload = {
        "user_id": str(user.id),
        "role": user.role,
        "bureau": user.bureau,
        "region": user.region,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        claims = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = await db.get(User, uuid.UUID(claims["user_id"]))
    if user is None or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User inactive or missing")
    return user


def require_roles(*roles: str):
    async def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return checker


def can_see_full_case(user: User, case_bureau: str) -> bool:
    if user.role in WIDE_ROLES:
        return True
    if user.role == ROLE_REGIONAL:
        return user.bureau == case_bureau or user.region is not None
    return user.bureau == case_bureau


def can_act_on_case(user: User, case_bureau: str) -> bool:
    if user.role in (ROLE_SENIOR, ROLE_AUTHORITY):
        return True
    if user.role == ROLE_REGIONAL:
        return user.bureau == case_bureau or user.region is not None
    if user.role == ROLE_OFFICER:
        return user.bureau == case_bureau
    return False  # admin manages config, does not act on cases (§8)
