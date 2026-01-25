"""Dependency injection wiring.

This package creates and wires up service instances with their dependencies.
"""

from app.dependencies.items import get_item_repository, get_item_service, reset_item_repository

__all__ = [
    "get_item_repository",
    "get_item_service",
    "reset_item_repository",
]


def reset_repositories() -> None:
    """Reset all repository singletons.

    Call this in test fixtures to ensure test isolation.
    """
    reset_item_repository()
