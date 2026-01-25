# Developer Guide

A quick guide to writing code that follows this architecture.

## Overview

This codebase follows a **layered architecture** with clear separation of concerns:

| Layer | Responsibility | Depends On |
|-------|----------------|------------|
| **Routes** | HTTP handling (thin) | Services |
| **Services** | Business logic | Repositories |
| **Repositories** | Data access | Storage backend |
| **Domain** | Business models | Nothing |

**Key principles:**

- **Routes are thin** — validate input, call service, return response
- **Services own the logic** — orchestration, validation, exceptions
- **Repositories are swappable** — interface + implementations (in-memory, SQL, Firestore, etc.)
- **Domain models are pure** — no framework dependencies

**Quick links:**

- [Adding a Feature](#adding-a-new-feature) — step-by-step guide
- [Rules by Layer](#rules-by-layer) — do's and don'ts
- [Exception Handling](#exception-handling) — error patterns
- [Logging](#logging) — structured logging guide
- [Typing](#typing-best-practices) — type annotation conventions

---

## Project Structure

```
src/app/
├── domain/         # Business models (Pydantic)
├── schema/         # API request/response models (Pydantic)
├── repositories/   # Data access (interface + implementations)
├── services/       # Business logic
├── routes/         # HTTP endpoints (thin)
├── dependencies/   # DI wiring (per-feature)
└── infrastructure/ # Logging, external clients
```

---

## Adding a New Feature

Example: Adding `users` feature.

### Step 1: Domain Model

Create `src/app/domain/users.py`:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    name: str

class UserCreate(BaseModel):
    email: str
    name: str
```

### Step 2: Schema (API models)

Create `src/app/schema/users.py`:

```python
from pydantic import BaseModel

# Requests
class CreateUserRequest(BaseModel):
    email: str
    name: str

# Responses
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
```

### Step 3: Repository

Create `src/app/repositories/users/` folder:

```python
# interface.py
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    async def get(self, user_id: str) -> User | None: ...
    
    @abstractmethod
    async def create(self, user_id: str, data: UserCreate) -> User: ...

# fake.py
class FakeUserRepository(UserRepository):
    def __init__(self):
        self.users: dict[str, User] = {}
    # ... implement methods
```

### Step 4: Service

Create `src/app/services/users/`:

```python
# service.py
class UserService:
    def __init__(self, users: UserRepository):
        self.users = users

# logic.py (pure functions)
def validate_email(email: str) -> bool:
    return "@" in email
```

### Step 5: Route

Create `src/app/routes/users.py`:

```python
router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)],
):
    # Call service, return response
```

### Step 6: Wire Dependencies

Create `src/app/dependencies/users.py`:

```python
from app.repositories.users import FakeUserRepository, UserRepository
from app.services.users import UserService

def get_user_repository(...) -> UserRepository:
    ...

async def get_user_service(...) -> UserService:
    ...
```

Then export from `src/app/dependencies/__init__.py`:

```python
from app.dependencies.users import get_user_repository, get_user_service
```

### Step 7: Register Route

Add to `src/app/main.py`:

```python
from app.routes.users import router as users_router
app.include_router(users_router)
```

---

## Rules by Layer

### Routes (thin)

```python
# ✅ DO: Call service, return response
@router.get("/{id}")
async def get_item(id: str, service: ItemService):
    item = await service.get_item(id)
    return ItemResponse.model_validate(item)

# ❌ DON'T: Put logic in routes
@router.get("/{id}")
async def get_item(id: str, repo: ItemRepository):
    item = await repo.get(id)
    if item.price > 100:  # Business logic doesn't belong here
        item.discount = 0.1
    return item
```

### Services

```python
# ✅ DO: Depend on repository interfaces
class ItemService:
    def __init__(self, items: ItemRepository):  # Abstract type
        self.items = items

# ❌ DON'T: Depend on concrete implementations
class ItemService:
    def __init__(self, items: FakeItemRepository):  # Concrete type
        self.items = items
```

### Pure Functions (logic.py)

```python
# ✅ DO: Input → Output, no side effects
def calculate_discount(price: Decimal, quantity: int) -> Decimal:
    if quantity >= 10:
        return price * Decimal("0.1")
    return Decimal("0")

# ❌ DON'T: Access external services
def calculate_discount(price: Decimal, api: ExternalAPI) -> Decimal:
    settings = api.get_settings()  # Side effect!
    return price * settings.discount_rate
```

### Repositories

```python
# ✅ DO: One repository per domain entity
class ItemRepository(ABC):
    async def get(self, item_id: str) -> Item | None: ...
    async def create(self, ...) -> Item: ...

# ❌ DON'T: Mix entities in one repository
class DataRepository(ABC):
    async def get_item(self, ...) -> Item: ...
    async def get_user(self, ...) -> User: ...  # Should be separate
```

---

## When to Use What

| I need to... | Use |
|--------------|-----|
| Validate API input | `schema/` (Pydantic) |
| Represent internal data | `domain/` (Pydantic) |
| Calculate/transform data | `services/*/logic.py` (pure functions) |
| Coordinate operations | `services/*/service.py` (service class) |
| Read/write data | `repositories/` |
| Handle HTTP | `routes/` |

---

## Testing Strategy

| What to test | How |
|--------------|-----|
| Pure functions | Direct call, no setup |
| Services | Inject `FakeRepository` |
| Routes | `TestClient` + fake dependencies |

```python
# Testing pure functions (instant)
def test_calculate_discount():
    assert calculate_discount(Decimal("100"), 10) == Decimal("10")

# Testing services (with fakes)
async def test_create_item():
    repo = FakeItemRepository()
    service = ItemService(items=repo)
    item = await service.create_item(ItemCreate(name="Test"))
    assert item.name == "Test"
```

---

## Common Patterns

### Service needs multiple repositories

```python
class OrderService:
    def __init__(
        self,
        orders: OrderRepository,
        users: UserRepository,    # Multiple repos OK
        items: ItemRepository,
    ):
        ...
```

### Sharing logic between services

Put shared logic in `services/shared/` or `domain/`:

```python
# services/shared/pricing.py
def apply_tax(amount: Decimal, rate: Decimal) -> Decimal:
    return amount * (1 + rate)
```

### Shared schemas

If a request/response object is reused across features, put it in `schema/shared.py`:

```python
# schema/shared.py
class Address(BaseModel):
    street: str
    city: str
```

### Common utilities

Put small shared helpers in `common/`:

```python
from app.common import normalize_pagination, utc_now

skip, limit = normalize_pagination(skip=skip, limit=limit)
created_at = utc_now()
```

---

## Typing Best Practices

This project uses Python 3.10+ type hints. Follow these conventions:

### Use Modern Syntax

```python
# ✅ DO: Modern union syntax (Python 3.10+)
def get_item(item_id: str) -> Item | None:
    ...

# ❌ DON'T: Old Optional syntax
from typing import Optional
def get_item(item_id: str) -> Optional[Item]:
    ...
```

```python
# ✅ DO: Built-in generics (Python 3.9+)
def list_items() -> list[Item]:
    ...

items: dict[str, Item] = {}
result: tuple[bool, str | None] = (True, None)

# ❌ DON'T: Import from typing
from typing import List, Dict, Tuple
def list_items() -> List[Item]:
    ...
```

```python
# ✅ DO: Use collections.abc for abstract types
from collections.abc import Sequence, Mapping, AsyncGenerator

async def get_items() -> AsyncGenerator[Item, None]:
    ...

# ❌ DON'T: Import from typing
from typing import AsyncGenerator
```

### Always Annotate Return Types

```python
# ✅ DO: Explicit return types
def calculate_total(prices: list[Decimal]) -> Decimal:
    return sum(prices)

async def create_item(data: ItemCreate) -> Item:
    ...

def __init__(self, repo: ItemRepository) -> None:
    self.repo = repo

# ❌ DON'T: Missing return types
def calculate_total(prices: list[Decimal]):
    return sum(prices)
```

### Use Annotated for Dependency Injection

```python
# ✅ DO: Annotated with Depends
from typing import Annotated

async def get_item(
    item_id: str,
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    ...

# ❌ DON'T: Depends without Annotated
async def get_item(
    item_id: str,
    service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    ...
```

### Abstract Methods

```python
# ✅ DO: Use ellipsis (...) for abstract method bodies
class ItemRepository(ABC):
    @abstractmethod
    async def get(self, item_id: str) -> Item | None:
        ...

# ❌ DON'T: Use pass
class ItemRepository(ABC):
    @abstractmethod
    async def get(self, item_id: str) -> Item | None:
        pass
```

### Function Parameters

```python
# ✅ DO: Use keyword-only arguments for optional params
async def list_items(*, skip: int = 0, limit: int = 100) -> list[Item]:
    ...

# ✅ DO: Type all parameters
def validate_name(name: str, max_length: int = 255) -> bool:
    ...

# ❌ DON'T: Leave parameters untyped
def validate_name(name, max_length=255):
    ...
```

### Complex Types

```python
# ✅ DO: Use TypeAlias for complex types (if reused)
from typing import TypeAlias

ItemDict: TypeAlias = dict[str, Item]
ValidationResult: TypeAlias = tuple[bool, str | None]

# ✅ DO: Use TypedDict for dict structures with known keys
from typing import TypedDict

class PaginationParams(TypedDict):
    skip: int
    limit: int
```

### Callable Types

```python
# ✅ DO: Use Callable from collections.abc
from collections.abc import Callable

def retry(func: Callable[[], T], attempts: int = 3) -> T:
    ...

# ✅ DO: Use ParamSpec for decorators that preserve signatures
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

def log_calls(func: Callable[P, T]) -> Callable[P, T]:
    ...
```

### Type Narrowing

```python
# ✅ DO: Check before using
item = await service.get_item(item_id)
if item is None:
    raise HTTPException(status_code=404)
return ItemResponse.model_validate(item)  # item is Item, not Item | None
```

### Avoid These Anti-Patterns

```python
# ❌ DON'T: Use Any unless absolutely necessary
from typing import Any
def process(data: Any) -> Any:
    ...

# ❌ DON'T: Use # type: ignore without explanation
result = sketchy_function()  # type: ignore

# ✅ DO: Explain if suppression is needed
result = sketchy_function()  # type: ignore[arg-type]  # third-party lib issue

# ❌ DON'T: Cast unnecessarily
from typing import cast
item = cast(Item, maybe_item)  # Avoid - use proper narrowing instead
```

---

## Logging

This project uses **structlog** for structured logging with automatic context propagation.

### Setup Overview

- **Development**: Colored console output (human-readable)
- **Production**: JSON output (machine-parseable, GCP-compatible)
- **Context variables**: `request_id` is automatically attached to all logs via middleware

Configure via environment variables:

```bash
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=console    # console (dev) or json (prod)
```

### Getting a Logger

```python
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
```

### Logging Best Practices

#### Use Structured Fields (Not String Interpolation)

```python
# ✅ DO: Pass data as keyword arguments
logger.info("item_created", item_id=item.id, name=item.name)

# ❌ DON'T: Interpolate strings
logger.info(f"Created item {item.id} with name {item.name}")
```

#### Use Snake_Case Event Names

```python
# ✅ DO: Descriptive event names
logger.info("payment_processed", amount=100, currency="USD")
logger.warning("rate_limit_exceeded", user_id=user_id)
logger.error("external_api_failed", service="stripe", status_code=500)

# ❌ DON'T: Sentence-style messages
logger.info("Payment was processed successfully")
```

#### Log at the Right Level

| Level | Use For | Example |
|-------|---------|---------|
| `DEBUG` | Detailed diagnostics (dev only) | Cache hits, SQL queries |
| `INFO` | Normal operations | `item_created`, `user_logged_in` |
| `WARNING` | Recoverable issues | Slow queries, retry attempts |
| `ERROR` | Failures needing attention | External API failures |
| `CRITICAL` | System unusable | Database connection lost |

#### Log in Services (Not Routes or Repositories)

```python
# ✅ DO: Log business events in services
class ItemService:
    async def create_item(self, data: ItemCreate) -> Item:
        item = await self.items.create(item_id, data)
        logger.info("item_created", item_id=item_id, name=data.name)
        return item

    async def delete_item(self, item_id: str) -> bool:
        deleted = await self.items.delete(item_id)
        if deleted:
            logger.info("item_deleted", item_id=item_id)
        return deleted

# ❌ DON'T: Log in routes (they should be thin)
@router.post("")
async def create_item(request: CreateItemRequest, service: ItemService):
    logger.info("creating item...")  # Don't do this
    return await service.create_item(...)
```

#### Log Errors with Context

```python
# ✅ DO: Include relevant context
try:
    result = await external_api.call(payload)
except ExternalAPIError as e:
    logger.error(
        "external_api_failed",
        service="payment_gateway",
        error=str(e),
        payload_id=payload.id,
    )
    raise

# ✅ DO: Use logger.exception() for stack traces
try:
    process_data(data)
except Exception:
    logger.exception("data_processing_failed", data_id=data.id)
    raise
```

#### What to Log vs What Not to Log

```python
# ✅ DO: Log these
logger.info("application_startup", env=settings.env, version="1.0.0")
logger.info("user_registered", user_id=user.id)
logger.info("order_completed", order_id=order.id, total=order.total)
logger.warning("slow_query", duration_ms=150, query_type="list_items")

# ❌ DON'T: Log sensitive data
logger.info("user_login", password=password)           # Never log passwords
logger.info("payment", credit_card=card_number)        # Never log card numbers
logger.info("request", headers=dict(request.headers))  # May contain auth tokens
```

### Request Context

The middleware automatically binds `request_id` to all logs during a request:

```python
# All logs within a request automatically include request_id
logger.info("item_created", item_id="123")
# Output: {"event": "item_created", "item_id": "123", "request_id": "abc-456", ...}
```

You can bind additional context for a request scope:

```python
from structlog.contextvars import bind_contextvars

# In a route or middleware
bind_contextvars(user_id=current_user.id)

# All subsequent logs in this request will include user_id
logger.info("item_created", item_id="123")
# Output: {"event": "item_created", "item_id": "123", "user_id": "user-789", ...}
```

---

## Exception Handling

Services raise domain exceptions. FastAPI exception handlers convert them to HTTP responses.

### Exception Hierarchy

| Exception | HTTP Status | Use For |
|-----------|-------------|---------|
| `NotFoundError` | 404 | Resource doesn't exist |
| `ValidationError` | 422 | Business rule violation |
| `ConflictError` | 409 | Duplicate or state conflict |
| `AuthorizationError` | 403 | Permission denied |
| `AppException` | 400 | Generic application error |

### Raising Exceptions in Services

```python
from app.services.exceptions import NotFoundError, ValidationError

class ItemService:
    async def get_item(self, item_id: str) -> Item:
        item = await self.items.get(item_id)
        if item is None:
            raise NotFoundError("Item", item_id)
        return item

    async def create_item(self, data: ItemCreate) -> Item:
        if await self.items.exists_by_name(data.name):
            raise ConflictError(f"Item '{data.name}' already exists")
        return await self.items.create(data)
```

### Routes Stay Clean

```python
# ✅ DO: Let exceptions propagate (handlers convert to HTTP responses)
@router.get("/{item_id}")
async def get_item(item_id: str, service: ItemService) -> ItemResponse:
    item = await service.get_item(item_id)  # Raises NotFoundError if missing
    return ItemResponse.model_validate(item)

# ❌ DON'T: Catch and re-raise as HTTPException
@router.get("/{item_id}")
async def get_item(item_id: str, service: ItemService) -> ItemResponse:
    item = await service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse.model_validate(item)
```

### Creating Custom Exceptions

Add new exceptions to `services/exceptions.py`:

```python
class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")
```

Then add a handler in `main.py`:

```python
@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": exc.message},
        headers={"Retry-After": str(exc.retry_after)},
    )
```

---

## Checklist for New Features

- [ ] Domain model in `domain/`
- [ ] Schema in `schema/`
- [ ] Repository interface + implementations in `repositories/`
- [ ] Service in `services/`
- [ ] Route in `routes/`
- [ ] Dependencies wired in `dependencies/`
- [ ] Router registered in `main.py`
