import json
import os
import time
from typing import Any

from pydantic import BaseModel


def get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "ollama").lower()


class LLMConfig:
    def __init__(self) -> None:
        self.provider = get_provider()
        self.model = os.getenv("LLM_MODEL") or self._default_model()
        self.base_url = os.getenv("LLM_BASE_URL")
        self.api_key = os.getenv("LLM_API_KEY")
        self.timeout = int(os.getenv("LLM_TIMEOUT_MS", "30000")) / 1000.0
        # Ollama needs an explicit api_base for LiteLLM
        if self.provider == "ollama" and not self.base_url:
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def _default_model(self) -> str:
        if self.provider == "ollama":
            return os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        if self.provider == "openai-free":
            return os.getenv("OPENAI_FREE_MODEL", "gpt-4o-mini")
        if self.provider == "gemini":
            return os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        if self.provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        return os.getenv("LLM_DEFAULT_MODEL", "llama3.2:3b")


CONFIG = LLMConfig()


def _build_litellm_kwargs(prompt: str, schema: type[BaseModel] | None = None) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": CONFIG.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "timeout": CONFIG.timeout,
    }
    if CONFIG.api_key:
        kwargs["api_key"] = CONFIG.api_key
    if CONFIG.base_url:
        kwargs["api_base"] = CONFIG.base_url
    return kwargs


def complete_json(prompt: str, schema: type[BaseModel] | None = None, model: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    t0 = time.time()
    try:
        import litellm  # type: ignore

        kwargs = _build_litellm_kwargs(prompt, schema)
        if model:
            kwargs["model"] = model
        resp = litellm.completion(**kwargs)
        content = resp.choices[0].message.content or "{}"
    except Exception:
        # Offline/fallback path per aiml-guide
        raise

    try:
        data = json.loads(content)
    except Exception:
        # Try to extract JSON block
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(content[start : end + 1])
        else:
            raise

    if schema is not None:
        parsed = schema.model_validate(data)
        data = parsed.model_dump()

    meta = {
        "model": kwargs.get("model") or CONFIG.model,
        "prompt_version": os.getenv("PROMPT_VERSION", "v1"),
        "tokens_in": getattr(getattr(resp, "usage", None), "prompt_tokens", None),
        "tokens_out": getattr(getattr(resp, "usage", None), "completion_tokens", None),
        "latency_ms": int((time.time() - t0) * 1000),
    }
    return data, meta
