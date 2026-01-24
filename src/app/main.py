"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.config import get_settings
from app.infrastructure.logging import configure_logging, get_logger
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


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attach request ID and bind logging context."""
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    bind_contextvars(request_id=request_id)
    try:
        response = await call_next(request)
    finally:
        clear_contextvars()
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
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
