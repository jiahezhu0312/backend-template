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


async def get_item_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AsyncGenerator[ItemRepository, None]:
    """Get the item repository based on environment."""
    if settings.is_test:
        yield FakeItemRepository()
    else:
        yield PostgresItemRepository(session)


async def get_item_service(
    repo: Annotated[ItemRepository, Depends(get_item_repository)],
) -> ItemService:
    """Get the item service with injected dependencies."""
    return ItemService(items=repo)
