"""Service layer - business logic and orchestration."""

from app.services.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DataSourceError,
    ExternalServiceError,
    NotFoundError,
    PreconditionError,
    RateLimitError,
    ServiceUnavailableError,
    TimeoutError,
    ValidationError,
)
from app.services.items import ItemService

__all__ = [
    # Services
    "ItemService",
    # Exceptions - Client Errors (4xx)
    "AppException",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "PreconditionError",
    "ValidationError",
    "RateLimitError",
    # Exceptions - Server Errors (5xx)
    "DataSourceError",
    "ExternalServiceError",
    "ServiceUnavailableError",
    "TimeoutError",
]
