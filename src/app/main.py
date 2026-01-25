"""FastAPI application entry point."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.config import get_settings
from app.infrastructure.logging import configure_logging, get_logger
from app.exceptions import (
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
from app.routes import health_router, items_router

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info(
        "application_startup",
        env=settings.env,
        debug=settings.debug,
    )
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title="FastAPI Backend",
    description="A layered FastAPI backend template",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Configure CORS if origins are specified
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Attach request ID and bind logging context."""
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    bind_contextvars(request_id=request_id)
    try:
        response = await call_next(request)
    finally:
        clear_contextvars()
    response.headers["X-Request-Id"] = request_id
    return response


# ─────────────────────────────────────────────────────────────
# Exception Handlers - Client Errors (4xx)
# ─────────────────────────────────────────────────────────────


@app.exception_handler(AuthenticationError)
async def authentication_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """Handle AuthenticationError exceptions."""
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthorizationError)
async def authorization_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle AuthorizationError exceptions."""
    return JSONResponse(status_code=403, content={"detail": exc.message})


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError exceptions."""
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    """Handle ConflictError exceptions."""
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(PreconditionError)
async def precondition_handler(request: Request, exc: PreconditionError) -> JSONResponse:
    """Handle PreconditionError exceptions."""
    return JSONResponse(status_code=412, content={"detail": exc.message})


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError exceptions."""
    content: dict[str, str | None] = {"detail": exc.message}
    if exc.field:
        content["field"] = exc.field
    return JSONResponse(status_code=422, content=content)


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    """Handle RateLimitError exceptions."""
    headers: dict[str, str] = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(status_code=429, content={"detail": exc.message}, headers=headers)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle generic AppException as 400 Bad Request."""
    return JSONResponse(status_code=400, content={"detail": exc.message})


# ─────────────────────────────────────────────────────────────
# Exception Handlers - Server Errors (5xx)
# ─────────────────────────────────────────────────────────────


@app.exception_handler(DataSourceError)
async def data_source_handler(request: Request, exc: DataSourceError) -> JSONResponse:
    """Handle DataSourceError exceptions."""
    logger.error("data_source_error", source=exc.source, message=exc.message)
    return JSONResponse(status_code=502, content={"detail": "Data source error"})


@app.exception_handler(ExternalServiceError)
async def external_service_handler(request: Request, exc: ExternalServiceError) -> JSONResponse:
    """Handle ExternalServiceError exceptions."""
    logger.error(
        "external_service_error",
        service=exc.service,
        message=exc.message,
        status_code=exc.status_code,
    )
    return JSONResponse(status_code=502, content={"detail": "External service error"})


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(
    request: Request, exc: ServiceUnavailableError
) -> JSONResponse:
    """Handle ServiceUnavailableError exceptions."""
    logger.warning("service_unavailable", message=exc.message)
    headers: dict[str, str] = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=503,
        content={"detail": exc.message},
        headers=headers,
    )


@app.exception_handler(TimeoutError)
async def timeout_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    """Handle TimeoutError exceptions."""
    logger.error(
        "timeout_error",
        operation=exc.operation,
        timeout_seconds=exc.timeout_seconds,
    )
    return JSONResponse(status_code=504, content={"detail": "Operation timed out"})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a consistent JSON error for unexpected failures."""
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


# Register routes
app.include_router(health_router)
app.include_router(items_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "FastAPI Backend Template"}
