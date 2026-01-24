"""Dependency injection wiring.

This module creates and wires up service instances with their dependencies.
It swaps real implementations for fakes when running in test mode.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.infrastructure.database import get_db_session
from app.repositories.items import (
    ItemRepository,
    PostgresItemRepository,
    FakeItemRepository,
)
from app.services.items import ItemService

# Singleton in-memory repository for test mode. This ensures all requests
# during a test run share the same backing store.
_test_item_repository: FakeItemRepository | None = None


def _get_test_item_repository() -> FakeItemRepository:
    """Get or create the singleton test repository."""
    global _test_item_repository
    if _test_item_repository is None:
        _test_item_repository = FakeItemRepository()
    return _test_item_repository


def reset_test_repositories() -> None:
    """Reset all test repository singletons.

    Call this in test fixtures to ensure test isolation.
    """
    global _test_item_repository
    if _test_item_repository is not None:
        _test_item_repository.clear()
        _test_item_repository = None


async def get_item_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)],
) -> AsyncGenerator[ItemRepository, None]:
    """Get the item repository based on environment.

    When running in test mode we want a single in-memory repository instance
    so calls that happen across multiple requests (create then list) operate
    on the same backing store. In production we instantiate the
    PostgresItemRepository per-request with the DB session.
    """
    if settings.is_test:
        yield _get_test_item_repository()
    else:
        assert session is not None, "Database session required in production"
        yield PostgresItemRepository(session)


async def get_item_service(
    repo: Annotated[ItemRepository, Depends(get_item_repository)],
) -> ItemService:
    """Get the item service with injected dependencies."""
    return ItemService(items=repo)
