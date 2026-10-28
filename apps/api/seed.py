"""Minimal demo seed: users + SLA config only. The synthetic dataset is AI member's scope."""

import asyncio
import sys

from sqlalchemy import select

from auth import hash_password
from db import SessionLocal, init_db
from models import SlaConfig, User

USERS = [
    ("Asha Verma", "asha@rb.gov.in", "officer", "RB", "North", "demo123"),
    ("Ravi Kumar", "ravi@pgrc.gov.in", "officer", "PGRC", "South", "demo123"),
    ("Meera Iyer", "meera@rb.gov.in", "regional", "RB", "West", "demo123"),
    ("S. Sharma", "sharma@hq.gov.in", "senior", None, None, "demo123"),
    ("Justice P. Nair", "nair@hq.gov.in", "authority", None, None, "demo123"),
    ("Admin", "admin@hq.gov.in", "admin", None, None, "demo123"),
]

SLA = [
    ("safety", 5, 2),
    ("fraud", 10, 3),
    ("fees", 15, 3),
    ("faculty", 30, 7),
    ("examination", 20, 5),
    ("placement", 30, 7),
    ("infrastructure", 45, 10),
    ("certificate", 15, 3),
    ("other", 30, 7),
]


async def seed() -> None:
    await init_db()
    async with SessionLocal() as db:
        for cat, days, warn in SLA:
            if await db.get(SlaConfig, cat) is None:
                db.add(SlaConfig(category=cat, days_to_dispose=days, warn_before_days=warn))
        for name, email, role, bureau, region, pw in USERS:
            existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if existing is None:
                db.add(User(name=name, email=email, role=role, bureau=bureau,
                            region=region, active=True, password_hash=hash_password(pw)))
        await db.commit()
    print(f"Seeded {len(USERS)} users (password: demo123) and {len(SLA)} SLA categories.")


if __name__ == "__main__":
    sys.exit(asyncio.run(seed()))
