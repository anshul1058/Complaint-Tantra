# COMPLAINT-TANTRA — Business Model

> Built for AICTE first, designed to scale to every education regulator — on a free/open stack that costs almost nothing to run.

---

## 1. What we sell

A single-window complaint intelligence platform for regulators:

| Layer | What it does | Who pays for it |
|---|---|---|
| Core platform | Ingestion, case tracking, overlap detection, dashboards, RBAC, reports | License |
| Agentic AI | Intake, triage, web intelligence, briefing agents | Included in license (LLM cost kept near-zero, see §4) |
| Deployment | On-prem / gov-cloud Docker install | One-time implementation |
| Support | AMC, training, SLA config, upgrades | Annual support fee |

**Model:** B2G (Business-to-Government) — one-time implementation + annual license + AMC. This is how Indian gov tech is actually bought; no freemium, no per-seat SaaS.

---

## 2. Customers

**Primary (v1):** AICTE — Regulation Bureau, PGRC, other Bureaus/Cells, Regional Offices.

**Expansion path (same product, same schema, new buyer):**

| Buyer | Why they need it |
|---|---|
| UGC / NCTE / NMC / BCI | Same problem: complaints scattered across cells |
| State technical universities | Affiliation complaints across departments |
| NAAC / accreditation bodies | Institution track-record intelligence |
| Universities (private) | Internal grievance redressal at scale |
| Insurance / banking ombudsman | Same overlap + triage + SLA pattern, non-education |

The overlap engine, triage and Institution 360 are domain-light — only the taxonomy and ingestion connectors change.

---

## 3. Revenue model

| Stream | Timing | Indicative structure |
|---|---|---|
| Implementation | One-time | Fixed fee per bureau onboarded (schema mapping, connectors, training) |
| Annual license | Recurring | Tiered by case volume (e.g., <50k / 50–2L / >2L cases/yr) |
| AMC & support | Recurring | ~15–20% of license: upgrades, SLA tuning, new taxonomies |
| Add-on modules | Optional | Predictive SLA, mobile app, on-prem LLM setup, extra connectors |
| Other regulators | Later | Same license re-sold per organization |

**Why this wins bids:** total 5-year cost is a fraction of a custom-built govt portal or a foreign SaaS — because the stack is free and AI runs on-prem (§4).

---

## 4. Cost model — how we keep it cheap

This is the differentiator in procurement. Every component chosen to be free, open, or near-zero at scale.

### 4.1 Stack = zero license cost

| Concern | Choice | Cost |
|---|---|---|
| Backend / frontend | FastAPI, Next.js | Free |
| Database | PostgreSQL + pgvector (one DB, no separate vector store) | Free |
| Queue / cache | Redis, Celery | Free |
| Object store | MinIO (self-hosted S3) | Free |
| Agents | LangGraph | Free |
| Monitoring | Langfuse (self-hosted) | Free |
| Deploy | Docker Compose on any gov server | Free |

### 4.2 AI cost control (the big one)

| Strategy | Saving |
|---|---|
| **On-prem open LLM** (Llama 3.x / Qwen via Ollama or vLLM) in production | Zero per-token API bills forever |
| **Cheap-first escalation**: small local model handles 80–90% of cases; big model only for gray-zone overlap judgments | Cuts token spend ~70% vs always using a large model |
| **24h web-search cache** per institution; refresh only on new case or manual trigger | Search API calls drop to near zero |
| **Free search fallback**: Google News RSS / GDELT instead of paid SerpAPI/Tavily | ₹0 for the fallback path |
| **PII masking + rules fallback**: if no LLM available, deterministic rules still classify and score | No dependency on paid APIs for core function |
| **Async agents on ingest**, results cached in DB | No idle LLM spend; officers read pre-computed scores |

### 4.3 Infrastructure cost

- Runs on a **single modest server** (8-core, 32 GB RAM handles lakhs of cases with materialized views).
- Prefer **AICTE's own data centre / MeghRaj gov cloud** — data stays inside (compliance requirement) and no foreign SaaS rent.
- Horizontal scaling only when case volume demands it — worker pods, not a re-architecture.

### 4.4 Indicative running cost (per year, one regulator)

| Item | Hackathon/demo | Production (on-prem) |
|---|---|---|
| LLM | Free-tier API key / Ollama on a laptop | Ollama on existing server — ₹0 tokens |
| Web search | Free RSS/GDELT + cached fixtures | RSS/GDELT primary; paid API optional ~₹10–20k/yr |
| Hosting | Free tier (Railway/Render trial) | Gov data centre — already paid for |
| DB / Redis / MinIO | Free managed tiers | Self-hosted — ₹0 |
| **Total marginal cost** | **~₹0** | **~₹10–20k/yr** (search API only) |

Compare: a custom govt portal build typically costs ₹50L–2Cr; foreign SaaS costs ₹20–50L/yr in licences. Complaint-Tantra's marginal cost is essentially the implementation fee + a small support contract.

---

## 5. Go-to-market

1. **Pilot first:** free/low-cost 3-month pilot on one Bureau (RB or PGRC) with synthetic + real sample data. Prove overlap F1 and time-saved numbers.
2. **SIH / demo proof:** live eval numbers + demo script (PRD §12) as the sales deck.
3. **Expand within AICTE:** pilot → other Bureaus → Regional Offices → Competent Authority dashboard.
4. **Sell the same instance** to other regulators — ingestion connectors are the only new work.
5. **Channel:** direct to AICTE IT + Regulation Bureau; empanelled gov-tech vendors if needed for procurement paperwork.

---

## 6. One-line pitch for the procurement slide

> **Free stack, on-prem AI, near-zero running cost** — Complaint-Tantra turns AICTE's scattered complaint data into one explainable, auditable intelligence window for a one-time implementation fee and a small annual support contract.
