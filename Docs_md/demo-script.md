# Complaint-Tantra — Demo Video Script

**Target length:** 4:30 core, or ~4:55 with the optional AI-pipeline insert
**Format:** screen recording + voiceover
**Resolution:** 1080p
**Problem statement:** Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells

---

## Pre-flight checklist

Run before recording:

```bash
# Terminal 1 — backend
cd apps/api
python seed.py
python seed_demo.py
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd apps/web
npm run dev
```

- Open <http://localhost:3000/login> in a clean browser profile.
- Close notifications, bookmarks bar and extra tabs. Set zoom to 110% for readability.
- Keep a second tab on the login page for the public-complaint scene.
- Have the six-stage pipeline slide ready if you use the 0:55 insert.
- Demo accounts are one-click presets on the login form (password `demo123`).

**Pre-seeded story:**

- Apex Institute (Greater Noida) has complaints in RB and PGRC.
- Vidyapeeth (Pune) and Government Polytechnic (Diglipur) also have planted overlaps.

---

## AI pipeline — what to explain, and where

**Where to put it (recommended):** a 25–30 second beat at **0:55**, immediately after the citizen complaint is submitted and before you log in. The viewer has just watched a complaint move; that is the moment the invisible work is interesting.

- With the insert, the video runs about **4:55**. If 4:30 is a hard limit, use the short version in the intake scene and keep the full pipeline for the deck/Q&A.
- Also make it **one slide in the pitch deck** — the same diagram, no narration needed there.

### One-slide diagram

```
Complaint
   │
   ▼
[1] Intake agent ........ language, translation, category, entities, summary
   │
   ▼
[2] Triage agent ........ C1–C4 criticality, emotion + intensity, safety flag
   │
   ├──► [3] Institution resolution .... Permanent ID → fuzzy name + address
   │
   ├──► [4] Deterministic scoring ..... priority score + overlap (T1/T2/T3)
   │
   └──► [5] Web intel + risk index .... cited findings, sentiment, risk
                                   │
                                   ▼
                 [6] Briefing agent ... narrative only; SQL supplies numbers
```

### Narration for the 0:55 insert

**ON SCREEN:** Pipeline slide with the six stages highlighting in order.

**NARRATION:**

> Here is what just happened in those few seconds. One — intake detects the language, translates, classifies the category and extracts entities. Two — triage assigns criticality from C1 to C4, reads the emotional signal, and raises the safety flag. Three — institution resolution uses the AICTE Permanent ID first, then fuzzy name and address matching, so the same college is never counted twice. Four — deterministic code scores priority and detects overlaps as T1, T2 or T3. Five — the web agent pulls cited public intelligence and updates the risk index. Six — the briefing agent writes the narrative.
>
> The LLM handles language and judgement. Every number — priority, overlap confidence, SLA, risk — comes from deterministic code, and the AI never changes case status. If any agent fails, intake still completes with a needs-review flag.

### If you must stay at 4:30 (no insert)

- **At 0:25–0:55 (intake):** add one sentence — *"Six stages run on every complaint: intake, triage, institution resolution, deterministic priority and overlap scoring, web intelligence, and briefing."*
- **At 2:25–3:05 (overlap room):** explain the union of four signals — institution match 40%, text similarity 30%, category 15%, time window 15% — and that 0.45–0.70 goes to an LLM judge.
- **At 3:05–3:35 (Institution 360):** explain that the web agent plans queries, verifies the same institution, cites URL and date, and can refine up to three rounds.

### What is LLM vs deterministic (for Q&A)

| Step | LLM | Deterministic code |
|---|---|---|
| Intake / translation / category | yes | rules fallback |
| Triage criticality + emotion + safety | yes | rules + sentiment model fallback |
| Institution matching | embeddings + fuzzy match | yes (thresholds 0.90 / 0.70–0.90) |
| Priority score | no | yes — fixed weights, safety bypass to 100 |
| Overlap score + tier | only in the 0.45–0.70 gray zone | yes — 40/30/15/15 weights |
| SLA / overdue / alerts | no | yes — computed flags |
| Risk index | web sentiment input | yes — aggregation |
| Brief / dossier narrative | yes | numbers always from SQL |

Every agent run is stored in `agent_runs` with model, prompt version, input hash, latency and token counts, so any output can be replayed.

---

## 0:00–0:25 — The problem

**ON SCREEN:** Title card or slow pan over the login screen.

**NARRATION:**

> Right now, a complaint about one college can land in the Regulation Bureau. Another lands in PGRC. Different officers, different formats, sometimes different spellings of the same institution. Nobody sees the full picture, so AICTE investigates twice, or not at all. Complaint-Tantra fixes that — one window for every complaint, across every bureau.

---

## 0:25–0:55 — Citizen intake

**ON SCREEN:** Click the **Register Complaint** tab. Fill quickly (or use pre-filled values) with:

- College: `Apex Institute of Technology and Management, Greater Noida`
- Category: `Safety`
- Description: mentions harassment of a student who reported an unapproved course, and that the student has threatened self-harm.

Submit the form.

**NARRATION:**

> Let's start where every case starts — a citizen. I register a complaint for Apex Institute. The moment I submit, the intake agent translates and classifies it, the triage agent flags the safety cues, resolves the institution, scores priority, and checks for overlaps. It is already in the PGRC officer's queue — no manual data entry.

**ON SCREEN:** Show the success message with the generated case number.

---

## 0:55–1:35 — Login and command dashboard

**ON SCREEN:** Officer Login → click the **PGRC Officer** preset → **Sign In**. Land on `/`.

**NARRATION:**

> I sign in as a PGRC officer. This is the command dashboard: total complaints, pending, under process, disposed, overdue, escalated, and safety-flagged. Bureau workload, status distribution, regional heatmap, live SLA alerts, and recent complaints — all scoped to my role. A senior officer sees the same data nationwide; an RB officer sees only what RB is allowed to see.

**ON SCREEN:** Hover KPI cards, scroll to workload and heatmap, point at the sidebar role scope.

---

## 1:35–2:25 — Priority queue and case dossier

**ON SCREEN:** Click **Priority Queue** (`/queue`). Show the top card and expand it.

**NARRATION:**

> The queue is not sorted by date. It is sorted by an explainable priority score: criticality, emotional distress, SLA time pressure, institution risk, and overlap. The complaint I just filed is at the top — because the safety flag routes it straight to urgent human review. Every score opens into its components and reasons. The AI never decides the case; it only tells the officer why this one should be read first.

**ON SCREEN:** Click the top case → `/cases/{id}`. Show priority breakdown, AI summary, overlap banner and action timeline.

**NARRATION:**

> Opening the case gives a one-page dossier: the AI brief, original complaint, priority breakdown, SLA clock, timestamped action log, and the full case history. The officer can remark, transfer, escalate, dispose, or reopen — and every action is appended to the audit trail.

---

## 2:25–3:05 — The core innovation: overlap room

**ON SCREEN:** Click **Overlap Room** (`/overlaps`). Show the purple banner, tier filters, the graph and a T1 pair. Click **Confirm**.

**NARRATION:**

> This is the heart of the problem statement. The system has already matched the new PGRC complaint with an existing RB case on the same institution — T1 overlap, with the confidence score and evidence: institution match, text similarity, category, and timing. The officer confirms the link, and both bureaus are notified before they issue conflicting notices. No shared spreadsheet. No phone call. Coordination happens on ingest.

**ON SCREEN:** Point at the T1/T2/T3 counts and the graph between bureau nodes.

---

## 3:05–3:35 — Institution 360 and web intelligence

**ON SCREEN:** From the case dossier, click the institution link → `/institutions/{id}`. Show the Risk Index, tabs and cited findings.

**NARRATION:**

> Every institution has a 360-degree profile: complaint history, an explainable risk index, and agentic web intelligence. The agent searches public news and prior reports, rejects same-name colleges in other states, and returns cited findings with source URL, date, topic, and sentiment. This is context — not evidence — and the disclaimer says so. The officer can dismiss any bad match, and that feedback is logged.

---

## 3:35–4:10 — Roles and reports

**ON SCREEN:** Use the role switcher to **Senior Management** or **Chairman AICTE**. Show dashboard widgets unlock, then open **Reports & Analytics** (`/reports`).

**NARRATION:**

> Access is role-based. As senior management, organisation-wide widgets and reports unlock: bureau workload, high-risk institutions, pendency and ageing, duplicates, disposal performance, and monthly trends. Every report exports to CSV or PDF. The same click as an officer returns a restricted view — cross-bureau summaries are redacted automatically.

---

## 4:10–4:30 — Proof and close

**ON SCREEN:** Cut to the evaluation numbers (README) or the overlap page banner. End on the tagline.

**NARRATION:**

> And this is measurable, not aspirational. On our labelled benchmark: institution matching F1 0.996, triage macro-F1 0.837, safety recall 1.0, overlap T1 and T2 F1 1.0. Deterministic scores, cited intelligence, human decisions, full audit. AI recommends. AICTE decides.

**ON SCREEN:** End card — **Complaint-Tantra — One window. Every complaint. Across every bureau.**

---

## Recording notes

- **Do not claim UI that isn't there.** There is no CSV-upload screen in the web app; the public complaint form is the live-ingest demo. CSV/Excel and REST ingestion exist through the API — mention it only if you show `/docs`.
- **Institution 360:** open it from a case dossier, not the sidebar. `/institutions/inst-001` is a placeholder and may 404.
- **Fallbacks:** if the LLM or network is slow, the pipeline degrades to rules and still completes — say "it degrades gracefully" instead of waiting. Keep evaluation numbers on a slide so the close never depends on live data.
- **Shorter cut (60 s):** Problem 10 s → public complaint submit 15 s → queue top card 10 s → T1 overlap confirm 15 s → institution risk/intel 5 s → close 5 s.
