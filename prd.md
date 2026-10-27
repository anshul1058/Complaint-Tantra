# COMPLAINT-TANTRA — Product Requirements Document (PRD)

**Product:** Complaint-Tantra — Agentic Integrated Complaint Monitoring Dashboard
**For:** AICTE (Regulation Bureau, PGRC, other Bureaus/Cells, Regional Offices, senior management, Competent Authority)
**Context:** Smart India Hackathon problem statement — *Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells*
**Version:** 1.0 | **Status:** Draft for team review

---

## 1. Problem

Complaints about technical institutions reach AICTE through multiple Bureaus/Cells (mainly RB and PGRC). There is no central, real-time view, so:
- The same institution can have cases in several Bureaus at once → duplicated work, overlapping or conflicting actions.
- Disposal is delayed; nobody can easily see which Bureau/officer owns what.
- Officers read complaints one by one with no sense of what is most critical, and with no quick view of the institution's public track record.

## 2. Vision

> One window where every complaint about an institution is visible, **understood**, **prioritized**, **cross-checked** and **backed by public evidence**, so AICTE acts once, acts early, and acts consistently.

## 3. Goals & non-goals

### Goals
1. Single source of truth for institution-related complaints across Bureaus.
2. Automatic, explainable **overlap detection** between Bureaus.
3. **AI triage**: order complaints by criticality, emotion and time pressure.
4. **Agentic web intelligence**: past reports/news about the institution with sentiment and citations.
5. Timely disposal via SLA tracking and alerts.
6. Role-based access, full audit trail, report generation.

### Non-goals (v1)
- Auto-deciding or auto-disposing cases (human always decides).
- Replacing Bureau case-management systems (we integrate/ingest, not replace).
- Public-facing complaint filing portal.
- Legal judgment on whether an institution is guilty.

## 4. Users & personas

| Persona | Needs | Key screens |
|---|---|---|
| **RB Officer – Rakesh** | Know if PGRC already has a case on the same college before issuing a notice | Case detail, Overlap room, Institution 360 |
| **PGRC Officer – Meera** | Clear, prioritized queue; spot urgent/emotional complaints early | Priority queue, Case brief |
| **Regional Officer** | Region view of pending/overdue cases | Region dashboard, reports |
| **Senior Management / Bureau Head** | Workload, ageing, bottlenecks, repeat offenders | Command dashboard, reports, alerts |
| **Competent Authority** | Escalations, institution risk at a glance, defensible decisions | Institution 360, escalation list, audit log |
| **System Admin** | Users, SLA rules, scoring weights | Admin console |

## 5. User stories (priority: P0 = must for demo, P1 = should, P2 = nice)

| ID | As a… | I want to… | So that… | P |
|---|---|---|---|---|
| US-1 | Officer | see all complaints for an institution across Bureaus | I know the full picture | P0 |
| US-2 | Officer | get "Potential Overlapping Cases – Coordination Required" with a confidence % and reasons | I avoid conflicting actions | P0 |
| US-3 | Officer | confirm, reject or manually link related cases | the system learns and records coordination | P0 |
| US-4 | Officer | see my queue sorted by AI priority with reasons | I handle the most critical work first | P0 |
| US-5 | Officer | see the emotion/urgency signal of a complaint | I notice distress or safety risks early | P0 |
| US-6 | Officer | open an Institution 360 with news/past reports and sentiment, each with source link | I get public context in seconds | P0 |
| US-7 | Officer | read a one-page AI case brief | I save reading time | P1 |
| US-8 | Officer | get alerts for overlap, due soon, overdue, stuck | I never miss a deadline | P0 |
| US-9 | Manager | see KPIs: total, pending, under process, disposed, transferred, overdue, escalated | I monitor performance | P0 |
| US-10 | Manager | see Bureau-wise workload and region heatmap | I balance resources | P1 |
| US-11 | Manager | generate institution/Bureau/region/status reports + ageing + disposal rate (PDF/CSV) | I report upward | P1 |
| US-12 | Officer | search & filter by institution, Permanent ID, case ID, Bureau, region, category, status, date | I find cases quickly | P0 |
| US-13 | Authority | see the full timestamped action history of any case | accountability | P0 |
| US-14 | Admin | configure SLA per category and scoring weights | policy changes without code | P1 |
| US-15 | Officer | read complaints in Hindi/regional languages with English summary | no language barrier | P1 |
| US-16 | Manager | get a daily "Top 10 needing attention" digest | start the day with focus | P1 |
| US-17 | Authority | see an Institution Risk Index and trend | spot repeat offenders | P1 |
| US-18 | Officer | dismiss an irrelevant web finding | AI errors don't pollute the record | P1 |

## 6. Functional requirements

### 6.1 Ingestion & data (FR-1x)
| ID | Requirement | P |
|---|---|---|
| FR-10 | Ingest cases via CSV/Excel upload and REST API into a common schema | P0 |
| FR-11 | Maintain canonical institution records; match by AICTE Permanent ID, else fuzzy match with confidence | P0 |
| FR-12 | Store raw institution string as received for audit | P0 |
| FR-13 | Support attachments (PDF/images) per case | P2 |

### 6.2 Case tracking & workflow (FR-2x)
| ID | Requirement | P |
|---|---|---|
| FR-20 | Case fields: case ID, date received, category, status, assigned Bureau & officer, last action, next action, expected disposal date | P0 |
| FR-21 | Status machine: Received → Under Process → Transferred / Escalated → Disposed → Reopened | P0 |
| FR-22 | Append-only action log with timestamp, actor, remarks, documents, transfers, escalations | P0 |
| FR-23 | Search & filters across all key fields; saved filters | P0 / P1 |

### 6.3 Overlap detection (FR-3x) — *key innovation*
| ID | Requirement | P |
|---|---|---|
| FR-30 | Detect cases from different Bureaus on the same institution automatically on ingest/update | P0 |
| FR-31 | Tiers: T1 same institution + related issue + overlapping window; T2 same institution/different issue; T3 possible duplicate | P0 |
| FR-32 | Show confidence score and evidence (ID match, name/address score, text similarity, reasoning) | P0 |
| FR-33 | Display banner **"Potential Overlapping Cases – Coordination Required"** on affected cases | P0 |
| FR-34 | Officers can confirm / reject / manually link; decisions logged and used for threshold tuning | P0 |
| FR-35 | Overlap graph view (Coordination Room) | P1 |
| FR-36 | Cross-Bureau redacted summary visibility, full details only per RBAC | P0 |

### 6.4 Agentic AI (FR-4x)
| ID | Requirement | P |
|---|---|---|
| FR-40 | **Intake Agent**: categorize, extract entities, translate to English, summarize | P0 |
| FR-41 | **Triage Agent**: criticality (C1–C4), emotion + intensity, safety flag | P0 |
| FR-42 | **Priority Score** (0–100) from criticality, emotion, time pressure, institution risk, overlap; always show components & reasons | P0 |
| FR-43 | **Safety flag** for self-harm/threat/harassment cues → urgent human-review queue | P0 |
| FR-44 | **Web Intelligence Agent**: search news and public prior reports for the institution, verify same-institution, classify topic/sentiment/severity, cite URL + date | P0 |
| FR-45 | Agent re-plans queries when results are ambiguous (max 3 rounds) | P1 |
| FR-46 | **Reputation Risk Score** and sentiment timeline per institution | P1 |
| FR-47 | **Briefing Agent**: case brief, institution dossier, daily digest | P1 |
| FR-48 | Reports: numbers from SQL only; LLM writes narrative | P0 |
| FR-49 | AI never changes case status; all AI outputs labelled "AI-generated", versioned, replayable | P0 |

### 6.5 Dashboard, alerts, reports (FR-5x)
| ID | Requirement | P |
|---|---|---|
| FR-50 | KPI dashboard: total, pending, under process, disposed, transferred, overdue, escalated | P0 |
| FR-51 | Institution-wise status, Bureau-wise workload, region heatmap | P0 / P1 |
| FR-52 | Alerts: overlap, pending reminder, escalation, SLA/timeline, safety, reputation spike | P0 |
| FR-53 | SLA configurable per category; overdue = computed flag | P0 |
| FR-54 | Reports: institution-wise, region-wise, Bureau-wise, status-wise, ageing, disposal rate, duplicates, monthly/quarterly performance; export PDF/CSV | P1 |
| FR-55 | Live dashboard updates via WebSocket | P1 |

### 6.6 Security & access (FR-6x)
| ID | Requirement | P |
|---|---|---|
| FR-60 | JWT auth, role- and region-scoped RBAC | P0 |
| FR-61 | Audit log of logins, views of sensitive cases, actions | P1 |
| FR-62 | PII masking before external LLM calls; on-prem LLM profile | P1 |
| FR-63 | Admin console for users, SLA, weights | P1 |

## 7. Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | Dashboard API p95 < 800 ms at 100k cases; new case scored < 15 s |
| Scalability | Horizontally scalable workers; materialized views for aggregates |
| Reliability | Agent failure never blocks case intake; fallback to rules + `needs_review` |
| Security | HTTPS, hashed passwords, least privilege, append-only action log |
| Explainability | Every AI score has reasons + confidence; prompts and models versioned |
| Usability | Works on desktop and tablet; accessible contrast; English + Hindi UI labels (P2) |
| Cost | Runs on free/open-source stack; model-agnostic LLM layer |
| Compliance | Public web data only; citations required; data stays in AICTE deployment in production |

## 8. Success metrics

### Product / impact (what we claim in the pitch)
| Metric | Baseline (assumed) | Target |
|---|---|---|
| Time to discover cross-Bureau overlap | Manual / often never | Instant, on ingest |
| Duplicate/overlapping actions | Not measured | Reduce via T1 alerts |
| Time officer spends reading + researching a case | ~20–30 min | < 5 min with brief + dossier |
| Overdue cases | Unknown | Visible daily; alert before breach |
| Disposal rate | — | Trackable by Bureau/region/month |

*(Baselines are assumptions for the pitch; present them as such and validate with AICTE officers if possible.)*

### Model quality (shown with live eval on synthetic data)
Overlap T1 F1 ≥ 0.85 · Institution match P ≥ 0.95 · Criticality accuracy ≥ 0.80 · Emotion macro-F1 ≥ 0.70 · Safety-flag recall ≥ 0.95 · Web finding same-institution precision ≥ 0.90 with 100% citation coverage.

## 9. Scope

### MVP (hackathon build)
Common-schema ingestion (CSV + API) · institution resolution · case tracking + action log + state machine · **overlap detection with confidence + confirm/reject/link** · **Intake + Triage + Web Intelligence agents** · priority queue · Institution 360 with sentiment timeline · KPI dashboard + Bureau workload · alerts (overlap, due soon, overdue, safety) · RBAC with 3–4 demo roles · PDF/CSV report export · synthetic dataset · eval dashboard.

### Phase 2
Briefing agent digests, region heatmap, risk index, multilingual UI, graph Coordination Room polish, saved views, notifications by email/SMS/WhatsApp.

### Phase 3 (roadmap slide)
Direct connectors to RB/PGRC systems · on-prem LLM deployment · continuous learning from officer decisions · predictive analytics (which cases will breach SLA) · integration with AICTE portal and state regulators · mobile app.

## 10. Differentiators (what makes us win)

1. **Explainable overlap engine** with confidence, tiers, officer feedback, measured F1.
2. **Agentic web intelligence** that plans, verifies and cites — not just a sentiment widget.
3. **Emotion-aware, time-aware triage** with a **safety escalation path**, transparent score components.
4. **Institution 360 + Risk Index** merging internal complaints with public signals.
5. **Responsible AI by design**: human-in-loop, audit, PII masking, on-prem option.
6. **Proof, not claims**: live evaluation numbers on a labelled synthetic benchmark.
7. **Deployable**: Docker Compose, free/open stack, clear integration story.

## 11. Dependencies & assumptions

- No real AICTE data available → synthetic data with realistic noise; real integration described via ingestion layer.
- Web search API key (or free fallback via RSS/GDELT) and one LLM provider key; local fallback via Ollama.
- Permanent ID may be missing in some Bureau data (handled by fuzzy matching).
- Public news about an institution is **context, not evidence of violation**; UI states this explicitly.

## 12. Demo script (5 minutes — rehearse this)

| Min | Scene | What judges see |
|---|---|---|
| 0:00 | **Problem** | 20-second story: same college, two Bureaus, two conflicting notices |
| 0:30 | **Login as RB Officer** | Priority queue, top card: C1 fraud complaint, fear (0.8), 3 days to SLA, "why #1" panel |
| 1:15 | **Ingest live** | Upload a new PGRC case for the same college under a messy name ("A.B.C. Coll. of Engg & Tech") |
| 1:45 | **Overlap fires** | Banner: *Potential Overlapping Cases – Coordination Required*, T1, 91% confidence, evidence breakdown; officer confirms; both Bureaus notified |
| 2:30 | **Agent at work** | Web Intelligence trace: plans queries, rejects a same-name college in another state, finds 3 cited articles, sentiment timeline turns negative |
| 3:15 | **Safety flag** | A complaint with distress cues jumps to urgent queue; human review required |
| 3:45 | **Manager view** | KPIs, Bureau workload, ageing chart, region heatmap; switch role to Competent Authority (different permissions) |
| 4:15 | **Proof** | Eval page: overlap precision/recall, before/after officer feedback |
| 4:40 | **Close** | Roadmap: connectors, on-prem LLM, predictive SLA; "AI recommends, AICTE decides." |

**Backup plan:** pre-cached web fixtures + recorded video of the full flow.

## 13. Delivery plan

Adjust dates to the actual SIH schedule; this is by phase.

| Phase | Focus | Deliverables |
|---|---|---|
| **P0 — Foundations** | Schema, auth/RBAC, ingestion, synthetic data generator, case CRUD + state machine | Working API + seeded DB |
| **P1 — Core intelligence** | Institution resolution, overlap pipeline, Intake + Triage agents, priority score | Overlap demo, queue |
| **P2 — Agentic web layer** | Web Intelligence Agent, cache, citations, sentiment timeline, Institution 360 | Dossier view |
| **P3 — Dashboard & alerts** | KPIs, workload, SLA engine, alerts, reports/export | Full UI |
| **P4 — Proof & polish** | Eval harness + charts, safety-flag flow, prompts tuning, Docker one-command, demo script, deck, video | Final-ready |
| **Buffer** | Bugs, rehearsal ×3, fallback assets | — |

### Suggested team split (6 members)
| Role | Owns |
|---|---|
| AI/Agents lead (you) | LangGraph, prompts, web agent, triage, eval |
| Backend lead | FastAPI, DB, state machine, RBAC, SLA/alerts |
| Data/ML | Entity resolution, embeddings, overlap scoring, synthetic data |
| Frontend lead | Dashboard, queue, Institution 360 |
| Frontend/UX + viz | Overlap graph, heatmap, reports, design polish |
| DevOps + PM + presenter | Docker, deploy, deck, demo script, rehearsals |

## 14. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Over-scoping | Unfinished demo | Strict P0 list; freeze features before final phase |
| LLM/API failures during demo | Embarrassing | Cached fixtures, local Ollama fallback, recorded video |
| Overlap false positives | Judges question accuracy | Confidence + tiers + eval numbers + officer feedback |
| Wrong-institution web matches | Misleading intel | Same-institution check, confidence threshold, dismiss button |
| Judges ask "real data?" | Credibility | Ingestion layer + synthetic benchmark + integration roadmap |
| Privacy concerns | Trust | PII masking, on-prem LLM, RBAC, audit, public-data-only web agent |

## 15. Open questions

1. Which fields do RB and PGRC actually share today (to refine the common schema)?
2. Exact SLA timelines per complaint category (use configurable placeholders).
3. Should the safety flag also notify an external helpline/authority, or only the Bureau head?
4. Are regional-language complaints common enough to make multilingual UI P0?
5. Retention policy for web findings and agent outputs.

## 16. Pitch checklist (for the final deck)

- [ ] 1 slide: problem with a concrete story (duplicate action on same college)
- [ ] 1 slide: solution in one picture (architecture diagram)
- [ ] 1 slide: overlap engine (tiers + confidence + feedback loop)
- [ ] 1 slide: agentic AI (agents + web plan→verify→cite loop)
- [ ] 1 slide: Responsible AI (human-in-loop, audit, citations, PII)
- [ ] 1 slide: eval numbers
- [ ] 1 slide: impact + feasibility + roadmap
- [ ] Live demo + backup video
