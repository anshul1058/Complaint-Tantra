#!/usr/bin/env python3
"""Export FastAPI schema for frontend type generation.

Usage: .venv/bin/python scripts/export_openapi.py
Then:  cd apps/web && npm run gen:api
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from main import app  # noqa: E402


def main() -> None:
    out = ROOT / "apps" / "web" / "openapi.json"
    out.write_text(json.dumps(app.openapi(), indent=2))
    print(f"wrote {out.relative_to(ROOT)} ({len(app.openapi()['paths'])} paths)")


if __name__ == "__main__":
    main()
