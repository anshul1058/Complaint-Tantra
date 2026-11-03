"""Minimal audit trail for login and case views (system.md §8)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models import AuditLog, User


def add_event(
    db: AsyncSession,
    *,
    action: str,
    user: User | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    ip: str | None = None,
    meta: dict | None = None,
) -> AuditLog:
    row = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        ip=ip,
        meta=meta,
    )
    db.add(row)
    return row
