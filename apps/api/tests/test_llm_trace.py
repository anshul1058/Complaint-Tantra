import langfuse

from agents import llm


def test_langfuse_disabled_without_keys(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.setattr(llm, "_trace_client", None)
    monkeypatch.setattr(llm, "_trace_failed", False)
    assert llm._langfuse_client() is None
    assert llm._trace("prompt", "model").__class__.__name__ == "nullcontext"


def test_langfuse_configured_client(monkeypatch):
    class FakeLangfuse:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def flush(self):
            pass

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr(langfuse, "Langfuse", FakeLangfuse)
    monkeypatch.setattr(llm, "_trace_client", None)
    monkeypatch.setattr(llm, "_trace_failed", False)
    assert isinstance(llm._langfuse_client(), FakeLangfuse)


def test_complete_json_updates_langfuse_span(monkeypatch):
    import litellm

    class Span:
        def __init__(self):
            self.updated = None

        def update(self, **kwargs):
            self.updated = kwargs

    class Context:
        def __init__(self, span):
            self.span = span

        def __enter__(self):
            return self.span

        def __exit__(self, *exc):
            return False

    class FakeClient:
        def __init__(self):
            self.span = Span()

        def start_as_current_observation(self, **kwargs):
            return Context(self.span)

    class Response:
        class Choice:
            class Message:
                content = '{"ok": true}'

            message = Message()

        choices = [Choice()]
        usage = type("Usage", (), {"prompt_tokens": 3, "completion_tokens": 2})()

    monkeypatch.setattr(llm, "_trace_client", FakeClient())
    monkeypatch.setattr(llm, "_trace_failed", False)
    monkeypatch.setattr(llm.CONFIG, "provider", "openai")
    monkeypatch.setattr(litellm, "completion", lambda **kwargs: Response())

    data, meta = llm.complete_json("hello")
    assert data == {"ok": True}
    assert meta["tokens_in"] == 3
    assert llm._trace_client.span.updated["output"] == {"ok": True}
