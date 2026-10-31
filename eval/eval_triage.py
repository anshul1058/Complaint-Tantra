#!/usr/bin/env python3
"""Rule-based triage evaluation on a small hand-checked labelled set.

Targets (system.md §11): criticality macro-F1 >= 0.80, safety recall >= 0.95.
The LLM path is not required; this is the offline floor that must hold.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from agents import _rule_intake, _rule_triage  # noqa: E402

# (text, expected criticality, safety expected)
CASES = [
    ("A student was assaulted and ragged inside the hostel; seniors threatened physical harm.", "C1", True),
    ("The college is running a fake unapproved B.Tech course without AICTE approval.", "C1", False),
    ("I want to kill myself, the harassment from faculty is unbearable.", "C1", True),
    ("The institute forged affiliation documents and charged capitation fee.", "C1", False),
    ("My fee refund has been denied for six months despite cancellation.", "C2", False),
    ("Capitation fee was demanded in cash during admission.", "C2", False),
    ("Scholarship amount was misused by the administration.", "C2", False),
    ("There are only two faculty members for the entire mechanical department.", "C3", False),
    ("Exam results have been withheld and revaluation requests are ignored.", "C3", False),
    ("The placement cell promised jobs but no company visited the campus.", "C3", False),
    ("Laboratory equipment is broken and the hostel building is unsafe.", "C3", False),
    ("My degree certificate has not been issued for eight months.", "C4", False),
    ("The transcript application is delayed with no response from the office.", "C4", False),
]


def main() -> int:
    labels = ["C1", "C2", "C3", "C4"]
    confusion = {a: {b: 0 for b in labels} for a in labels}
    safety_tp = safety_fn = 0

    for text, expected, expected_safety in CASES:
        case = {"text_original": text, "raw_institution": None}
        intake = _rule_intake(case)
        triage = _rule_triage(case, intake)
        got = triage["criticality"]
        confusion[expected][got] += 1
        if expected_safety:
            if triage["safety_flag"]:
                safety_tp += 1
            else:
                safety_fn += 1

    f1s = []
    correct = 0
    total = 0
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in labels if other != label)
        fn = sum(confusion[label][other] for other in labels if other != label)
        correct += tp
        total += sum(confusion[label].values())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if sum(confusion[label].values()):
            f1s.append(f1)

    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    accuracy = correct / total if total else 0.0
    safety_recall = safety_tp / (safety_tp + safety_fn) if safety_tp + safety_fn else 1.0

    print(f"triage: accuracy={accuracy:.3f} macro-F1={macro_f1:.3f} "
          f"safety-recall={safety_recall:.3f} (n={total})")
    ok = macro_f1 >= 0.80 and safety_recall >= 0.95
    print("PASS" if ok else "FAIL (targets: macro-F1 >= 0.80, safety recall >= 0.95)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
