#!/usr/bin/env python3
"""Institution-matching evaluation against the real AICTE institution master.

Builds noisy name variants (abbreviations, punctuation, word order, typos) and
checks whether entity resolution auto-links them back to the right institution.

Target (system.md §11): precision >= 0.95, recall >= 0.90 at the 0.90 threshold.
"""
import csv
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from services.entity_resolution import match_score, normalize_name, verdict  # noqa: E402

DATA = ROOT / "data" / "institutions.csv"
SAMPLE = 120
POOL = 300
SEED = 42

ABBREV = {
    "engineering": "engg",
    "college": "coll",
    "institute": "inst",
    "technology": "tech",
    "university": "univ",
    "polytechnic": "poly",
}


def load_rows() -> list[dict]:
    with DATA.open(newline="", encoding="utf-8") as fh:
        rows = [
            r for r in csv.DictReader(fh)
            if (r.get("institution_name") or "").strip()
        ]
    return rows


def noise(name: str, rng: random.Random) -> str:
    text = name.lower()
    mode = rng.randrange(5)
    if mode == 0:
        text = re.sub(r"[^\w\s]", " ", text)
    elif mode == 1:
        for full, short in ABBREV.items():
            text = re.sub(rf"\b{full}\b", short, text)
    elif mode == 2:
        words = text.split()
        if len(words) > 1:
            words[0], words[1] = words[1], words[0]
        text = " ".join(words)
    elif mode == 3:
        words = text.split()
        if words:
            i = rng.randrange(len(words))
            word = words[i]
            if len(word) > 4:
                cut = rng.randrange(1, len(word) - 1)
                words[i] = word[:cut] + word[cut + 1:]
        text = " ".join(words)
    else:
        text = re.sub(r"\b(of|the|and)\b", "", text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    rng = random.Random(SEED)
    rows = load_rows()
    if not rows:
        print(f"dataset missing: {DATA}")
        return 1

    pool = rng.sample(rows, min(POOL, len(rows)))
    queries = rng.sample(pool, min(SAMPLE, len(pool)))

    tp = fp = fn = 0
    misses = []
    for truth in queries:
        target = truth["permanent_id"]
        query = noise(truth["institution_name"], rng)
        best_id, best_score = None, 0.0
        for cand in pool:
            score = match_score(
                {
                    "name_normalized": normalize_name(cand["institution_name"]),
                    "address": cand.get("address_line1"),
                    "city": cand.get("city"),
                    "state": cand.get("state"),
                },
                name=query,
                city=truth.get("city") or None,
                state=truth.get("state") or None,
            )
            if score > best_score:
                best_id, best_score = cand["permanent_id"], score

        if verdict(best_score) != "auto":
            fn += 1
            misses.append((query, truth["institution_name"], round(best_score, 3)))
            continue
        if best_id == target:
            tp += 1
        else:
            fp += 1
            misses.append((query, truth["institution_name"], round(best_score, 3)))

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    print(f"institution matching: P={precision:.3f} R={recall:.3f} F1={f1:.3f} "
          f"(n={len(queries)}, auto-linked={tp + fp})")
    if misses[:5]:
        print("sample misses:")
        for q, t, s in misses[:5]:
            print(f"  {q!r} -> {t!r} (best={s})")

    ok = precision >= 0.95 and recall >= 0.90
    print("PASS" if ok else "FAIL (targets: P >= 0.95, R >= 0.90)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
