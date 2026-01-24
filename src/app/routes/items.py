"""Item endpoints - example CRUD routes.

Routes are thin: they receive requests, call services, and return responses.
Business logic belongs in services, not here.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_item_service
from app.domain.items import ItemCreate, ItemUpdate
from app.schema.items import (
    CreateItemRequest,
    UpdateItemRequest,
    ItemResponse,
    ItemListResponse,
)
from app.services.items import ItemService

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=ItemListResponse)
async def list_items(
    service: Annotated[ItemService, Depends(get_item_service)],
    skip: int = 0,
    limit: int = 100,
) -> ItemListResponse:
    """List all items with pagination."""
    items = await service.list_items(skip=skip, limit=limit)
    total = await service.count_items()
    return ItemListResponse(
        items=[ItemResponse.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    """Get a single item by ID."""
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return ItemResponse.model_validate(item)


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    request: CreateItemRequest,
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    """Create a new item."""
    data = ItemCreate(name=request.name, description=request.description)
    item = await service.create_item(data)
    return ItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    request: UpdateItemRequest,
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    """Update an existing item."""
    data = ItemUpdate(**request.model_dump(exclude_unset=True))
    item = await service.update_item(item_id, data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return ItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: str,
    service: Annotated[ItemService, Depends(get_item_service)],
) -> None:
    """Delete an item."""
    deleted = await service.delete_item(item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
