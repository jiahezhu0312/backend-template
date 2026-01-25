"""Pagination helpers."""

DEFAULT_LIMIT = 100
MAX_LIMIT = 100


def normalize_pagination(
    *, skip: int = 0, limit: int = DEFAULT_LIMIT, max_limit: int = MAX_LIMIT
) -> tuple[int, int]:
    """Normalize skip/limit values with safe defaults."""
    safe_skip = max(skip, 0)
    safe_limit = max(min(limit, max_limit), 1)
    return safe_skip, safe_limit
