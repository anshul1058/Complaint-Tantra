"""Multilingual sentiment first pass (XLM-RoBERTa), used by the triage fallback.

The model is optional and lazy: when transformers/the weights are unavailable
the triage agent keeps its keyword rules. Set SENTIMENT_BACKEND=rules to skip.
"""

import os
import threading

DEFAULT_MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
LABELS = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}

_pipeline = None
_failed = False
_lock = threading.Lock()


def _get_pipeline():
    global _pipeline, _failed
    if _pipeline is not None:
        return _pipeline
    if _failed:
        return None
    with _lock:
        if _pipeline is None and not _failed:
            try:
                from transformers import pipeline

                _pipeline = pipeline(
                    "sentiment-analysis",
                    model=os.getenv("SENTIMENT_MODEL", DEFAULT_MODEL),
                    device=-1,
                )
            except Exception:
                _failed = True
    return _pipeline


def analyze_sentiment(text: str | None) -> dict | None:
    """Return {label, score} in negative|neutral|positive, or None if unavailable."""
    if not text or not text.strip():
        return None
    if os.getenv("SENTIMENT_BACKEND", "auto").lower() == "rules":
        return None
    model = _get_pipeline()
    if model is None:
        return None
    try:
        result = model(text[:512])[0]
        label = LABELS.get(str(result.get("label", "")).upper(), "neutral")
        return {"label": label, "score": round(float(result.get("score", 0.0)), 3)}
    except Exception:
        return None
