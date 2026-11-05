import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db import SessionLocal, init_db
from routers import (
    admin,
    agents,
    alerts,
    attachments,
    auth,
    cases,
    dashboard,
    filters,
    ingest,
    institutions,
    meta,
    reports,
    public,
    ws,
)
from workers.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger("complaint_tantra")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from services.scoring_config import load as load_weights

    async with SessionLocal() as db:
        await load_weights(db)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Complaint-Tantra API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    started = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(json.dumps({
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": int((time.time() - started) * 1000),
    }))
    return response


for r in (auth, meta, ingest, public, cases, institutions, dashboard, alerts, reports, agents,
          admin, filters, attachments, ws):
    app.include_router(r.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
