#!/usr/bin/env python3
"""Load the AICTE institution CSV into Supabase/Postgres.

Usage (repo root):
    .venv/bin/python scripts/import_institutions.py
    .venv/bin/python scripts/import_institutions.py --file data/institutions_real.csv
    .venv/bin/python scripts/import_institutions.py --truncate
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402

from db import SessionLocal, init_db  # noqa: E402
from models import Institution  # noqa: E402
from services.entity_resolution import normalize_name  # noqa: E402


def _row(raw: dict) -> dict:
    address = ", ".join(
        part for part in (raw.get("address_line1"), raw.get("address_line2")) if part
    )
    return {
        "permanent_id": raw["permanent_id"].strip(),
        "name": raw["institution_name"].strip(),
        "name_normalized": normalize_name(raw["institution_name"]),
        "address": address or None,
        "city": raw.get("city") or None,
        "state": raw.get("state") or None,
        "region": raw.get("aicte_region") or None,
        "trust_or_society": raw.get("trust_name") or None,
    }


async def load(path: Path, truncate: bool, batch_size: int) -> None:
    await init_db()
    rows = [_row(r) for r in csv.DictReader(path.open(encoding="utf-8")) if r.get("permanent_id")]
    print(f"csv rows: {len(rows)}")

    async with SessionLocal() as db:
        if truncate:
            await db.execute(Institution.__table__.delete())
            await db.commit()
            print("cleared institutions")

        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            stmt = insert(Institution).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Institution.permanent_id],
                set_={
                    "name": stmt.excluded.name,
                    "name_normalized": stmt.excluded.name_normalized,
                    "address": stmt.excluded.address,
                    "city": stmt.excluded.city,
                    "state": stmt.excluded.state,
                    "region": stmt.excluded.region,
                    "trust_or_society": stmt.excluded.trust_or_society,
                },
            )
            await db.execute(stmt)
            await db.commit()
            print(f"  {min(start + batch_size, len(rows))}/{len(rows)}", flush=True)

        total = (await db.execute(select(func.count()).select_from(Institution))).scalar()
        with_pid = (await db.execute(
            select(func.count()).select_from(Institution).where(Institution.permanent_id.is_not(None))
        )).scalar()
        print(f"institutions in DB: {total}, with permanent_id: {with_pid}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(ROOT / "data" / "institutions_real.csv"))
    ap.add_argument("--truncate", action="store_true", help="delete existing institutions first")
    ap.add_argument("--batch", type=int, default=500)
    args = ap.parse_args()
    asyncio.run(load(Path(args.file), args.truncate, args.batch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
