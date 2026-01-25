"""PostgreSQL implementation of ItemRepository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.items import Item, ItemCreate, ItemUpdate
from app.infrastructure.orm import ItemORM
from app.repositories.items.interface import ItemRepository


class PostgresItemRepository(ItemRepository):
    """PostgreSQL implementation of ItemRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, item_id: str) -> Item | None:
        """Get an item by ID."""
        result = await self.session.execute(select(ItemORM).where(ItemORM.id == item_id))
        row = result.scalar_one_or_none()
        return Item.model_validate(row) if row else None

    async def list(self, *, skip: int = 0, limit: int = 100) -> list[Item]:
        """List items with pagination."""
        result = await self.session.execute(select(ItemORM).offset(skip).limit(limit))
        rows = result.scalars().all()
        return [Item.model_validate(row) for row in rows]

    async def count(self) -> int:
        """Count total items."""
        result = await self.session.execute(select(func.count()).select_from(ItemORM))
        return int(result.scalar_one())

    async def create(self, item_id: str, data: ItemCreate) -> Item:
        """Create a new item."""
        orm_item = ItemORM(
            id=item_id,
            name=data.name,
            description=data.description,
        )
        self.session.add(orm_item)
        await self.session.flush()
        await self.session.refresh(orm_item)
        return Item.model_validate(orm_item)

    async def update(self, item_id: str, data: ItemUpdate) -> Item | None:
        """Update an existing item."""
        result = await self.session.execute(select(ItemORM).where(ItemORM.id == item_id))
        orm_item = result.scalar_one_or_none()
        if not orm_item:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(orm_item, field, value)

        await self.session.flush()
        await self.session.refresh(orm_item)
        return Item.model_validate(orm_item)

    async def delete(self, item_id: str) -> bool:
        """Delete an item."""
        result = await self.session.execute(select(ItemORM).where(ItemORM.id == item_id))
        orm_item = result.scalar_one_or_none()
        if not orm_item:
            return False

        await self.session.delete(orm_item)
        await self.session.flush()
        return True
