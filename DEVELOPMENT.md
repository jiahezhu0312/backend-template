# Developer Guide

A quick guide to writing code that follows this architecture.

## Project Structure

```
src/app/
├── domain/         # Business models (Pydantic)
├── schema/         # API request/response models (Pydantic)
├── repositories/   # Data access (interface + implementations)
├── services/       # Business logic
├── routes/         # HTTP endpoints (thin)
└── infrastructure/ # Database, logging, external clients
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

# postgres.py
class PostgresUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    # ... implement methods

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

Add to `src/app/dependencies.py`:

```python
async def get_user_repository(...) -> UserRepository:
    ...

async def get_user_service(...) -> UserService:
    ...
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
async def get_item(id: str, db: Session):
    item = db.query(Item).filter_by(id=id).first()
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
    def __init__(self, items: PostgresItemRepository):  # Concrete type
        self.items = items
```

### Pure Functions (logic.py)

```python
# ✅ DO: Input → Output, no side effects
def calculate_discount(price: Decimal, quantity: int) -> Decimal:
    if quantity >= 10:
        return price * Decimal("0.1")
    return Decimal("0")

# ❌ DON'T: Access database or external services
def calculate_discount(price: Decimal, db: Session) -> Decimal:
    settings = db.query(Settings).first()  # Side effect!
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
| Read/write database | `repositories/` |
| Handle HTTP | `routes/` |

---

## Testing Strategy

| What to test | How |
|--------------|-----|
| Pure functions | Direct call, no setup |
| Services | Inject `FakeRepository` |
| Routes | `TestClient` + fake dependencies |
| Repositories | Integration test with real DB |

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

### Database transactions

Handled automatically by `get_db_session()` - commits on success, rollbacks on error.

---

## Checklist for New Features

- [ ] Domain model in `domain/`
- [ ] Schema in `schema/`
- [ ] Repository interface + implementations in `repositories/`
- [ ] Service in `services/`
- [ ] Route in `routes/`
- [ ] Dependencies wired in `dependencies.py`
- [ ] Router registered in `main.py`
- [ ] ORM model in `infrastructure/orm.py` (if new table)
- [ ] Migration created with `alembic revision --autogenerate`
