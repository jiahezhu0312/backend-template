# AI Code Generation Prompt

Use this prompt when asking an AI to generate code from an OpenAPI specification.

---

## Prompt Template

Copy everything below the line and paste it along with your OpenAPI spec:

---

You are generating Python code for a FastAPI backend following a layered architecture. Generate code that follows these patterns exactly.

## Architecture Layers

```
Request → Route → Service → Repository → Storage
              ↓         ↓
           Schema    Domain
```

## File Structure

```
src/app/
├── schema/{feature}.py      # API request/response models (from OpenAPI)
├── domain/{feature}.py      # Internal business models (if different from schema)
├── repositories/{feature}/
│   ├── interface.py         # Abstract repository
│   └── fake.py              # In-memory implementation
├── services/{feature}/
│   ├── service.py           # Business logic orchestration
│   └── logic.py             # Pure functions (only if needed)
├── routes/{feature}.py      # HTTP endpoints
├── dependencies/{feature}.py # Dependency injection wiring
└── main.py                  # Register router here
```

## Import Convention

Always use direct imports, never package-level imports:

```python
# ✅ Correct
from app.services.orders.service import OrderService
from app.repositories.orders.interface import OrderRepository
from app.dependencies.orders import get_order_service

# ❌ Wrong - no __init__.py re-exports
from app.services import OrderService
```

## Generation Rules

### 1. Schema (generate first)

Create Pydantic models matching OpenAPI schemas exactly:

```python
# schema/{feature}.py
from pydantic import BaseModel, Field

class CreateOrderRequest(BaseModel):
    """Maps to OpenAPI requestBody schema."""
    items: list[OrderItemRequest] = Field(min_length=1)
    shipping_address: str = Field(min_length=1, max_length=500)

class OrderResponse(BaseModel):
    """Maps to OpenAPI response schema."""
    id: str
    status: str
    total: Decimal
    created_at: datetime
```

### 2. Routes (generate second)

Thin handlers that delegate to service/repository:

```python
# routes/{feature}.py
from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status

from app.schema.orders import CreateOrderRequest, OrderResponse
from app.dependencies.orders import get_order_service
from app.services.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    """Docstring from OpenAPI description."""
    order = await service.create_order(request)
    return OrderResponse.model_validate(order)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: Annotated[str, Path(description="Order ID")],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    order = await service.get_order(order_id)
    return OrderResponse.model_validate(order)
```

### 3. Parameter Types

| OpenAPI Location | FastAPI Type |
|------------------|--------------|
| path parameters | `Annotated[str, Path()]` |
| query parameters | `Annotated[int, Query(ge=0)] = 0` |
| requestBody | Pydantic model as parameter |
| headers | `Annotated[str, Header()]` |

### 4. Repository Interface (generate third)

Define abstract methods for data operations:

```python
# repositories/{feature}/interface.py
from abc import ABC, abstractmethod
from app.domain.orders import Order, OrderCreate

class OrderRepository(ABC):
    @abstractmethod
    async def get(self, order_id: str) -> Order | None:
        ...
    
    @abstractmethod
    async def create(self, order_id: str, data: OrderCreate) -> Order:
        ...
    
    @abstractmethod
    async def list(self, *, skip: int = 0, limit: int = 100) -> list[Order]:
        ...
```

### 5. Fake Repository (generate fourth)

In-memory implementation for development/testing:

```python
# repositories/{feature}/fake.py
from app.domain.orders import Order, OrderCreate
from app.repositories.orders.interface import OrderRepository

class FakeOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
    
    async def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)
    
    async def create(self, order_id: str, data: OrderCreate) -> Order:
        order = Order(id=order_id, **data.model_dump())
        self._orders[order_id] = order
        return order
```

### 6. Service (generate fifth)

Only create if there's business logic. Otherwise, route can use repository directly.

```python
# services/{feature}/service.py
import uuid
from app.domain.orders import Order, OrderCreate
from app.repositories.orders.interface import OrderRepository
from app.exceptions import NotFoundError

class OrderService:
    def __init__(self, orders: OrderRepository) -> None:
        self.orders = orders
    
    async def get_order(self, order_id: str) -> Order:
        order = await self.orders.get(order_id)
        if order is None:
            raise NotFoundError("Order", order_id)
        return order
    
    async def create_order(self, data: OrderCreate) -> Order:
        order_id = str(uuid.uuid4())
        # TODO: Add business logic here
        return await self.orders.create(order_id, data)
```

### 7. Dependencies (generate sixth)

Wire up repository and service:

```python
# dependencies/{feature}.py
from typing import Annotated
from fastapi import Depends
from app.config import Settings, get_settings
from app.repositories.orders.interface import OrderRepository
from app.repositories.orders.fake import FakeOrderRepository
from app.services.orders.service import OrderService

_fake_repo: FakeOrderRepository | None = None

def get_order_repository(settings: Annotated[Settings, Depends(get_settings)]) -> OrderRepository:
    global _fake_repo
    if _fake_repo is None:
        _fake_repo = FakeOrderRepository()
    return _fake_repo

async def get_order_service(
    repo: Annotated[OrderRepository, Depends(get_order_repository)],
) -> OrderService:
    return OrderService(orders=repo)
```

### 8. Register Router (add to main.py)

```python
from app.routes.orders import router as orders_router
app.include_router(orders_router)
```

## Decision: Simple vs Complex

**Simple (skip service layer):**
- GET endpoints that just fetch data
- No business rules or validation beyond schema
- Single repository operation

**Complex (use service layer):**
- POST/PUT/PATCH with business rules
- Operations involving multiple repositories
- Calculations, state transitions, validation logic

## Exceptions

Use domain exceptions, not HTTPException:

```python
from app.exceptions import NotFoundError, ValidationError, ConflictError

# In service
if order is None:
    raise NotFoundError("Order", order_id)

if order.status == "shipped":
    raise ValidationError("Cannot modify shipped order")
```

## What to Generate

Given an OpenAPI spec, generate in this order:

1. **Schema models** - All request/response types from OpenAPI schemas
2. **Route handlers** - All endpoints from OpenAPI paths
3. **Repository interface** - Infer CRUD operations from endpoints
4. **Fake repository** - In-memory implementation
5. **Service class** - Only if endpoints have business logic (mark TODO for actual logic)
6. **Dependencies** - Wiring for repository and service
7. **Router registration** - Line to add to main.py

Mark any business logic with `# TODO: Add business logic` comments since OpenAPI doesn't specify implementation details.

---

## OpenAPI Spec

[PASTE YOUR OPENAPI SPEC HERE]

---

## Additional Context (optional)

[DESCRIBE ANY BUSINESS RULES OR COMPLEXITY NOT IN THE SPEC]

- Feature complexity: simple / complex
- Business rules: (list any rules)
- Needs separate domain models: yes / no
