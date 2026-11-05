from services import sentiment


def test_analyze_sentiment_maps_plain_labels(monkeypatch):
    class FakeModel:
        def __call__(self, text):
            return [{"label": "negative", "score": 0.91}]

    monkeypatch.setattr(sentiment, "_pipeline", FakeModel())
    monkeypatch.delenv("SENTIMENT_BACKEND", raising=False)
    assert sentiment.analyze_sentiment("terrible") == {"label": "negative", "score": 0.91}
