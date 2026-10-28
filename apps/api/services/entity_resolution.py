"""Institution resolution (system.md §5). Rules first; embeddings when present."""

import re
from difflib import SequenceMatcher

ABBREV = {
    "engg": "engineering",
    "eng": "engineering",
    "tech": "technology",
    "inst": "institute",
    "coll": "college",
    "univ": "university",
    "poly": "polytechnic",
    "dipl": "diploma",
}


def normalize_name(name: str) -> str:
    s = (name or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    tokens = [ABBREV.get(t, t) for t in s.split()]
    return " ".join(tokens)


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def token_set_ratio(a: str, b: str) -> float:
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    inter = " ".join(sorted(ta & tb))
    union = " ".join(sorted(ta | tb))
    return max(
        _ratio(inter, " ".join(sorted(ta))),
        _ratio(inter, " ".join(sorted(tb))),
        _ratio(inter, union),
    ) * 100


def match_score(
    cand: dict,
    *,
    name: str,
    address: str | None = None,
    city: str | None = None,
    state: str | None = None,
) -> float:
    """0.5*token_set(name) + 0.3*address + 0.2*(state/city) — §5.

    Weights renormalize over the components actually provided, so a name-only
    comparison can still reach the 0.90 auto-link threshold.
    """
    ns = token_set_ratio(normalize_name(name), cand.get("name_normalized", "")) / 100.0
    parts: list[tuple[float, float]] = [(0.5, ns)]
    if address:
        parts.append((0.3, _ratio(address.lower(), (cand.get("address") or "").lower())))
    if state or city:
        hits = 0
        total = 0
        if state:
            total += 1
            hits += int((cand.get("state") or "").lower() == state.lower())
        if city:
            total += 1
            hits += int((cand.get("city") or "").lower() == city.lower())
        parts.append((0.2, hits / total if total else 0.0))
    weight_sum = sum(w for w, _ in parts)
    return sum(w * v for w, v in parts) / weight_sum


def verdict(score: float) -> str:
    if score >= 0.90:
        return "auto"       # auto-link
    if score >= 0.70:
        return "confirm"    # needs confirmation (shown to officer)
    return "new"            # new/unmatched institution


def category_relatedness(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return 0.4  # rough relatedness without the full lookup matrix


def time_overlap(received_a, received_b, window_days: int = 90) -> float:
    if received_a is None or received_b is None:
        return 0.0
    delta = abs((received_a - received_b).total_seconds()) / 86400
    if delta <= window_days:
        return 1.0 - (delta / window_days) * 0.5
    return 0.0
