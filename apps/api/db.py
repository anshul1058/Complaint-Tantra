from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

def _async_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


# Supabase's transaction pooler (PgBouncer) can reuse a backend connection for
# different clients. asyncpg's default prepared-statement cache then causes
# errors such as `prepared statement ... already exists` during startup. Keep
# the cache disabled for pooler URLs; it is safe for direct Postgres URLs too.
engine = create_async_engine(
    _async_url(settings.database_url),
    pool_pre_ping=True,
    connect_args={"statement_cache_size": 0},
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        import models  # noqa: F401  (register tables)

        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_institutions_name_trgm "
            "ON institutions USING gin (name_normalized gin_trgm_ops)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_institutions_name_embedding "
            "ON institutions USING hnsw (name_embedding vector_cosine_ops)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_cases_text_embedding "
            "ON cases USING hnsw (text_embedding vector_cosine_ops)"
        ))
        await conn.execute(text(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_counts AS
            SELECT assigned_bureau, status, date_trunc('month', received_at) AS m, count(*) AS n
            FROM cases GROUP BY 1,2,3
            """
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_cases_received_at ON cases (received_at DESC)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_cases_status_bureau ON cases (status, assigned_bureau)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_alerts_unread ON alerts (acknowledged_at, created_at DESC)"
        ))
        try:
            # Append-only timeline; the app only inserts (§3, §8).
            await conn.execute(text(
                "REVOKE UPDATE, DELETE, TRUNCATE ON case_actions FROM PUBLIC"
            ))
        except Exception:
            pass
