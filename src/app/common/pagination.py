"""Pagination helpers."""


def normalize_pagination(*, skip: int = 0, limit: int = 100, max_limit: int = 100) -> tuple[int, int]:
    """Normalize skip/limit values with safe defaults."""
    safe_skip = max(skip, 0)
    safe_limit = max(min(limit, max_limit), 1)
    return safe_skip, safe_limit
