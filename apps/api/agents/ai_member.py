import json
import os
from pathlib import Path

from agents.llm import complete_json
from agents.schemas import IntakeOutput, TriageOutput


PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str, version: str = "v1") -> str:
    path = PROMPTS_DIR / version / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    # Fallback to apps/api/prompts as well
    alt = Path(__file__).parent.parent / "prompts" / version / f"{name}.md"
    if alt.exists():
        return alt.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt not found: {path}")


def run_intake(case: dict) -> dict:
    prompt = _load_prompt("intake", os.getenv("PROMPT_VERSION", "v1"))
    # Minimal context injection
    ctx = json.dumps(case, ensure_ascii=False)
    full = f"{prompt}\n\nCOMPLAINT:\n{ctx}\n"
    out, meta = complete_json(full, IntakeOutput)
    out["model"] = meta.get("model")
    out["prompt_version"] = meta.get("prompt_version")
    out["tokens_in"] = meta.get("tokens_in")
    out["tokens_out"] = meta.get("tokens_out")
    out["latency_ms"] = meta.get("latency_ms")
    return out


def run_triage(case: dict, intake: dict | None = None) -> dict:
    prompt = _load_prompt("triage", os.getenv("PROMPT_VERSION", "v1"))
    ctx = {"case": case, "intake": intake}
    full = f"{prompt}\n\nINPUT:\n{json.dumps(ctx, ensure_ascii=False)}\n"
    out, meta = complete_json(full, TriageOutput)
    out["model"] = meta.get("model")
    out["prompt_version"] = meta.get("prompt_version")
    out["tokens_in"] = meta.get("tokens_in")
    out["tokens_out"] = meta.get("tokens_out")
    out["latency_ms"] = meta.get("latency_ms")
    return out
