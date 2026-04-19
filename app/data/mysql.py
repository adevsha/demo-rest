import asyncio
import logging
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_engine() -> AsyncEngine:
    global _engine, _session_factory
    _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)

    last_error: Exception | None = None
    for attempt in range(1, 6):
        try:
            async with _engine.begin() as conn:
                from app.models.db import product, user  # noqa: F401 — register mappers

                await conn.run_sync(Base.metadata.create_all)
            return _engine
        except Exception as exc:
            last_error = exc
            logger.warning(
                "MySQL not ready (attempt %d/5): %s", attempt, exc
            )
            await asyncio.sleep(2)
    raise RuntimeError(f"MySQL unreachable after retries: {last_error}")


async def close_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("MySQL engine not initialized")
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        yield session
