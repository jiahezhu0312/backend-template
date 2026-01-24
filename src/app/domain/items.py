"""Item domain models.

These represent the internal business concept of an Item.
Used by services and repositories.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Item(BaseModel):
    """Domain model for an item.

    This is the internal representation used by services and repositories.
    It may contain fields not exposed in API responses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ItemCreate(BaseModel):
    """Data required to create a new item."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class ItemUpdate(BaseModel):
    """Data for updating an existing item. All fields optional."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None
