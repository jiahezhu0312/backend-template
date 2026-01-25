"""Application exception hierarchy.

Define domain exceptions here. Routes map these to HTTP responses.
Services and repositories should raise these exceptions, not HTTP exceptions.

Exception → HTTP mapping (defined in main.py):
    AuthenticationError  → 401 Unauthorized
    AuthorizationError   → 403 Forbidden
    NotFoundError        → 404 Not Found
    ConflictError        → 409 Conflict
    PreconditionError    → 412 Precondition Failed
    ValidationError      → 422 Unprocessable Entity
    RateLimitError       → 429 Too Many Requests
    AppException         → 400 Bad Request (catch-all)
    DataSourceError      → 502 Bad Gateway
    ExternalServiceError → 502 Bad Gateway
    ServiceUnavailableError → 503 Service Unavailable
    TimeoutError         → 504 Gateway Timeout
"""


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "An error occurred") -> None:
        self.message = message
        super().__init__(message)


# ─────────────────────────────────────────────────────────────
# Client Errors (4xx)
# ─────────────────────────────────────────────────────────────


class AuthenticationError(AppException):
    """Raised when authentication is missing or invalid.

    Use for: missing token, expired token, invalid credentials.
    Maps to: 401 Unauthorized
    """

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message)


class AuthorizationError(AppException):
    """Raised when a user lacks permission for an operation.

    Use for: user is authenticated but not allowed to perform action.
    Maps to: 403 Forbidden
    """

    def __init__(self, message: str = "Not authorized") -> None:
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist.

    Maps to: 404 Not Found
    """

    def __init__(self, resource: str = "Resource", resource_id: str | None = None) -> None:
        self.resource = resource
        self.resource_id = resource_id
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message)


class ConflictError(AppException):
    """Raised when an operation conflicts with existing state.

    Use for: duplicate entries, concurrent modification conflicts.
    Maps to: 409 Conflict
    """

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message)


class PreconditionError(AppException):
    """Raised when a precondition for the operation is not met.

    Use for: ETag mismatch, version conflicts, conditional requests.
    Maps to: 412 Precondition Failed
    """

    def __init__(self, message: str = "Precondition failed") -> None:
        super().__init__(message)


class ValidationError(AppException):
    """Raised when input validation fails at the domain level.

    Use for: business rule violations beyond schema validation.
    Maps to: 422 Unprocessable Entity
    """

    def __init__(self, message: str = "Validation failed", field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


class RateLimitError(AppException):
    """Raised when rate limit is exceeded.

    Maps to: 429 Too Many Requests
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after  # seconds until retry is allowed
        super().__init__(message)


# ─────────────────────────────────────────────────────────────
# Server Errors (5xx)
# ─────────────────────────────────────────────────────────────


class DataSourceError(AppException):
    """Raised when an internal data source returns invalid or corrupt data.

    Use for: malformed JSON from GCS/S3, schema mismatch, data corruption.
    Maps to: 502 Bad Gateway
    """

    def __init__(self, source: str, message: str = "Invalid data") -> None:
        self.source = source
        super().__init__(f"{source}: {message}")


class ExternalServiceError(AppException):
    """Raised when an external API or service call fails.

    Use for: third-party API errors, payment gateway failures, etc.
    Maps to: 502 Bad Gateway
    """

    def __init__(
        self,
        service: str,
        message: str = "External service error",
        status_code: int | None = None,
    ) -> None:
        self.service = service
        self.status_code = status_code  # original status from external service
        super().__init__(f"{service}: {message}")


class ServiceUnavailableError(AppException):
    """Raised when a required service or dependency is unavailable.

    Use for: database down, cache unavailable, maintenance mode.
    Maps to: 503 Service Unavailable
    """

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after  # seconds until service may be available
        super().__init__(message)


class TimeoutError(AppException):
    """Raised when an operation times out.

    Use for: database query timeout, external API timeout.
    Maps to: 504 Gateway Timeout
    """

    def __init__(self, operation: str = "Operation", timeout_seconds: float | None = None) -> None:
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        message = f"{operation} timed out"
        if timeout_seconds:
            message = f"{operation} timed out after {timeout_seconds}s"
        super().__init__(message)
