"""Database connection and session management."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings

# Lazy initialization - only create engine/factory when actually needed
_engine = None
_async_session_factory = None


def _get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    return _engine


def _get_session_factory():
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


async def get_db_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncGenerator[AsyncSession | None, None]:
    """Get the database session based on environment.

    When running in test mode we skip database connection entirely since
    fake repositories don't need a real session. In production we provide
    a properly managed async session with automatic commit/rollback.
    """
    if settings.is_test:
        # Test mode: no database session needed (fake repos handle storage)
        yield None
    else:
        # Production: provide real database session
        async with _get_session_factory()() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


def reset_database() -> None:
    """Reset database engine and session factory.

    Call this in test fixtures to ensure test isolation.
    """
    global _engine, _async_session_factory
    _engine = None
    _async_session_factory = None
