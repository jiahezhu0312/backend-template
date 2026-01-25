"""Item service - orchestration layer.

The service class coordinates operations and depends on repositories.
For complex calculations, it calls pure functions from logic.py.
"""

import uuid

from app.domain.items import Item, ItemCreate, ItemUpdate
from app.repositories.items import ItemRepository
from app.services.exceptions import NotFoundError


class ItemService:
    """Service for item-related business operations."""

    def __init__(self, items: ItemRepository) -> None:
        self.items = items

    async def get_item(self, item_id: str) -> Item:
        """Get an item by ID. Raises NotFoundError if not found."""
        item = await self.items.get(item_id)
        if item is None:
            raise NotFoundError("Item", item_id)
        return item

    async def list_items(self, *, skip: int = 0, limit: int = 100) -> list[Item]:
        """List items with pagination."""
        return await self.items.list(skip=skip, limit=limit)

    async def count_items(self) -> int:
        """Count total items."""
        return await self.items.count()

    async def create_item(self, data: ItemCreate) -> Item:
        """Create a new item with a generated ID."""
        item_id = str(uuid.uuid4())
        return await self.items.create(item_id, data)

    async def update_item(self, item_id: str, data: ItemUpdate) -> Item:
        """Update an existing item. Raises NotFoundError if not found."""
        item = await self.items.update(item_id, data)
        if item is None:
            raise NotFoundError("Item", item_id)
        return item

    async def delete_item(self, item_id: str) -> None:
        """Delete an item. Raises NotFoundError if not found."""
        deleted = await self.items.delete(item_id)
        if not deleted:
            raise NotFoundError("Item", item_id)
