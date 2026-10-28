"""Overlap detection pipeline (system.md §5) — deterministic scoring, no LLM required."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Case, CaseLink, Institution
from services.entity_resolution import category_relatedness, time_overlap

GRAY_ZONE = (0.45, 0.70)
WEIGHTS = {"inst": 0.40, "text": 0.30, "cat": 0.15, "time": 0.15}


def _cosine(a, b) -> float:
    if a is None or b is None:
        return 0.0
    try:
        import numpy as np

        va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        return float(np.dot(va, vb) / denom) if denom else 0.0
    except Exception:
        return 0.0


def assign_tier(score: float, text_sim: float, cat_rel: float, same_bureau: bool) -> str | None:
    if score >= 0.75 and cat_rel >= 0.9:
        return "T1"
    if score >= 0.55:
        return "T2"
    if score >= GRAY_ZONE[0]:
        return "T3"
    return None


async def detect_overlaps(db: AsyncSession, case: Case) -> list[CaseLink]:
    """Score every open case at the same institution; persist T1–T3 links."""
    if case.institution_id is None:
        return []
    result = await db.execute(
        select(Case).where(
            Case.institution_id == case.institution_id,
            Case.id != case.id,
            Case.status.notin_(("Disposed",)),
        )
    )
    candidates = result.scalars().all()
    if not candidates:
        return []

    inst = await db.get(Institution, case.institution_id)
    links: list[CaseLink] = []
    for cand in candidates:
        text_sim = _cosine(case.text_embedding, cand.text_embedding)
        if text_sim == 0.0 and case.text_english and cand.text_english:
            # fallback when embeddings absent: cheap token overlap
            ta = set(case.text_english.lower().split())
            tb = set(cand.text_english.lower().split())
            text_sim = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
        cat_rel = category_relatedness(case.category, cand.category)
        t_ovl = time_overlap(case.received_at, cand.received_at)
        inst_match = 1.0 if inst else 0.5  # institution already resolved to link them
        score = (
            WEIGHTS["inst"] * inst_match
            + WEIGHTS["text"] * text_sim
            + WEIGHTS["cat"] * cat_rel
            + WEIGHTS["time"] * t_ovl
        )

        # Gray zone → LLM judge (system.md §5, §6.4): blend score with judge confidence
        if GRAY_ZONE[0] <= score < GRAY_ZONE[1]:
            try:
                from agents.overlap import judge_overlap

                verdict = judge_overlap(
                    {
                        "text_english": case.text_english,
                        "raw_institution": case.raw_institution,
                        "category": case.category,
                    },
                    {
                        "text_english": cand.text_english,
                        "raw_institution": cand.raw_institution,
                        "category": cand.category,
                    },
                )
                conf = float(verdict.get("confidence") or 0.0)
                if verdict.get("related") in ("same_issue", "duplicate"):
                    score = 0.5 * score + 0.5 * max(score, conf)
                elif verdict.get("related") == "different_issue":
                    score = 0.5 * score
            except Exception:
                pass  # offline path: keep deterministic score
        same_bureau = cand.assigned_bureau == case.assigned_bureau
        tier = assign_tier(score, text_sim, cat_rel, same_bureau)
        if tier is None:
            continue

        a, b = sorted([str(case.id), str(cand.id)])
        existing = await db.execute(
            select(CaseLink).where(
                CaseLink.case_a == uuid.UUID(a),
                CaseLink.case_b == uuid.UUID(b),
            )
        )
        if existing.first():
            continue

        link = CaseLink(
            case_a=uuid.UUID(a),
            case_b=uuid.UUID(b),
            tier=tier,
            confidence=round(score, 3),
            evidence={
                "id_match": str(case.institution_id) == str(cand.institution_id),
                "name_score": inst_match,
                "text_sim": round(text_sim, 3),
                "cat_rel": cat_rel,
                "time_ovl": round(t_ovl, 3),
                "reasoning": (
                    f"score={score:.2f} text={text_sim:.2f} "
                    f"cat={cat_rel:.2f} time={t_ovl:.2f}"
                ),
                "same_bureau": same_bureau,
                "in_gray_zone": GRAY_ZONE[0] <= score < GRAY_ZONE[1],
            },
            detected_by="agent",
        )
        db.add(link)
        links.append(link)
    await db.commit()
    for l in links:
        await db.refresh(l)
    return links
