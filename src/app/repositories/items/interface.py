"""Item repository interface.

Defines what operations are needed for item data access.
"""

from abc import ABC, abstractmethod

from app.domain.items import Item, ItemCreate, ItemUpdate


class ItemRepository(ABC):
    """Abstract interface for item data access."""

    @abstractmethod
    async def get(self, item_id: str) -> Item | None:
        """Get an item by ID."""
        ...

    @abstractmethod
    async def list(self, *, skip: int = 0, limit: int = 100) -> list[Item]:
        """List items with pagination."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Count total items."""
        ...

    @abstractmethod
    async def create(self, item_id: str, data: ItemCreate) -> Item:
        """Create a new item."""
        ...

    @abstractmethod
    async def update(self, item_id: str, data: ItemUpdate) -> Item | None:
        """Update an existing item. Returns None if not found."""
        ...

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete an item. Returns True if deleted, False if not found."""
        ...
