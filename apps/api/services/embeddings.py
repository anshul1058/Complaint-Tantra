"""Text embeddings: BAAI/bge-m3 when available, deterministic hashing fallback.

The model is loaded lazily on first use, so importing the app or running tests
never triggers a download. Set EMBEDDING_BACKEND=hash to force the offline
fallback (fast demos, CI, no network).
"""

import hashlib
import math
import os
import re
import threading

DIM = 1024
DEFAULT_MODEL = "BAAI/bge-m3"

_model = None
_model_failed = False
_lock = threading.Lock()


def _model_name() -> str:
    name = os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
    return name if "/" in name else f"BAAI/{name}"


def _get_model():
    global _model, _model_failed
    if _model is not None:
        return _model
    if _model_failed:
        return None
    with _lock:
        if _model is None and not _model_failed:
            try:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(
                    _model_name(), device=os.getenv("EMBEDDING_DEVICE") or None
                )
            except Exception:
                _model_failed = True
    return _model


def _hash_embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % DIM
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return None
    return [v / norm for v in vec]


def embed_text(text: str | None) -> list[float] | None:
    if not text or not text.strip():
        return None

    if os.getenv("EMBEDDING_BACKEND", "auto").lower() != "hash":
        model = _get_model()
        if model is not None:
            vec = model.encode(text, normalize_embeddings=True).tolist()
            if len(vec) == DIM:
                return vec
    return _hash_embed(text)
