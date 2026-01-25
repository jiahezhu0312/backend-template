# Code Review Guide

A quick reference for reviewing code in this project.

## Architecture Overview

```
Request → Route → Service → Repository → Storage
              ↓         ↓
           Schema    Domain
```

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Routes | `routes/` | HTTP handling only (thin) |
| Schema | `schema/` | API request/response models |
| Services | `services/` | Business logic |
| Domain | `domain/` | Internal data models |
| Repositories | `repositories/` | Data access |

**Note:** Not every feature needs all layers. See [When to Skip Layers](#when-its-ok-to-skip-layers).

---

## Review Checklist

### Routes

- [ ] Routes are thin - call service/repo and return response
- [ ] No business logic in routes (calculations, complex conditionals)
- [ ] Uses `Annotated[..., Depends()]` for dependency injection
- [ ] Returns proper status codes (201 for create, 204 for delete)
- [ ] Path/Query/Field used correctly (see [Parameter Types](#parameter-types))

```python
# ✅ Good - thin route with service
@router.get("/{item_id}")
async def get_item(
    item_id: Annotated[str, Path()],
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    item = await service.get_item(item_id)
    return ItemResponse.model_validate(item)

# ✅ Also OK - simple lookup without service (no business logic)
@router.get("/{product_id}")
async def get_product(
    product_id: Annotated[str, Path()],
    repo: Annotated[ProductRepository, Depends(get_product_repo)],
) -> ProductResponse:
    product = await repo.get(product_id)
    if product is None:
        raise NotFoundError("Product", product_id)
    return ProductResponse.model_validate(product)

# ❌ Bad - business logic in route
@router.get("/{item_id}")
async def get_item(item_id: str, repo: ItemRepository):
    item = await repo.get(item_id)
    if item.price > 100:  # Business logic doesn't belong here
        item.discount = 0.1
    return item
```

### Services

- [ ] Depends on repository **interfaces** (not implementations)
- [ ] Raises domain exceptions (not HTTPException)
- [ ] Contains business logic (validation, calculations, orchestration)
- [ ] `logic.py` only needed if there are pure functions worth isolating

```python
# ✅ Good - interface dependency
def __init__(self, items: ItemRepository):
    self.items = items

# ❌ Bad - concrete implementation
def __init__(self, items: FakeItemRepository):
    self.items = items
```

### Exceptions

- [ ] Services raise domain exceptions from `app/exceptions.py`
- [ ] No `HTTPException` in services
- [ ] Routes let exceptions propagate (handlers convert to HTTP)

```python
# ✅ Good
if item is None:
    raise NotFoundError("Item", item_id)

# ❌ Bad
if item is None:
    raise HTTPException(status_code=404, detail="Not found")
```

### Repositories

- [ ] Interface defines the contract
- [ ] Methods return domain models, not raw dicts
- [ ] Single file OK for simple cases, folder for complex

### Typing

- [ ] All functions have return type annotations
- [ ] Uses modern syntax: `str | None` not `Optional[str]`
- [ ] Uses `list[Item]` not `List[Item]`

```python
# ✅ Good
async def get_item(self, item_id: str) -> Item | None:
    ...

# ❌ Bad
async def get_item(self, item_id: str):  # Missing return type
    ...
```

### Logging

- [ ] Uses structured logging with keyword arguments
- [ ] Event names are snake_case
- [ ] Logs in services, not routes
- [ ] No sensitive data logged

```python
# ✅ Good
logger.info("item_created", item_id=item.id, name=item.name)

# ❌ Bad
logger.info(f"Created item {item.id}")
```

---

## Parameter Types

Quick reference for FastAPI parameters:

| Data Location | Use | Example |
|---------------|-----|---------|
| URL path `/items/{id}` | `Path()` | `item_id: Annotated[str, Path()]` |
| Query string `?skip=0` | `Query()` | `skip: Annotated[int, Query(ge=0)] = 0` |
| JSON body | Pydantic model + `Field()` | `name: str = Field(min_length=1)` |
| HTTP headers | `Header()` | `x_request_id: Annotated[str, Header()]` |

```python
# Example combining multiple parameter types
@router.patch("/{item_id}")
async def update_item(
    item_id: Annotated[str, Path()],           # URL path
    dry_run: Annotated[bool, Query()] = False, # Query string
    request: UpdateItemRequest,                 # JSON body
) -> ItemResponse:
    ...
```

---

## When It's OK to Skip Layers

Not every feature needs the full architecture. Use judgment:

| Scenario | Recommendation |
|----------|----------------|
| Simple CRUD, no business rules | Skip service, call repo from route |
| Domain model = API schema | Use one model in `schema/` |
| No pure functions to isolate | Skip `logic.py` |
| Complex validation/calculations | Use full structure |
| Multiple endpoints share logic | Use service |

**Signal to add a service:** If you're adding `if` statements with business logic in a route, move it to a service.

---

## Common Issues to Catch

| Issue | What to Look For |
|-------|------------------|
| Logic in routes | Calculations, complex conditionals, loops |
| Concrete dependencies | Service depending on `FakeRepo` instead of `RepoInterface` |
| Missing types | Functions without return types |
| HTTPException in services | Should use domain exceptions |
| String logging | `f"..."` instead of keyword args |
| Wrong parameter type | Using `Query()` for path segment, `Field()` in route |

---

## Questions to Ask During Review

1. **Is this the right complexity?** Simple feature with full architecture? Complex feature without service?
2. **Is it testable?** Services should work with any repository implementation.
3. **Are types complete?** Every function should have return types.
4. **Is the parameter type correct?** Path for URL segments, Query for filters, Field for body.
5. **Is logging useful?** Structured logs with context, not string messages.

---

## What NOT to Nitpick

These are style preferences, not correctness issues. Don't block PRs over them:

- `...` vs `pass` in abstract methods
- Minor naming variations that are still clear
- Import ordering (let tooling handle it)
- Whitespace/formatting (let tooling handle it)

Focus reviews on architecture, correctness, and maintainability.
