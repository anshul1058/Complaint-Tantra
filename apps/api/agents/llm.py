import atexit
import json
import os
import time
from contextlib import nullcontext
from typing import Any

from pydantic import BaseModel

from services.pii import mask_pii


def get_provider() -> str:
    return os.getenv("LLM_PROVIDER", "none").lower()


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

_trace_client = None
_trace_failed = False


def _langfuse_client():
    """Optional Langfuse client; disabled unless both keys are configured."""
    global _trace_client, _trace_failed
    if _trace_client is not None or _trace_failed:
        return _trace_client
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        return None
    try:
        from langfuse import Langfuse

        _trace_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com",
        )
        atexit.register(_trace_client.flush)
    except Exception:
        _trace_failed = True
        _trace_client = None
    return _trace_client


def _trace(prompt: str, model: str):
    client = _langfuse_client()
    if client is None:
        return nullcontext(None)
    kwargs = {
        "name": "llm.complete_json",
        "as_type": "generation",
        "input": prompt,
        "model": model,
        "metadata": {"provider": CONFIG.provider},
    }
    if hasattr(client, "start_as_current_observation"):
        return client.start_as_current_observation(**kwargs)
    legacy = {k: v for k, v in kwargs.items() if k not in ("as_type", "model")}
    return client.start_as_current_span(**legacy)


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
    if CONFIG.provider == "none":
        raise RuntimeError("LLM_PROVIDER=none")
    prompt = mask_pii(prompt)
    try:
        import litellm  # type: ignore
    except Exception:
        raise

    kwargs = _build_litellm_kwargs(prompt, schema)
    if model:
        kwargs["model"] = model
    with _trace(prompt, str(kwargs.get("model") or CONFIG.model)) as span:
        resp = None
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                resp = litellm.completion(**kwargs)
                break
            except Exception as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.5)
        if resp is None:
            raise last_error or RuntimeError("LLM call failed")

        content = resp.choices[0].message.content or "{}"
        try:
            data = json.loads(content)
        except Exception:
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
        if span is not None:
            try:
                span.update(
                    output=data,
                    metadata=meta,
                    usage_details={
                        "input": meta["tokens_in"] or 0,
                        "output": meta["tokens_out"] or 0,
                    },
                )
            except Exception:
                pass
        return data, meta
