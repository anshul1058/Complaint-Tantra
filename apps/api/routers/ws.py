"""Live event stream for dashboards/alerts (system.md §10)."""

import asyncio
import json
import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from config import settings
from db import SessionLocal
from models import User

router = APIRouter(tags=["ws"])


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()
        self.lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self.lock:
            self.connections.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self.lock:
            self.connections.discard(ws)

    async def broadcast(self, event: dict) -> None:
        payload = json.dumps(event, default=str)
        async with self.lock:
            dead = []
            for ws in self.connections:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.connections.discard(ws)


manager = ConnectionManager()


async def broadcast_event(kind: str, data: dict) -> None:
    await manager.broadcast({"kind": kind, "data": data})


@router.websocket("/ws/events")
async def events(ws: WebSocket, token: Annotated[str | None, Query()] = None) -> None:
    if not token:
        await ws.close(code=4401)
        return
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = uuid.UUID(claims["user_id"])
    except Exception:
        await ws.close(code=4401)
        return
    async with SessionLocal() as db:
        user = await db.get(User, user_id)
        if user is None or not user.active:
            await ws.close(code=4401)
            return
    await manager.connect(ws)
    try:
        await ws.send_text(json.dumps({"kind": "connected", "data": {"user": user.email}}))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(ws)
