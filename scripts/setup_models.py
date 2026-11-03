#!/usr/bin/env python3
"""Download and verify the local models named in Docs_md/aiml-guide.md.

    .venv/bin/python scripts/setup_models.py              # BGE-M3 only
    .venv/bin/python scripts/setup_models.py --sentiment  # + XLM-RoBERTa sentiment
    .venv/bin/python scripts/setup_models.py --all

The LLM itself is provider-agnostic (LiteLLM). For the documented Ollama demo:
    ollama pull llama3.2:3b
    export LLM_PROVIDER=ollama
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from config import settings  # noqa: E402
from services.embeddings import DIM, active_backend, embed_text  # noqa: E402


def check_embedding() -> None:
    print(f"BGE-M3 model: {settings.embedding_model}")
    vec = embed_text("AICTE complaint about fee refund")
    if vec is None or len(vec) != DIM:
        raise SystemExit(f"embedding failed or has wrong dimension (expected {DIM})")
    if active_backend() != "bge-m3":
        raise SystemExit(
            "BGE-M3 did not load (fell back to hashing). Install sentence-transformers "
            "and retry; check EMBEDDING_BACKEND is not set to hash."
        )
    print(f"  OK backend=bge-m3 dim={len(vec)}")


def check_sentiment() -> None:
    from services.sentiment import DEFAULT_MODEL, analyze_sentiment

    model = os.getenv("SENTIMENT_MODEL", DEFAULT_MODEL)
    print(f"sentiment model: {model}")
    result = analyze_sentiment("The college threatened students and refused our fee refund.")
    if result is None:
        raise SystemExit("sentiment model unavailable (check transformers install/network)")
    print(f"  OK label={result['label']} score={result['score']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sentiment", action="store_true", help="download XLM-RoBERTa sentiment")
    ap.add_argument("--all", action="store_true", help="embeddings + sentiment")
    args = ap.parse_args()

    check_embedding()
    if args.sentiment or args.all:
        check_sentiment()

    provider = os.getenv("LLM_PROVIDER", "ollama")
    print(f"LLM provider: {provider}")
    if provider == "ollama":
        print(f"  run: ollama pull {os.getenv('OLLAMA_MODEL', 'llama3.2:3b')}")
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
