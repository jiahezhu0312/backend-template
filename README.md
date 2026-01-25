# FastAPI Backend Template

A layered FastAPI backend template with testable architecture, using uv for package management.

## Features

- **Layered Architecture**: Domain models, Services, Repositories, Routes
- **Dependency Injection**: Swap implementations easily (in-memory, PostgreSQL, Firestore, etc.)
- **Pydantic Everywhere**: Runtime validation at all layers
- **Storage Agnostic**: Repository pattern lets you plug in any backend
- **Structured Logging**: JSON logs in production with structlog

## Project Structure

```
src/app/
├── main.py              # FastAPI app entry point
├── config.py            # Pydantic Settings
├── dependencies/        # DI wiring (per-feature)
│   └── items.py
├── domain/
│   └── items.py         # Pydantic domain models (internal)
├── schema/
│   └── items.py         # API request/response schemas
├── services/
│   └── items/
│       ├── service.py   # Business logic (orchestration)
│       └── logic.py     # Pure functions (calculations)
├── repositories/
│   └── items/
│       ├── interface.py # Abstract interface
│       └── fake.py      # In-memory implementation
├── infrastructure/
│   └── logging.py       # structlog configuration
└── routes/
    └── items.py         # CRUD routes
```

## Quick Start

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
# Install dependencies (including dev tools like pytest, ruff, pyright)
uv sync --extra dev

# Start server
uv run uvicorn app.main:app --reload

# Or use make
make install  # Install dependencies
make dev      # Start dev server
```

Open http://localhost:8000/docs to use the API.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Environment (local, test, staging, production) | `local` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (console, json) | `console` |
| `CORS_ORIGINS` | Comma-separated allowed origins | (empty) |

## Documentation

- [Developer Guide](docs/development.md) — architecture, patterns, and conventions
- [Code Review Guide](docs/code-review.md) — checklist for reviewers

### Quick Reference

| I need to... | Where |
|--------------|-------|
| Add API input/output models | `schema/` |
| Add internal business models | `domain/` |
| Add calculations/rules | `services/*/logic.py` |
| Coordinate operations | `services/*/service.py` |
| Read/write data | `repositories/` |
| Handle HTTP requests | `routes/` |

### Adding a Feature

1. **Domain model** → `domain/your_feature.py`
2. **API schemas** → `schema/your_feature.py`
3. **Repository interface** → `repositories/your_feature/interface.py`
4. **Repository implementation** → `repositories/your_feature/fake.py` (or your storage backend)
5. **Service** → `services/your_feature/`
6. **Routes** → `routes/your_feature.py`
7. **Wire it up** → `dependencies/your_feature.py` and `main.py`

### Adding a Real Database

The template uses an in-memory repository by default. To add a real database:

1. Add dependencies (e.g., `sqlalchemy`, `asyncpg` for PostgreSQL)
2. Create a new repository implementation (e.g., `PostgresItemRepository`)
3. Update `dependencies.py` to return the real implementation based on settings
4. Add database URL to config if needed

The repository pattern makes this swap straightforward—your services don't change.

## Architecture

```
Request → Schema → Service → Domain → Repository → Storage
                      ↓
Response ← Schema ← Service
```

| Layer | Purpose |
|-------|---------|
| **Routes** | HTTP handling (thin) |
| **Schema** | API request/response validation |
| **Services** | Business logic + orchestration |
| **Domain** | Internal business models |
| **Repositories** | Data access abstraction |
| **Infrastructure** | Logging, external clients |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root |
| GET | `/health` | Health check |
| GET | `/items` | List items |
| GET | `/items/{id}` | Get item |
| POST | `/items` | Create item |
| PATCH | `/items/{id}` | Update item |
| DELETE | `/items/{id}` | Delete item |

## Production Checklist

- Set `ENV=production` and `LOG_FORMAT=json`
- Configure your storage backend (CloudSQL, Firestore, etc.)
- Review CORS and allowed hosts

## License

MIT
