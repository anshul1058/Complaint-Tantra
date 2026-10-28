# Frontend Guide — Complaint-Tantra

Owner: frontend member. Stack: **Next.js (App Router) + TypeScript + Tailwind + shadcn/ui**.
Read first: `prd.md` (roles, screens), `system.md` §7 (API), §8 (RBAC).

## Golden rule — no hardcoded business data

**Nothing about complaints, institutions, or analytics is written into components.**

- No hardcoded categories, statuses, criticality codes, or SLA days → fetch from API (add `GET /meta/options` on backend if a list endpoint is missing; ask, don't invent).
- No hardcoded KPI numbers, chart data, case text, institution names, or officer names — all from API responses.
- No mock JSON committed into components "temporarily". For local development before the API is ready, use a typed mock layer in `lib/mock/` that mirrors API response types and is deleted before demo.
- Static chrome is fine: nav labels, button text, page titles, empty-state copy.

This matters because the demo shows live AI-scored data; one hardcoded fake chart discredits the whole product.

## Your scope

Everything under `apps/web/`. You consume the backend's `/openapi.json` — generate TS types from it (`openapi-typescript`), never hand-copy field names.

## Pages (map to roles in prd.md)

| Route | Who | Contents |
|---|---|---|
| `/login` | all | JWT login |
| `/` (dashboard) | all, scoped | KPI cards, bureau workload, region heatmap (Leaflet + India GeoJSON), SLA alert strip |
| `/queue` | officer+ | priority-ranked cases (`GET /queue/priority`), sort by score |
| `/cases` | officer+ | search + filters (institution, status, category, date range) |
| `/cases/[id]` | officer+ | detail: original + English text, AI summary, priority breakdown (why #1), timeline, overlaps, actions (remark/transfer/escalate/dispose/reopen) |
| `/overlaps` | officer+ | T1/T2/T3 list, evidence side-by-side, confirm/reject buttons |
| `/institutions/[id]` | officer+ | profile, risk index, complaint history, web findings timeline |
| `/reports` | senior+ | institution/bureau/region/ageing/disposal — tables + charts + export |

## Key components

- **PriorityBreakdown** — renders `priority_reasons` JSON from the API as component bars + reason list (score formula lives in backend; display only).
- **OverlapGraph** — React Flow graph of linked cases, data from `GET /cases/{id}/overlaps`.
- **StateBadge / StatusTimeline** — drive transitions from API-valid-next-states, don't compute transitions in UI.
- **Charts**: Recharts for trends/workload. Numbers always from API, never computed in the client.
- **RBAC in UI**: hide actions the role can't do (based on JWT role claim), but the backend is the enforcement — UI hiding is cosmetic.

## Data layer

- `lib/api/` — one fetch wrapper: attaches JWT, handles 401 → login, typed via generated OpenAPI types.
- Poll `/dashboard/summary` every 30s for demo (WebSocket `/ws/events` is stretch goal — skip unless time remains).
- After any action (transfer, dispose, confirm-overlap): refetch the affected query. No optimistic state machines.

## Free deploy

Vercel free. Env: `NEXT_PUBLIC_API_URL`. Nothing else ships to the client — no service keys.

## Definition of done

- Zero hardcoded business strings in components (`grep` categories/names/numbers before demo).
- Login as 2 different roles → screens visibly differ per RBAC.
- Full demo path works: login → queue → open case → see AI brief → dispose → timeline updates.
