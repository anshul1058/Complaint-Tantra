def test_hash_embedding_is_deterministic_and_normalized(monkeypatch):
    monkeypatch.setenv("EMBEDDING_BACKEND", "hash")
    from services.embeddings import DIM, embed_text

    a = embed_text("fee refund denied by college")
    b = embed_text("fee refund denied by college")
    other = embed_text("ragging and threats in the hostel")

    assert a == b
    assert len(a) == DIM
    assert abs(sum(v * v for v in a) - 1.0) < 1e-9
    assert sum(x * y for x, y in zip(a, other)) < 0.5
    assert embed_text("   ") is None
