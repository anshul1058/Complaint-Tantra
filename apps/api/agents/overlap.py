from agents.llm import complete_json
from agents.schemas import OverlapJudge


OVERLAP_JUDGE_PROMPT = """You compare two complaints about possibly the same institution. Return JSON only:
{ "same_institution": bool, "same_issue": bool, "related": "same_issue|related_issue|different_issue|duplicate",
  "confidence": 0..1, "reason": "<=40 words citing specific details" }
Base your answer only on the two texts and institution fields. If unsure, lower the confidence.
"""


def judge_overlap(new_case: dict, other_case: dict) -> dict:
    full = OVERLAP_JUDGE_PROMPT + "\n\nCASE_A:\n" + str(new_case) + "\n\nCASE_B:\n" + str(other_case) + "\n"
    out, meta = complete_json(full, OverlapJudge)
    out["model"] = meta.get("model")
    out["prompt_version"] = meta.get("prompt_version")
    return out
