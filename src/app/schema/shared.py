"""Shared schema models used across features."""

from pydantic import BaseModel, Field


class Address(BaseModel):
    """Example shared schema for nested objects."""

    street: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=255)
