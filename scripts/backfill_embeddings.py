#!/usr/bin/env python3
"""Backfill BGE-M3 vectors for institutions and cases.

Usage (repo root):
    .venv/bin/python scripts/backfill_embeddings.py
    .venv/bin/python scripts/backfill_embeddings.py --kind institutions --force
    .venv/bin/python scripts/backfill_embeddings.py --allow-hash

Never mixes backends silently: with EMBEDDING_BACKEND=hash you must pass
--allow-hash, and switching backends requires --force to re-embed every row.
"""

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from sqlalchemy import select  # noqa: E402

from db import SessionLocal, init_db  # noqa: E402
from models import Case, Institution  # noqa: E402
from services.embeddings import active_backend, embed_many  # noqa: E402


async def backfill(kind: str, limit: int | None, force: bool, batch_size: int = 32) -> None:
    async with SessionLocal() as db:
        if kind in ("institutions", "all"):
            q = select(Institution)
            if not force:
                q = q.where(Institution.name_embedding.is_(None))
            if limit:
                q = q.limit(limit)
            rows = list((await db.execute(q)).scalars())
            print(f"institutions: {len(rows)} rows")
            for start in range(0, len(rows), batch_size):
                batch = rows[start : start + batch_size]
                vecs = await asyncio.to_thread(embed_many, [r.name for r in batch])
                for row, vec in zip(batch, vecs):
                    row.name_embedding = vec
                await db.commit()
                print(f"  {min(start + batch_size, len(rows))}/{len(rows)}", flush=True)

        if kind in ("cases", "all"):
            q = select(Case).where(Case.text_english.is_not(None) | Case.text_original.is_not(None))
            if not force:
                q = q.where(Case.text_embedding.is_(None))
            if limit:
                q = q.limit(limit)
            rows = list((await db.execute(q)).scalars())
            print(f"cases: {len(rows)} rows")
            for start in range(0, len(rows), batch_size):
                batch = rows[start : start + batch_size]
                texts = [r.text_english or r.text_original for r in batch]
                vecs = await asyncio.to_thread(embed_many, texts)
                for row, vec in zip(batch, vecs):
                    row.text_embedding = vec
                await db.commit()
                print(f"  {min(start + batch_size, len(rows))}/{len(rows)}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["institutions", "cases", "all"], default="all")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="re-embed rows that already have vectors")
    ap.add_argument("--allow-hash", action="store_true", help="write hashing vectors instead of BGE-M3")
    ap.add_argument("--batch", type=int, default=64)
    args = ap.parse_args()

    backend = active_backend()
    print(f"embedding backend: {backend}")
    if backend == "hash" and not args.allow_hash:
        print(
            "Refusing to write hashing vectors. Install sentence-transformers and download "
            "BAAI/bge-m3, or pass --allow-hash for an offline demo.",
            file=sys.stderr,
        )
        return 2

    async def run() -> None:
        await init_db()
        await backfill(args.kind, args.limit, args.force, args.batch)

    asyncio.run(run())
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
