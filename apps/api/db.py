from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
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
