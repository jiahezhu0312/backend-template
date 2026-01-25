"""Item domain models.

These represent the internal business concept of an Item.
Used by services and repositories.

Note: Validation constraints (min_length, max_length) are defined in the
schema layer (schema/items.py) which is the API boundary. Domain models
trust that data has already been validated by the time it reaches here.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    """Data required to create a new item.

    Validation is handled at the API boundary (schema layer).
    """

    name: str
    description: str | None = None


class ItemUpdate(BaseModel):
    """Data for updating an existing item. All fields optional.

    Validation is handled at the API boundary (schema layer).
    """

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
