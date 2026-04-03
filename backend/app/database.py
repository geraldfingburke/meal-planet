from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def worker_session():
    """Create an isolated engine+session for dramatiq worker threads.

    Each call gets its own engine so asyncpg connections aren't shared
    across event loops created by different ``asyncio.run()`` calls.
    """
    _engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=2, max_overflow=0)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with _session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
    await _engine.dispose()
