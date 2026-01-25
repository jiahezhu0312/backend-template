"""Repository layer - data access organized by feature/domain."""

from app.repositories.items.fake import FakeItemRepository
from app.repositories.items.interface import ItemRepository
from app.repositories.items.postgres import PostgresItemRepository

__all__ = [
    "ItemRepository",
    "PostgresItemRepository",
    "FakeItemRepository",
]
