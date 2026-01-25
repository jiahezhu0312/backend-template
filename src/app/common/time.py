"""Time helpers."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)
