# COMPLAINT-TANTRA — Future Scope

> From AICTE pilot to every regulator — phased, funded by each phase's own savings.

---

## 1. Phase 2 (3–6 months post-pilot)

| Item | What it adds |
|---|---|
| Briefing agent digests | Daily "Top 10 needing attention" + monthly reports, fully automated |
| Region heatmap | Regional Office workload view on the command dashboard |
| Institution Risk Index trend | Time-series chart of repeat offenders |
| Multilingual UI | Hindi + regional labels (complaint text already translated by Intake Agent) |
| Channel alerts | Email / SMS / WhatsApp for overlap, due-soon, overdue, safety |
| Saved views | Officers save filter presets per bureau/category |
| Coordination Room polish | Graph view of cross-Bureau case links, drag-to-link |

**Funding:** covered by the AMC contract — no new procurement needed.

---

## 2. Phase 3 (6–18 months)

| Item | What it adds |
|---|---|
| **Direct read-only connectors** | Live pull from RB / PGRC / other Bureau systems — CSV upload becomes optional |
| **On-prem LLM hardening** | Dedicated GPU box or vLLM cluster; open model fine-tuned on AICTE complaint taxonomy |
| **Continuous learning** | Officer confirm/reject decisions auto-tune overlap thresholds (feedback loop closed) |
| **Predictive SLA analytics** | Model flags which open cases will breach, before they breach |
| AICTE portal integration | Complaints filed on the public portal land directly in the queue |
| State regulator bridge | Share institution intelligence with state technical universities |
| Mobile app | Field regional officers: view assigned cases, add remarks, scan attachments |

**Funding:** add-on module fees + expanded annual license (volume tier likely moves up).

---

## 3. Beyond AICTE (18–36 months)

| Direction | What it is | Revenue |
|---|---|---|
| Multi-regulator platform | Same engine licensed to UGC, NMC, NCTE, state universities | Per-org license |
| Ombudsman / grievance boards | Re-skin for banking (RBI), insurance (IRDAI), telecom (TRAI) | Per-org license + connectors |
| Institution 360 as a service | Accreditation agencies (NAAC) buy the risk-intelligence layer alone | API/module license |
| Predictive policy reports | Anonymized aggregate trend reports for ministry decision-making | New report line |
| International | Developing-country education regulators with the same fragmented-complaint problem | Export licensing |

The overlap engine, triage scorer and Institution 360 are domain-light — each new buyer only needs taxonomy + ingestion connector work, not a rebuild.

---

## 4. Deliberately NOT doing

Keeps scope and cost low; these are conscious exclusions, not gaps:

- **Public complaint-filing portal** — the regulator's own channels stay the entry point; we integrate, don't replace.
- **Auto-disposal of cases** — human decides (also a legal/gov requirement).
- **Proprietary in-house LLM** — open models + fine-tune beat it on cost and control.
- **Multi-tenant SaaS on foreign cloud** — gov data residency makes this non-viable anyway; on-prem is both compliant and cheaper.
