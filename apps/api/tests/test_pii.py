from services.pii import mask_pii


def test_mask_pii_removes_contact_and_aadhaar():
    raw = "Call 9876543210 or mail a@b.com, Aadhaar 1234 5678 9012"
    out = mask_pii(raw)
    assert "9876543210" not in out
    assert "a@b.com" not in out
    assert "1234 5678 9012" not in out
    assert "[PHONE]" in out and "[EMAIL]" in out and "[AADHAAR]" in out


def test_mask_pii_empty():
    assert mask_pii(None) == ""
