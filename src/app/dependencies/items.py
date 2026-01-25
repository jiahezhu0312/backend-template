"""Item dependencies.

Wires up the item repository and service.
"""

from typing import Annotated

from fastapi import Depends

from app.config import Settings, get_settings
from app.repositories.items import FakeItemRepository, ItemRepository
from app.services.items import ItemService

# Singleton in-memory repository for test/local mode.
_fake_item_repository: FakeItemRepository | None = None


def _get_fake_item_repository() -> FakeItemRepository:
    """Get or create the singleton fake repository."""
    global _fake_item_repository
    if _fake_item_repository is None:
        _fake_item_repository = FakeItemRepository()
    return _fake_item_repository


def reset_item_repository() -> None:
    """Reset the item repository singleton."""
    global _fake_item_repository
    if _fake_item_repository is not None:
        _fake_item_repository.clear()
        _fake_item_repository = None


def get_item_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ItemRepository:
    """Get the item repository based on environment.

    In test mode, returns an in-memory fake. In production/staging,
    return your real implementation (e.g., GCS, Firestore, PostgreSQL).
    """
    if settings.is_test:
        return _get_fake_item_repository()

    # TODO: Add your real implementation here, e.g.:
    # return GCSItemRepository(bucket=settings.gcs_bucket)
    # return FirestoreItemRepository(project=settings.gcp_project)

    # Fallback to fake for local development
    return _get_fake_item_repository()


async def get_item_service(
    repo: Annotated[ItemRepository, Depends(get_item_repository)],
) -> ItemService:
    """Get the item service with injected dependencies."""
    return ItemService(items=repo)
