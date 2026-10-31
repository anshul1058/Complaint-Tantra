#!/usr/bin/env python3
"""Overlap-tier evaluation using the pure §5 scoring path.

Labels: T1 = same institution + same issue, T2 = same institution + related
issue, NONE = different institution. Target: T1 F1 >= 0.85 (system.md §11).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from services.entity_resolution import category_relatedness  # noqa: E402
from services.overlap import assign_tier, score_pair  # noqa: E402

SAME_BUREAU = True


def text_sim(a: str, b: str) -> float:
    ta, tb = set(a.lower().split()), set(b.lower().split())
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0


# (case_a_text, a_category, case_b_text, b_category, same_institution, expected_tier)
PAIRS = [
    ("my fee refund was denied by the college", "fees",
     "the college refused my fee refund request", "fees", True, "T1"),
    ("fake unapproved course running without AICTE approval", "fraud",
     "college runs unapproved course and forged approval", "fraud", True, "T1"),
    ("hostel ragging and threat to students by seniors", "safety",
     "seniors are ragging students in the hostel", "safety", True, "T1"),
    ("faculty shortage in the mechanical department", "faculty",
     "there is a faculty shortage for students in the department", "faculty", True, "T1"),
    ("my fee refund was denied by the college", "fees",
     "faculty shortage in the mechanical department", "faculty", True, "T2"),
    ("exam results are withheld without reason", "examination",
     "placement cell did not bring any company", "placement", True, "T2"),
    ("library and lab equipment are broken", "infrastructure",
     "certificate not issued by the office", "certificate", True, "T2"),
    ("my fee refund was denied by the college", "fees",
     "hostel ragging and threat to students", "safety", False, None),
    ("fake affiliation documents were submitted", "fraud",
     "placement package was not as promised", "placement", False, None),
    ("certificate issue is delayed", "certificate",
     "faculty shortage in the department", "faculty", False, None),
] * 5


def main() -> int:
    expected_counts = {"T1": 0, "T2": 0, None: 0}
    predicted_counts = {"T1": 0, "T2": 0, None: 0}
    tp = {"T1": 0, "T2": 0}

    for a_text, a_cat, b_text, b_cat, same_inst, expected in PAIRS:
        sim = text_sim(a_text, b_text)
        cat = category_relatedness(a_cat, b_cat)
        score = score_pair(1.0 if same_inst else 0.0, sim, cat, 1.0)
        predicted = assign_tier(score, sim, cat, SAME_BUREAU)
        expected_counts[expected] += 1
        predicted_counts[predicted] += 1
        if predicted == expected and expected in tp:
            tp[expected] += 1

    for tier in ("T1", "T2"):
        p = tp[tier] / predicted_counts[tier] if predicted_counts[tier] else 0.0
        r = tp[tier] / expected_counts[tier] if expected_counts[tier] else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        print(f"{tier}: P={p:.3f} R={r:.3f} F1={f1:.3f}")

    t1_p = tp["T1"] / predicted_counts["T1"] if predicted_counts["T1"] else 0.0
    t1_r = tp["T1"] / expected_counts["T1"] if expected_counts["T1"] else 0.0
    t1_f1 = 2 * t1_p * t1_r / (t1_p + t1_r) if t1_p + t1_r else 0.0
    ok = t1_f1 >= 0.85
    print("PASS" if ok else "FAIL (target: T1 F1 >= 0.85)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
