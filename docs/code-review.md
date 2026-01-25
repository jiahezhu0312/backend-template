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

---

## Review Checklist

### Routes

- [ ] Routes are thin - just call service and return response
- [ ] No business logic in routes
- [ ] Uses `Annotated[..., Depends()]` for dependency injection
- [ ] Returns proper status codes (201 for create, 204 for delete)

```python
# ✅ Good
@router.get("/{item_id}")
async def get_item(
    item_id: str,
    service: Annotated[ItemService, Depends(get_item_service)],
) -> ItemResponse:
    item = await service.get_item(item_id)
    return ItemResponse.model_validate(item)

# ❌ Bad - logic in route
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
- [ ] Contains all business logic
- [ ] Pure functions in `logic.py`, orchestration in `service.py`

```python
# ✅ Good - interface dependency
def __init__(self, items: ItemRepository):
    self.items = items

# ❌ Bad - concrete implementation
def __init__(self, items: FakeItemRepository):
    self.items = items
```

### Exceptions

- [ ] Services raise domain exceptions from `services/exceptions.py`
- [ ] No `HTTPException` in services
- [ ] Exceptions let the handlers convert to HTTP responses

```python
# ✅ Good
if item is None:
    raise NotFoundError("Item", item_id)

# ❌ Bad
if item is None:
    raise HTTPException(status_code=404, detail="Not found")
```

### Repositories

- [ ] One repository per domain entity
- [ ] Interface defines the contract (`interface.py`)
- [ ] Implementation in separate file (`fake.py`, `postgres.py`, etc.)
- [ ] Methods return domain models, not raw dicts

### Typing

- [ ] All functions have return type annotations
- [ ] Uses modern syntax: `str | None` not `Optional[str]`
- [ ] Uses `list[Item]` not `List[Item]`
- [ ] `__init__` returns `-> None`

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
- [ ] No sensitive data logged (passwords, tokens, etc.)

```python
# ✅ Good
logger.info("item_created", item_id=item.id, name=item.name)

# ❌ Bad
logger.info(f"Created item {item.id}")
```

---

## Common Issues to Catch

| Issue | What to Look For |
|-------|------------------|
| Logic in routes | If/else, calculations, loops in route handlers |
| Concrete dependencies | Service depending on `FakeRepo` instead of `RepoInterface` |
| Missing types | Functions without return types, untyped parameters |
| HTTPException in services | Should use domain exceptions |
| String logging | `f"..."` instead of keyword args |
| Old type syntax | `Optional`, `List`, `Dict` from typing |

---

## File Locations Quick Reference

| Adding... | Location |
|-----------|----------|
| API input/output models | `schema/` |
| Internal business models | `domain/` |
| Business rules/calculations | `services/*/logic.py` |
| Operation coordination | `services/*/service.py` |
| Data access | `repositories/` |
| HTTP endpoints | `routes/` |
| Domain exceptions | `services/exceptions.py` |
| Dependency wiring | `dependencies/` |

---

## Questions to Ask During Review

1. **Is this in the right layer?** Logic should be in services, not routes.
2. **Is it testable?** Services should work with any repository implementation.
3. **Are types complete?** Every function should have return types.
4. **Will this scale?** Repository pattern allows swapping storage backends.
5. **Is logging useful?** Structured logs with context, not string messages.
