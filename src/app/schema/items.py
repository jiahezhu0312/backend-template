"""Item-related request and response schemas.

Each feature/domain gets its own schema file containing both
requests and responses for that feature.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────
# Requests
# ─────────────────────────────────────────────────────────────


class CreateItemRequest(BaseModel):
    """Request body for creating an item."""

    name: str = Field(..., min_length=1, max_length=255, examples=["My Item"])
    description: str | None = Field(
        None,
        max_length=1000,
        examples=["A description of the item"],
    )


class UpdateItemRequest(BaseModel):
    """Request body for updating an item. All fields optional."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None


# ─────────────────────────────────────────────────────────────
# Responses
# ─────────────────────────────────────────────────────────────


class ItemResponse(BaseModel):
    """Response model for a single item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None


class ItemListResponse(BaseModel):
    """Response model for a list of items."""

    items: list[ItemResponse]
    total: int
