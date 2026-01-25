# FastAPI Backend Template

A layered FastAPI backend template with testable architecture, using uv for package management.

## Features

- **Layered Architecture**: Domain models, Services, Repositories, Routes
- **Dependency Injection**: Swap real implementations for fakes in tests
- **Pydantic Everywhere**: Runtime validation at all layers (TypeScript-style)
- **PostgreSQL + Alembic**: Async database with migrations
- **Structured Logging**: JSON logs in production with structlog
- **Docker Ready**: Multi-stage Dockerfile + docker-compose

## Project Structure

```
src/app/
├── main.py              # FastAPI app entry point
├── config.py            # Pydantic Settings
├── dependencies.py      # DI wiring
├── domain/
│   └── items.py         # Pydantic domain models (internal)
├── schema/
│   └── items.py         # Item request/response schemas
├── services/
│   └── items/
│       ├── service.py   # Business logic (orchestration)
│       └── logic.py     # Pure functions (calculations)
├── repositories/
│   └── items/
│       ├── interface.py # Abstract interface
│       ├── postgres.py  # PostgreSQL implementation
│       └── fake.py      # In-memory (for tests)
├── infrastructure/
│   ├── database.py      # SQLAlchemy async setup
│   ├── orm.py           # ORM models
│   └── logging.py       # structlog configuration
└── routes/
    └── items.py         # CRUD routes
```

## Quick Start

### Option 1: With Docker

```bash
# Start app + database
docker compose up --build -d

# Run migrations to create tables
docker compose exec app alembic revision --autogenerate -m "initial"
docker compose exec app alembic upgrade head

# View logs
docker compose logs -f
```

Open http://localhost:8000/docs to use the API.

### Option 2: Local Development (without Docker)

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), PostgreSQL running locally

```bash
# Install dependencies
uv sync

# Create .env file
echo "DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app" > .env

# Run migrations
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head

# Start server
uv run uvicorn app.main:app --reload
```

## Database Migrations

This template uses **Alembic** to manage database schema changes.

### Why Migrations?

When you use a real database, tables don't create themselves. Migrations:
1. Generate SQL to create/modify tables based on your ORM models
2. Track which changes have been applied
3. Allow rolling back changes if needed

### Common Commands

```bash
# Generate a new migration (after changing ORM models)
alembic revision --autogenerate -m "description of change"

# Apply all pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

With Docker, prefix commands with `docker compose exec app`:
```bash
docker compose exec app alembic upgrade head
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Environment (local, test, staging, production) | `local` |
| `DEBUG` | Enable debug mode | `false` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/app` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (console, json) | `console` |

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the full developer guide.

### Quick Reference

| I need to... | Where |
|--------------|-------|
| Add API input/output models | `schema/` |
| Add internal business models | `domain/` |
| Add calculations/rules | `services/*/logic.py` |
| Coordinate operations | `services/*/service.py` |
| Add database table | `infrastructure/orm.py` + migration |
| Read/write data | `repositories/` |
| Handle HTTP requests | `routes/` |

### Adding a Feature

1. **Domain model** → `domain/your_feature.py`
2. **API schemas** → `schema/your_feature.py`
3. **Repository** → `repositories/your_feature/`
4. **Service** → `services/your_feature/`
5. **Routes** → `routes/your_feature.py`
6. **Wire it up** → `dependencies.py` and `main.py`
7. **Migration** → `uv run alembic revision --autogenerate -m "add your_feature"`

## Architecture

```
Request → Schema → Service → Domain → Repository → Database
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
| **Infrastructure** | Database, logging, external clients |

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
- Use a managed PostgreSQL instance
- Run `alembic upgrade head` before deploying new code
- Review CORS and allowed hosts

## License

MIT
