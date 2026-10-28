"""Priority score — formula lives here, never in the LLM (system.md §4.4)."""

from datetime import datetime

CRITICALITY_WEIGHTS = {"C1": 1.00, "C2": 0.75, "C3": 0.50, "C4": 0.25}

# distress/fear/hopelessness count more than frustration (§4.4)
EMOTION_WEIGHTS = {
    "distress": 1.0,
    "fear": 1.0,
    "hopelessness": 0.9,
    "anger": 0.7,
    "frustration": 0.5,
    "neutral": 0.1,
    "hopeful": 0.0,
}

WEIGHTS = {"criticality": 0.35, "emotion": 0.20, "time": 0.25, "risk": 0.10, "overlap": 0.10}


def emotion_weighted(label: str | None, intensity: float | None) -> float:
    if not label or intensity is None:
        return 0.0
    base = EMOTION_WEIGHTS.get(label, 0.1)
    return base * max(0.0, min(1.0, intensity))


def overlap_bonus(links: list[dict]) -> float:
    """1 if any pending T1 link, 0.5 if T2/T3, else 0."""
    tiers = {l.get("tier") for l in links if l.get("decision", "pending") == "pending"}
    if "T1" in tiers:
        return 1.0
    if tiers:
        return 0.5
    return 0.0


def compute_priority(
    *,
    criticality: str | None,
    emotion_label: str | None,
    emotion_intensity: float | None,
    time_pressure: float,
    institution_risk_index: float | None,
    links: list[dict] | None = None,
    safety_flag: bool = False,
) -> tuple[float, dict]:
    """Return (score 0..100, priority_reasons dict per §4.4)."""
    cw = CRITICALITY_WEIGHTS.get(criticality or "", 0.25)
    ew = emotion_weighted(emotion_label, emotion_intensity)
    tp = min(time_pressure, 1.5)
    risk = max(0.0, min(100.0, institution_risk_index or 0.0)) / 100.0
    ob = overlap_bonus(links or [])

    if safety_flag:
        # Bypasses scoring → urgent human review (§4.2)
        score = 100.0
        components = {"criticality": 1.0, "emotion": ew, "time": 1.0, "risk": risk, "overlap": ob}
        reasons = ["SAFETY FLAG: urgent human review required"]
    else:
        raw = (
            WEIGHTS["criticality"] * cw
            + WEIGHTS["emotion"] * ew
            + WEIGHTS["time"] * min(tp, 1.0)
            + WEIGHTS["risk"] * risk
            + WEIGHTS["overlap"] * ob
        )
        score = round(100.0 * max(0.0, min(1.0, raw)), 1)
        components = {
            "criticality": round(WEIGHTS["criticality"] * cw, 3),
            "emotion": round(WEIGHTS["emotion"] * ew, 3),
            "time": round(WEIGHTS["time"] * min(tp, 1.0), 3),
            "risk": round(WEIGHTS["risk"] * risk, 3),
            "overlap": round(WEIGHTS["overlap"] * ob, 3),
        }
        reasons = _reasons(criticality, emotion_label, emotion_intensity, time_pressure, risk, ob)

    return score, {"priority_score": score, "components": components, "reasons": reasons}


def _reasons(cw, elabel, eint, tp, risk, ob) -> list[str]:
    out = []
    if cw in CRITICALITY_WEIGHTS:
        out.append(f"{cw}: base weight {CRITICALITY_WEIGHTS[cw]:.2f}")
    if elabel and eint is not None:
        out.append(f"Emotion: {elabel} ({eint:.1f})")
    if tp > 0:
        out.append(f"Time pressure: {tp:.2f}")
    if risk > 0:
        out.append(f"Institution risk index: {risk * 100:.0f}/100")
    if ob > 0:
        out.append(f"Overlap bonus: {ob:.1f}")
    return out
