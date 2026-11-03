"""PII masking before text leaves the process to an external LLM (system.md §6.2)."""

import re

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)")
_AADHAAR = re.compile(r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)")


def mask_pii(text: str | None) -> str:
    if not text:
        return ""
    text = _EMAIL.sub("[EMAIL]", text)
    text = _AADHAAR.sub("[AADHAAR]", text)
    text = _PHONE.sub("[PHONE]", text)
    return text


if __name__ == "__main__":
    raw = "Call 9876543210 or mail a@b.com, Aadhaar 1234 5678 9012"
    masked = mask_pii(raw)
    assert "9876543210" not in masked and "a@b.com" not in masked
    assert "[PHONE]" in masked and "[EMAIL]" in masked and "[AADHAAR]" in masked
    print(masked)
