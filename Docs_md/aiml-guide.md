# AI/ML Guide — Complaint-Tantra

Owner: AI/ML member. Stack: **LangGraph + LiteLLM + pgvector + rapidfuzz + sentence embeddings**.
Read first: `system.md` §4 (scoring), §5 (overlap), §6 (agent contracts + prompts), §10 (synthetic data), §11 (eval targets).

## Your scope

`apps/api/agents/`, `apps/api/prompts/`, `data/synthetic/`, `eval/`.
You expose **pure Python functions with strict Pydantic JSON output** — the backend member wraps them into API endpoints. You do not write routes or UI.

## Build order

1. **LLM wrapper** (do this first — everything depends on it):

```python
# agents/llm.py
# Provider-agnostic via LiteLLM. One env var swaps models:
# LLM_PROVIDER=openai-free | ollama | anthropic | gemini
# Demo on laptop: Ollama (llama3.2:3b or qwen2.5:3b) or a free API tier.
```

2. **Synthetic dataset** (`data/synthetic/`) — before any agent: ~800 messy Indian institution names (abbreviations, typos, missing Permanent ID 25%), ~5000 multilingual complaints (English/Hindi/Marathi samples), planted overlaps (300 T1, 300 T2, 150 T3), 500 hand-checked emotion/criticality labels. Use Faker. This is your training AND eval currency — backend uses it to seed, frontend never sees it as fake product data.

3. **Intake agent** — prompt v1 in `system.md` §6.2, stored in `prompts/v1/intake.md`. Output: translate, categorize (taxonomy you define with backend in `sla_config`), extract entities, neutral summary. Never guess — null allowed. Run every output through Pydantic; fail → retry once → rules fallback → `needs_review=True`.

4. **Triage agent** — prompt `system.md` §6.3. Criticality C1–C4, emotion + intensity, `safety_flag`. Safety flag short-circuits everything → urgent human review. You return components; **the numeric priority score is computed in backend code** (formula `system.md` §4.4) — do not ask the LLM for the score.

5. **Embeddings + institution resolution** — bge-m3 or multilingual-e5 (Hindi+English) into `VECTOR(1024)` columns. Institution match: rapidfuzz token-set + address + state per `system.md` §5 thresholds (≥0.90 auto, 0.70–0.90 officer confirm, <0.70 new).

6. **Overlap detection** — hybrid score (institution 0.40, text cosine 0.30, category relatedness 0.15, time 0.15). Gray zone 0.45–0.70 → LLM judge (`system.md` §6.4). Return tiers T1/T2/T3 with evidence JSON.

7. **Web intelligence agent** — prompt `system.md` §6.5. Search via Tavily/Brave free tier, fallback Google News RSS + GDELT (free). trafilatura for text. Guardrails hard: max 12 fetches, 24h cache, every finding needs URL + date, `match_confidence < 0.6` hidden. For demo, ship cached mock news fixtures for known institutions so the stage never depends on live search.

8. **Briefing agent** — case brief, institution dossier, daily digest. Report numbers come from SQL (backend passes them in); LLM writes narrative only.

## Contracts with backend member (freeze early)

```python
# Each agent: def run(case: dict, ctx: dict) -> <PydanticModel>
# All models in agents/schemas.py, strict, extra="forbid".
# State machine + priority formula stay backend-side.
# agent_runs logging: you return {model, prompt_version, tokens, latency} alongside output.
```

## Evaluation (your demo slide)

Scripts in `eval/`, run against the labelled synthetic set:

| What | Target |
|---|---|
| Institution matching | P ≥ 0.95, R ≥ 0.90 |
| Overlap T1 F1 | ≥ 0.85 |
| Criticality macro-F1 | ≥ 0.80 |
| Safety flag recall | ≥ 0.95 |
| Ingest → scored latency | < 15 s |

## Demo-mode rules

- Ollama runs on a laptop during the demo; `LLM_PROVIDER` env swaps in seconds — the story is "provider-agnostic", prove it.
- PII masking before any text leaves to an external API (`architecture.md` §232).
- Every prompt is a versioned file — `/agents/replay/{case_id}` must reproduce output. Never inline prompt strings in code.
- Offline path: if LLM is down mid-demo, agents degrade to rules + `needs_review`, backend still works.

## Definition of done

- Seeded 5000-case dataset loads; ingest of one raw multilingual complaint returns full scored JSON < 15 s.
- Eval numbers printed by `eval/` script match the targets above (or gaps are documented).
- Swap `LLM_PROVIDER` ollama ↔ free API with zero code changes.
