from agents.llm import complete_json


BRIEF_PROMPT = """You are the Briefing Agent. Write a concise case brief for an officer.
Use ONLY the facts provided (SQL numbers passed in). Do not invent statistics.
Return JSON: {"case_brief": "...", "suggested_next_action": "...", "key_points": []}
"""


def write_brief(case: dict, ctx: dict) -> dict:
    try:
        full = BRIEF_PROMPT + "\n\nCASE:\n" + str(case) + "\n\nCTX:\n" + str(ctx) + "\n"
        out, meta = complete_json(full, None)
        out["model"] = meta.get("model")
        out["prompt_version"] = meta.get("prompt_version")
        out["source"] = "llm"
        return out
    except Exception:
        return {
            "case_brief": case.get("ai_summary") or "",
            "suggested_next_action": "Review and take appropriate action",
            "key_points": [],
            "source": "rules",
        }
