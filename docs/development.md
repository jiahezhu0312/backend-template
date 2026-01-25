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

- [Implementing from OpenAPI](#practical-guide-implementing-from-openapi-contract) — simple vs complex scenarios
- [Adding a Feature](#adding-a-new-feature) — step-by-step guide
- [When to Skip Layers](#when-to-skip-layers-pragmatic-shortcuts) — simplify when appropriate
- [FastAPI Parameter Types](#fastapi-parameter-types) — Path, Query, Field, Header
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

### Import Convention

Always import directly from modules, not from package `__init__.py`:

```python
# ✅ Do this - direct imports
from app.services.items.service import ItemService
from app.repositories.items.interface import ItemRepository
from app.dependencies.items import get_item_service

# ❌ Not this - no __init__.py re-exports to maintain
from app.services import ItemService
```

This means adding a new feature doesn't require updating any `__init__.py` files.

---

## Practical Guide: Implementing from OpenAPI Contract

You've received a new OpenAPI spec with endpoints to implement. Here's how to approach it.

### Simple Scenario: Add a Single Read Endpoint

**Contract says:** `GET /products/{product_id}` returns product details.

**Step 1: Create the schema (match the contract)**

```python
# schema/products.py
from pydantic import BaseModel

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    in_stock: bool
```

**Step 2: Create the route**

```python
# routes/products.py
from typing import Annotated
from fastapi import APIRouter, Depends, Path

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: Annotated[str, Path()],
    repo: Annotated[ProductRepository, Depends(get_product_repo)],
) -> ProductResponse:
    product = await repo.get(product_id)
    if product is None:
        raise NotFoundError("Product", product_id)
    return ProductResponse.model_validate(product)
```

**Step 3: Create minimal repository**

```python
# repositories/products.py (single file is fine for simple cases)
from abc import ABC, abstractmethod

class ProductRepository(ABC):
    @abstractmethod
    async def get(self, product_id: str) -> Product | None: ...

class FakeProductRepository(ProductRepository):
    async def get(self, product_id: str) -> Product | None:
        # TODO: Replace with real implementation
        return None
```

**Step 4: Wire it up**

```python
# dependencies/products.py
def get_product_repo() -> ProductRepository:
    return FakeProductRepository()
```

```python
# main.py
from app.routes.products import router as products_router
app.include_router(products_router)
```

**That's it.** No service layer needed for a simple lookup. Total: 4 files touched.

---

### Complex Scenario: Add a Feature with Business Logic

**Contract says:**
- `POST /orders` — create order (must validate inventory, calculate totals)
- `GET /orders/{order_id}` — get order details
- `POST /orders/{order_id}/cancel` — cancel order (only if not shipped)

This has business logic (validation, calculations, state transitions), so use the full structure.

**Step 1: Analyze what you need**

- Business rules: inventory check, total calculation, cancellation rules
- Multiple endpoints sharing logic → needs a service
- Data storage → needs a repository

**Step 2: Start with schema (from the contract)**

```python
# schema/orders.py
from pydantic import BaseModel, Field
from decimal import Decimal

class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)

class CreateOrderRequest(BaseModel):
    items: list[OrderItemRequest] = Field(min_length=1)
    shipping_address: str

class OrderResponse(BaseModel):
    id: str
    status: str
    items: list[OrderItemResponse]
    total: Decimal
    created_at: datetime
```

**Step 3: Create domain models (internal representation)**

```python
# domain/orders.py
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"

class Order(BaseModel):
    id: str
    status: OrderStatus
    items: list[OrderItem]
    total: Decimal
    created_at: datetime

class OrderCreate(BaseModel):
    items: list[OrderItemCreate]
    shipping_address: str
```

**Step 4: Create repository interface**

```python
# repositories/orders/interface.py
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    async def get(self, order_id: str) -> Order | None: ...
    
    @abstractmethod
    async def create(self, order_id: str, data: OrderCreate) -> Order: ...
    
    @abstractmethod
    async def update_status(self, order_id: str, status: OrderStatus) -> Order | None: ...
```

**Step 5: Create service with business logic**

```python
# services/orders/service.py
class OrderService:
    def __init__(
        self,
        orders: OrderRepository,
        products: ProductRepository,  # Need to check inventory
    ) -> None:
        self.orders = orders
        self.products = products

    async def create_order(self, data: OrderCreate) -> Order:
        # Business logic: validate inventory
        for item in data.items:
            product = await self.products.get(item.product_id)
            if product is None:
                raise NotFoundError("Product", item.product_id)
            if product.stock < item.quantity:
                raise ValidationError(f"Insufficient stock for {product.name}")
        
        # Business logic: calculate total
        total = calculate_order_total(data.items, products)
        
        order_id = str(uuid.uuid4())
        return await self.orders.create(order_id, data, total)

    async def cancel_order(self, order_id: str) -> Order:
        order = await self.orders.get(order_id)
        if order is None:
            raise NotFoundError("Order", order_id)
        
        # Business logic: can only cancel if not shipped
        if order.status == OrderStatus.SHIPPED:
            raise ValidationError("Cannot cancel shipped order")
        
        return await self.orders.update_status(order_id, OrderStatus.CANCELLED)
```

```python
# services/orders/logic.py (pure functions)
def calculate_order_total(items: list[OrderItem], products: dict[str, Product]) -> Decimal:
    total = Decimal("0")
    for item in items:
        product = products[item.product_id]
        total += product.price * item.quantity
    return total
```

**Step 6: Create thin routes**

```python
# routes/orders.py
@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    request: CreateOrderRequest,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    data = OrderCreate(**request.model_dump())
    order = await service.create_order(data)
    return OrderResponse.model_validate(order)

@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: Annotated[str, Path()],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    order = await service.cancel_order(order_id)
    return OrderResponse.model_validate(order)
```

**Step 7: Wire dependencies and register router**

---

### Decision Checklist: Simple vs Complex

Before you start, ask yourself:

| Question | If Yes → |
|----------|----------|
| Is it just fetching/storing data with no rules? | Simple (skip service) |
| Are there business rules to enforce? | Complex (use service) |
| Do multiple endpoints share logic? | Complex (use service) |
| Does it need to coordinate multiple repositories? | Complex (use service) |
| Will the logic need unit testing in isolation? | Complex (use service + logic.py) |

**Start simple.** If you find yourself adding `if` statements and validation in the route, that's your signal to introduce a service.

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

## When to Skip Layers (Pragmatic Shortcuts)

The full architecture (domain → schema → repository → service → route → dependencies) is designed for complex features. **Not every feature needs all layers.** Here's when to simplify:

### Skip `logic.py` for Simple Services

Only create a separate `logic.py` when you have pure functions worth isolating (calculations, transformations, validation logic). For basic CRUD, just use `service.py`.

```
# Full structure (complex feature with business rules)
services/orders/
├── __init__.py
├── service.py      # Orchestration
└── logic.py        # Price calculations, discount rules, etc.

# Simplified (basic CRUD)
services/users/
├── __init__.py
└── service.py      # Everything here is fine
```

### Combine Domain and Schema When Identical

If your domain model and API schema have the same fields, you don't need both. The separation exists for when they diverge.

```python
# ❌ Unnecessary duplication
# domain/users.py
class User(BaseModel):
    id: str
    email: str
    name: str

# schema/users.py  
class UserResponse(BaseModel):  # Identical to domain model
    id: str
    email: str
    name: str

# ✅ Just use one (in schema/) and import it where needed
# schema/users.py
class User(BaseModel):
    id: str
    email: str
    name: str

class UserResponse(User):  # Or just use User directly as response
    pass
```

**When to separate them:**
- API uses different field names (`user_id` vs `id`)
- API excludes internal fields (`password_hash`, `internal_notes`)
- Different validation rules for API vs internal use

### Skip Service Layer for Trivial Endpoints

For simple read-only endpoints with no business logic, calling the repository directly from the route is acceptable.

```python
# ✅ OK for trivial cases - health check, simple lookups
@router.get("/config")
async def get_config(repo: Annotated[ConfigRepository, Depends(get_config_repo)]) -> ConfigResponse:
    config = await repo.get_current()
    return ConfigResponse.model_validate(config)

# ❌ Still use services when there's any logic
@router.get("/{item_id}")
async def get_item(item_id: str, repo: ItemRepository) -> ItemResponse:
    item = await repo.get(item_id)
    if item is None:  # This check belongs in a service
        raise HTTPException(404)
    return ItemResponse.model_validate(item)
```

### Decision Guide

| Situation | Recommendation |
|-----------|----------------|
| Simple CRUD, no business rules | Skip `logic.py`, consider skipping service |
| Domain model = API schema | Use one model, put in `schema/` |
| Complex calculations/validation | Use full structure with `logic.py` |
| Multiple consumers of same logic | Use full structure (services are reusable) |
| Need to swap storage backends | Always use repository interface |

**Remember:** Start simple, add layers when you feel the pain of not having them. It's easier to add structure than to remove it.

---

## FastAPI Parameter Types

Understanding when to use `Path`, `Query`, `Field`, `Body`, and `Header`.

### Quick Reference

| Data Location | FastAPI Type | Example URL/Body |
|---------------|--------------|------------------|
| URL path segment | `Path()` | `/items/{item_id}` |
| Query string | `Query()` | `/items?skip=0&limit=10` |
| Request body (JSON) | Pydantic model + `Field()` | `{"name": "Test"}` |
| HTTP headers | `Header()` | `X-Request-ID: abc123` |

### Path Parameters

Use for resource identifiers in the URL path.

```python
from fastapi import Path

@router.get("/{item_id}")
async def get_item(
    item_id: Annotated[str, Path(description="The item's unique identifier")],
) -> ItemResponse:
    ...

# With validation
@router.get("/{item_id}")
async def get_item(
    item_id: Annotated[str, Path(min_length=1, max_length=36)],
) -> ItemResponse:
    ...
```

### Query Parameters

Use for optional filters, pagination, sorting.

```python
from fastapi import Query

@router.get("")
async def list_items(
    skip: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
) -> ItemListResponse:
    ...
```

### Request Body (Pydantic Models)

Use `Field()` inside Pydantic models for body validation.

```python
from pydantic import BaseModel, Field

class CreateItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Item name")
    description: str | None = Field(default=None, max_length=1000)
    price: Decimal = Field(gt=0, description="Price must be positive")
    tags: list[str] = Field(default_factory=list, max_length=10)

@router.post("")
async def create_item(request: CreateItemRequest) -> ItemResponse:
    ...
```

### Headers

Use for metadata like authentication, request tracing.

```python
from fastapi import Header

@router.get("")
async def list_items(
    x_request_id: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> ItemListResponse:
    ...
```

### Common Patterns

```python
# Combining path + query + body
@router.patch("/{item_id}")
async def update_item(
    item_id: Annotated[str, Path()],                    # From URL path
    dry_run: Annotated[bool, Query()] = False,          # From query string
    request: UpdateItemRequest,                          # From JSON body
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    if dry_run:
        return await service.preview_update(item_id, request)
    return await service.update_item(item_id, request)
```

### When to Use What

| I want to... | Use |
|--------------|-----|
| Identify a specific resource | `Path()` — `/users/{user_id}` |
| Filter or paginate a list | `Query()` — `?status=active&page=2` |
| Send structured data to create/update | Pydantic model (body) |
| Send metadata about the request | `Header()` |
| Send a single value in the body | `Body()` — rarely needed |

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
