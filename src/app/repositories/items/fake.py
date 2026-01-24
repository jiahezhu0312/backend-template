"""Fake (in-memory) implementation of ItemRepository for testing."""

from datetime import datetime, timezone

from app.domain.items import Item, ItemCreate, ItemUpdate
from app.repositories.items.interface import ItemRepository


class FakeItemRepository(ItemRepository):
    """In-memory implementation of ItemRepository for testing."""

    def __init__(self) -> None:
        self.items: dict[str, Item] = {}

    async def get(self, item_id: str) -> Item | None:
        """Get an item by ID."""
        return self.items.get(item_id)

    async def list(self, *, skip: int = 0, limit: int = 100) -> list[Item]:
        """List items with pagination."""
        all_items = list(self.items.values())
        return all_items[skip : skip + limit]

    async def count(self) -> int:
        """Count total items."""
        return len(self.items)

    async def create(self, item_id: str, data: ItemCreate) -> Item:
        """Create a new item."""
        now = datetime.now(timezone.utc)
        item = Item(
            id=item_id,
            name=data.name,
            description=data.description,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        self.items[item_id] = item
        return item

    async def update(self, item_id: str, data: ItemUpdate) -> Item | None:
        """Update an existing item."""
        existing = self.items.get(item_id)
        if not existing:
            return None

        update_data = data.model_dump(exclude_unset=True)
        updated = existing.model_copy(
            update={
                **update_data,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self.items[item_id] = updated
        return updated

    async def delete(self, item_id: str) -> bool:
        """Delete an item."""
        if item_id not in self.items:
            return False
        del self.items[item_id]
        return True

    # Test helpers

    def seed(self, items: list[Item]) -> None:
        """Seed the repository with test data."""
        for item in items:
            self.items[item.id] = item

    def clear(self) -> None:
        """Clear all items."""
        self.items.clear()
