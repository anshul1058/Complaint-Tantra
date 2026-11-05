from agents import llm


def test_model_prefix_follows_provider(monkeypatch):
    monkeypatch.setattr(llm.CONFIG, "provider", "ollama")
    assert llm._qualified_model("llama3.2:3b") == "ollama/llama3.2:3b"
    monkeypatch.setattr(llm.CONFIG, "provider", "gemini")
    assert llm._qualified_model("gemini-2.5-flash") == "gemini/gemini-2.5-flash"
    monkeypatch.setattr(llm.CONFIG, "provider", "anthropic")
    assert llm._qualified_model("claude-3-haiku-20240307") == "anthropic/claude-3-haiku-20240307"
    monkeypatch.setattr(llm.CONFIG, "provider", "openai-free")
    assert llm._qualified_model("gpt-4o-mini") == "openai/gpt-4o-mini"
    assert llm._qualified_model("qwen/qwen3.8-27b") == "openai/qwen/qwen3.8-27b"
    assert llm._qualified_model("openai/gpt-oss-120b") == "openai/openai/gpt-oss-120b"


def test_model_prefix_not_duplicated(monkeypatch):
    monkeypatch.setattr(llm.CONFIG, "provider", "gemini")
    assert llm._qualified_model("gemini/gemini-2.5-flash") == "gemini/gemini-2.5-flash"
