"""Application exception hierarchy.

Define domain exceptions here. Routes map these to HTTP responses.
Services should raise these exceptions, not HTTP exceptions.
"""


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "An error occurred") -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", resource_id: str | None = None) -> None:
        self.resource = resource
        self.resource_id = resource_id
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(message)


class ValidationError(AppException):
    """Raised when input validation fails at the domain level."""

    def __init__(self, message: str = "Validation failed", field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


class ConflictError(AppException):
    """Raised when an operation conflicts with existing state."""

    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message)


class AuthorizationError(AppException):
    """Raised when a user lacks permission for an operation."""

    def __init__(self, message: str = "Not authorized") -> None:
        super().__init__(message)
