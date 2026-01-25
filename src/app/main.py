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
from app.routes import health_router, items_router
from app.services import (
    AppException,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

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


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError exceptions."""
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError exceptions."""
    content: dict[str, str | None] = {"detail": exc.message}
    if exc.field:
        content["field"] = exc.field
    return JSONResponse(status_code=422, content=content)


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    """Handle ConflictError exceptions."""
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(AuthorizationError)
async def authorization_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle AuthorizationError exceptions."""
    return JSONResponse(status_code=403, content={"detail": exc.message})


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle generic AppException as 400 Bad Request."""
    return JSONResponse(status_code=400, content={"detail": exc.message})


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
