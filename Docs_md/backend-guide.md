# Backend Guide — Complaint-Tantra

Owner: backend member. Stack: **FastAPI + SQLAlchemy + PostgreSQL (pgvector)**.
Read first: `system.md` (data model §2, state machine §3, API surface §7, RBAC §8, SLA §9).

## Your scope

Everything under `apps/api/`: routers, services, models, schemas, auth, workers/scheduler.
You do NOT write UI or AI prompts — you call them.

## Repo layout (create this)

```
apps/api/
├── main.py              # FastAPI app, CORS, router mounting
├── config.py            # env vars (DATABASE_URL, JWT_SECRET, ...)
├── models/              # SQLAlchemy models (mirror system.md §2 exactly)
├── schemas/             # Pydantic request/response models
├── routers/             # auth, cases, institutions, overlaps, dashboard, reports, alerts
├── services/            # case_service, sla_engine, entity_resolution, report_service
├── agents/              # thin wrappers that call the AI member's functions
└── workers/             # APScheduler jobs (demo) → Celery later
```

## Build order

1. **DB schema** — migrate every table in `system.md` §2 (institutions, cases, case_actions, case_links, web_findings, institution_risk, alerts, sla_config, users, agent_runs). Enable `pgvector`, `pg_trgm`. Demo DB: Supabase free (it supports pgvector).
2. **Auth** — `POST /auth/login`, JWT with claims `{user_id, role, bureau, region}`. Every query scoped by bureau/region per RBAC matrix `system.md` §8. Roles: officer, regional, senior, authority, admin.
3. **Case state machine** — statuses and transitions exactly per `system.md` §3. Every transition writes a `case_actions` row. `Overdue` is computed, never stored.
4. **CRUD + search** — `/cases` with filters (institution, case_no, bureau, region, category, status, date range, sort=priority), `/cases/{id}` detail+timeline, `POST /cases/{id}/actions`.
5. **SLA engine** — deterministic, in `services/sla_engine.py`. Load days-per-category from `sla_config`. Scheduler (APScheduler in-process for demo): hourly "due soon / overdue / stuck" checks → insert into `alerts`.
6. **Overlaps + dashboard + reports** — endpoints from `system.md` §7. Numbers from SQL only (materialized view `mv_dashboard_counts`).
7. **Agent integration** — call the AI member's functions via thin wrappers in `agents/`:

```python
# agents/intake.py — contract with AI member, agreed once, don't change silently
def run_intake(case: dict) -> dict:   # returns validated JSON per system.md §6.2
def run_triage(case: dict) -> dict:   # system.md §6.3
def detect_overlaps(case: dict) -> list:  # system.md §5
```

Agent runs are async on ingest; store every run in `agent_runs`. AI never sets `status` — only suggests fields (`criticality`, `priority_score`, `ai_summary`, ...).

## Contracts (freeze early, notify others when changed)

- **API contract**: expose `/openapi.json` (FastAPI default). Frontend generates types from it.
- **AI contract**: the 3 functions above + `compute_priority(components) -> score` (the formula in `system.md` §4.4 lives in YOUR code, not the LLM).
- **Env vars**: `DATABASE_URL`, `JWT_SECRET`, `SUPABASE_SERVICE_KEY` (demo storage), `LLM_PROVIDER` + keys (from AI member).

## Demo-mode shortcuts (documented, reversible)

| Full (production) | Demo |
|---|---|
| Celery worker + beat + Redis | APScheduler inside API process |
| MinIO | Supabase Storage bucket, or Postgres `bytea` |
| Ollama/vLLM | AI member runs model locally / free API |

## Definition of done

- `curl` through every endpoint in `system.md` §7 against seeded data works
- RBAC: officer of bureau A cannot read bureau B's case content (redacted summary only for overlaps)
- pytest for state machine transitions + SLA math (the only non-trivial logic — leave a runnable check)
