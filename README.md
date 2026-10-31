# Complaint-Tantra

**AI-powered Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells.**

Complaint-Tantra is built for the Smart India Hackathon problem of fragmented grievance handling at AICTE. Complaints about the same institution can land in different bureaus (RB, PGRC, regional offices), in different languages, with different names for the same college. The platform gives every bureau a shared intake, triage, SLA and overlap-detection layer while preserving role-based access.

---

## What it does

- **Unified intake** — JSON or CSV complaints, multilingual text, institution resolution by AICTE Permanent ID or fuzzy name matching.
- **AI/ML pipeline** — intake translation/classification, triage (criticality C1–C4, emotion, safety flag), deterministic priority scoring, overlap detection, institution risk index, web intelligence and case briefs.
- **Explainable priority** — every score carries its component breakdown and human-readable reasons. The LLM never decides the score and never changes case status.
- **Cross-bureau overlap detection** — hybrid scoring (institution + text similarity + category + time) with T1/T2/T3 tiers and officer confirm/reject decisions.
- **SLA engine** — deterministic due-soon / overdue / stuck detection, hourly alerts, append-only audit log.
- **Role-based dashboards** — officer, regional, senior, authority and admin scopes; cross-bureau case summaries are redacted.
- **Next.js frontend** — dashboard, priority queue, case dossier, overlap coordination room, institution 360° page and reports.

---

## Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│  apps/web (Next.js 16)      │  HTTP  │  apps/api (FastAPI)              │
│  App Router + TypeScript    │ ─────► │  routers → services → agents      │
│  Tailwind + Recharts        │  JWT   │  APScheduler workers              │
└─────────────────────────────┘        └──────────────┬───────────────────┘
                                                      │ SQLAlchemy async
                                       ┌──────────────▼───────────────────┐
                                       │ PostgreSQL + pgvector + pg_trgm  │
                                       │ cases, institutions, links,      │
                                       │ alerts, agent_runs, SLA config   │
                                       └──────────────────────────────────┘
```

AI calls are provider-agnostic through **LiteLLM** (`LLM_PROVIDER=ollama|gemini|anthropic|openai-free`). If no LLM is reachable, the pipeline degrades to deterministic rules and marks output `needs_review` — ingest never blocks.

---

## Project structure

```
Complaint-Tantra/
├── apps/
│   ├── api/                        # FastAPI backend
│   │   ├── main.py                 # app factory, CORS, router mounting, lifespan
│   │   ├── config.py               # env-backed settings
│   │   ├── db.py                   # async engine/session, schema + pgvector indexes
│   │   ├── auth.py                 # password hashing, JWT, RBAC helpers
│   │   ├── seed.py                 # demo users + SLA categories
│   │   ├── seed_demo.py            # demo cases that exercise agents + overlaps
│   │   ├── Dockerfile              # backend image
│   │   ├── models/__init__.py      # SQLAlchemy tables mirroring system.md §2
│   │   ├── schemas/__init__.py     # Pydantic request/response contracts
│   │   ├── routers/
│   │   │   ├── auth.py             # POST /auth/login, GET /auth/me
│   │   │   ├── ingest.py           # POST /ingest/cases, /ingest/cases/csv
│   │   │   ├── cases.py            # /cases, /cases/{id}, actions, links, queue
│   │   │   ├── institutions.py     # profile, risk, web intel, refresh
│   │   │   ├── dashboard.py        # summary, workload, heatmap
│   │   │   ├── alerts.py           # scoped alert feed
│   │   │   ├── reports.py          # JSON/CSV reports
│   │   │   ├── agents.py           # replay endpoint
│   │   │   └── meta.py             # statuses, transitions, categories, roles
│   │   ├── services/
│   │   │   ├── state_machine.py    # statuses + validated transitions
│   │   │   ├── case_service.py     # create case, apply action, resolve institution
│   │   │   ├── sla_engine.py       # pure SLA math (overdue is computed)
│   │   │   ├── priority.py         # deterministic §4.4 priority formula
│   │   │   ├── overlap.py          # hybrid scoring + tiering
│   │   │   ├── entity_resolution.py# name normalisation + fuzzy match
│   │   │   ├── embeddings.py       # BGE-M3 (lazy) + hashing fallback, 1024-dim
│   │   │   ├── risk.py             # institution risk index
│   │   │   └── report_service.py   # SQL aggregates for reports
│   │   ├── agents/
│   │   │   ├── llm.py              # LiteLLM wrapper + strict JSON parsing
│   │   │   ├── ai_member.py        # prompt loading for intake/triage
│   │   │   ├── schemas.py          # strict Pydantic agent outputs
│   │   │   ├── graph.py            # LangGraph flow + offline sequential fallback
│   │   │   ├── overlap.py          # gray-zone LLM judge
│   │   │   ├── web_intel.py        # Tavily live search + fixtures + classifier
│   │   │   ├── briefing.py         # case brief narrative
│   │   │   └── prompts/v1/         # versioned intake + triage prompts
│   │   ├── workers/scheduler.py    # hourly SLA alerts, nightly risk/MV refresh
│   │   └── tests/                  # state machine, SLA, agents (26 tests)
│   │
│   └── web/                        # Next.js frontend (canonical frontend entrypoint)
│       ├── src/app/
│       │   ├── page.tsx            # dashboard
│       │   ├── queue/page.tsx      # priority queue
│       │   ├── cases/page.tsx      # case search/filter
│       │   ├── cases/[id]/page.tsx # case dossier + actions + timeline
│       │   ├── overlaps/page.tsx   # overlap coordination room
│       │   ├── institutions/[id]/page.tsx
│       │   ├── reports/page.tsx
│       │   └── login/page.tsx
│       ├── src/components/         # dashboard, case, layout and UI primitives
│       ├── src/lib/api/client.ts   # typed API wrapper + auth header
│       ├── src/lib/auth.tsx        # JWT login, role switching, session state
│       ├── src/lib/types.ts        # frontend contract types
│       └── src/lib/mock/data.ts    # dev-only fallback used when API is offline
│
├── data/
│   ├── institutions.csv            # cleaned AICTE institution master (~13k rows)
│   ├── institutions_stage1.json
│   ├── web_fixtures/               # offline web-intel fixtures
│   └── raw/                        # scraped sources (gitignored)
├── eval/                           # runnable offline evaluations
│   ├── eval_institutions.py
│   ├── eval_triage.py
│   ├── eval_overlap.py
│   └── run_all.py
├── scripts/                        # dataset build / enrichment / geo scripts
├── Docs_md/                        # PRD, architecture, system design, guides
├── Dockerfile                      # frontend image (apps/web)
└── .env.example                    # environment template
```

The root `index.html` placeholder has been removed. **`apps/web` is the frontend** and is what the root Dockerfile builds.

---

## Tech stack

| Layer | Stack |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn-style components, Recharts, Lucide |
| Backend | FastAPI, SQLAlchemy 2 async, Pydantic 2, PyJWT, APScheduler |
| Database | PostgreSQL 16 + `pgvector` + `pg_trgm` (Supabase compatible) |
| AI/ML | LiteLLM, LangGraph, strict Pydantic JSON schemas, rapidfuzz-style entity matching, deterministic scoring |
| Search | Tavily API (optional), cached fixtures for offline demos |
| Deploy | Docker, Vercel/free-tier friendly |

---

## Getting started

### 1. Prerequisites

- Python 3.12+
- Node.js 20+ (Node 22 recommended)
- PostgreSQL 16 with `pgvector` (or a Supabase project)

### 2. Environment

```bash
cp .env.example .env
```

Fill at minimum:

```ini
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
JWT_SECRET=change-me-long-random-string
CORS_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

AI keys are optional. With `LLM_PROVIDER=none` (or no LLM running) the system uses deterministic rules and still works end to end.

Embeddings use **BAAI/bge-m3**, loaded lazily on the first ingest; that first call downloads ~2 GB. Set `EMBEDDING_BACKEND=hash` for offline/CI runs or when the model is not cached.

### 3. Backend

```bash
cd apps/api
python -m venv ../../.venv && source ../../.venv/bin/activate
pip install -r requirements.txt
python seed.py          # users + SLA categories (password: demo123)
python seed_demo.py     # optional demo cases + planted overlaps
uvicorn main:app --reload --port 8000
```

- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

Database extensions and tables are created automatically on startup.

### 4. Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open <http://localhost:3000>. The frontend falls back to local mock data if the API is unreachable, so it renders even before the backend is up.

### Demo accounts

| Role | Email | Password |
|---|---|---|
| RB officer | asha@rb.gov.in | demo123 |
| PGRC officer | ravi@pgrc.gov.in | demo123 |
| Regional | meera@rb.gov.in | demo123 |
| Senior management | sharma@hq.gov.in | demo123 |
| Competent Authority | nair@hq.gov.in | demo123 |
| Admin | admin@hq.gov.in | demo123 |

---

## Docker

### Frontend

```bash
docker build -t complaint-tantra-web \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 .

docker run -p 3000:3000 complaint-tantra-web
```

### Backend

```bash
docker build -t complaint-tantra-api apps/api
docker run -p 8000:8000 --env-file .env complaint-tantra-api
```

The backend needs a reachable PostgreSQL instance (local, Docker network, or Supabase) via `DATABASE_URL`.

---

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/login` | JWT login |
| GET | `/auth/me` | current user |
| POST | `/ingest/cases` | single or bulk JSON ingest |
| POST | `/ingest/cases/csv` | CSV ingest |
| GET | `/cases` | search + filters (bureau, status, category, region, date, priority sort) |
| GET | `/cases/{id}` | dossier + timeline + brief |
| GET | `/cases/{id}/actions` | append-only action log |
| POST | `/cases/{id}/actions` | remark / assign / transfer / escalate / dispose / reopen |
| GET | `/cases/{id}/overlaps` | overlaps for one case |
| GET | `/overlaps` | all visible overlaps with evidence |
| POST | `/overlaps/{link_id}/decision` | confirm / reject |
| POST | `/cases/{id}/link` | manual link |
| GET | `/queue/priority` | ranked open cases |
| GET | `/institutions/{id}` | profile + history + risk |
| GET | `/institutions/{id}/risk` | risk index breakdown |
| GET | `/institutions/{id}/intel` | cited web findings |
| POST | `/institutions/{id}/intel/refresh` | re-run web intelligence |
| GET | `/dashboard/summary` | KPI counts |
| GET | `/dashboard/workload` | bureau workload |
| GET | `/dashboard/heatmap` | region/state density |
| GET | `/alerts` | scoped alert feed |
| GET | `/reports/{type}` | institution / bureau / region / ageing / disposal (`json` or `csv`) |
| POST | `/agents/replay/{case_id}` | re-run agents for reproducibility |
| GET | `/meta/options` | statuses, transitions, categories, roles |

---

## AI/ML pipeline

1. **Intake agent** (`agents/ai_member.py`, prompt `prompts/v1/intake.md`) — language detection, English translation, category/subcategory, entities, neutral summary.
2. **Triage agent** (prompt `prompts/v1/triage.md`) — criticality C1–C4, emotion label + intensity, safety flag and urgency cues.
3. **Priority score** (`services/priority.py`) — deterministic formula:
   `0.35·criticality + 0.20·emotion + 0.25·time_pressure + 0.10·risk + 0.10·overlap`, safety flags bypass to 100.
4. **Institution resolution** (`services/entity_resolution.py`) — normalization + token-set fuzzy matching; ≥0.90 auto-link, 0.70–0.90 needs confirmation.
5. **Overlap detection** (`services/overlap.py`) — `0.40·institution + 0.30·text cosine + 0.15·category + 0.15·time`; T1/T2/T3 tiers; gray zone 0.45–0.70 can call the LLM judge.
6. **Web intelligence** (`agents/web_intel.py`) — Tavily search when `TAVILY_API_KEY` is set, fixtures for offline demos, same-institution guard, every finding needs a URL and date.
7. **Risk index** (`services/risk.py`) — complaint load, repeat offenders, negative web coverage and overlap density.
8. **Briefing** (`agents/briefing.py`) — narrative only; SQL supplies all numbers.

Every agent run is stored in `agent_runs` with model, prompt version, input hash, latency and token counts.

---

## Running the evaluations

```bash
python eval/run_all.py
```

Latest results on the bundled data:

```
institution matching: P=0.991 R=0.924 F1=0.957   (target P>=0.95, R>=0.90)  PASS
triage: accuracy=0.846 macro-F1=0.837 safety-recall=1.000                  PASS
overlap: T1 F1=1.000, T2 F1=1.000                                          PASS
```

Tests:

```bash
cd apps/api && pytest -q     # 26 passed
cd apps/web && npm run lint && npm run build
```

---

## Screenshots

Capture these after running the demo (save under `Docs_md/screenshots/`):

| Screen | Route | Suggested file |
|---|---|---|
| National dashboard (KPIs, workload, heatmap) | `/` | `dashboard.png` |
| AI priority queue with explanations | `/queue` | `priority-queue.png` |
| Case dossier with AI brief and timeline | `/cases/{id}` | `case-dossier.png` |
| Cross-bureau overlap coordination room | `/overlaps` | `overlaps.png` |
| Institution 360° + web intelligence | `/institutions/{id}` | `institution-360.png` |
| Executive reports | `/reports` | `reports.png` |

Example embed once the files exist:

```markdown
![Dashboard](Docs_md/screenshots/dashboard.png)
```

---

## Roles and access

| Capability | Officer | Regional | Senior | Authority | Admin |
|---|---|---|---|---|---|
| View own-bureau cases | yes | region | all | all | all |
| View cross-bureau summary | yes | yes | yes | yes | yes |
| Act on case | yes | yes | yes | yes | no |
| Confirm/reject overlaps | yes | yes | yes | yes | no |
| Org-wide dashboards/reports | no | region | yes | yes | yes |
| Manage users/SLA/weights | no | no | no | no | yes |

Cross-bureau overlap views return summaries only — raw text and AI internals stay inside the owning bureau.

---

## Documentation

- [`Docs_md/prd.md`](Docs_md/prd.md) — product requirements and screens
- [`Docs_md/architecture.md`](Docs_md/architecture.md) — architecture and flows
- [`Docs_md/system.md`](Docs_md/system.md) — data model, state machine, scoring, contracts
- [`Docs_md/backend-guide.md`](Docs_md/backend-guide.md)
- [`Docs_md/frontend-guide.md`](Docs_md/frontend-guide.md)
- [`Docs_md/aiml-guide.md`](Docs_md/aiml-guide.md)
- [`Docs_md/institutions-csv-guide.md`](Docs_md/institutions-csv-guide.md)

---

## License

See [`LICENSE`](LICENSE).
