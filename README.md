# FastAPI Backend Template

A layered FastAPI backend template with testable architecture, using uv for package management.

## Features

- **Layered Architecture**: Domain models, Services, Repositories, Routes
- **Dependency Injection**: Swap real implementations for fakes in tests
- **Pydantic Everywhere**: Runtime validation at all layers (TypeScript-style)
- **Async PostgreSQL**: SQLAlchemy 2.0 with asyncpg
- **Alembic Migrations**: Async-compatible database migrations
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
│   ├── health.py        # Health check schemas
│   └── items.py         # Item request/response schemas
├── services/
│   └── items/
│       ├── service.py   # Business logic (orchestration)
│       └── logic.py     # Pure functions (calculations)
├── repositories/
│   └── items/
│       ├── interface.py # Abstract interface
│       ├── postgres.py  # PostgreSQL implementation
│       └── fake.py      # In-memory for testing
├── infrastructure/
│   ├── database.py      # SQLAlchemy async setup
│   ├── orm.py           # ORM models (separate from domain)
│   └── logging.py       # structlog configuration
└── routes/
    ├── health.py        # Health check endpoint
    └── items.py         # Example CRUD routes
```

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for PostgreSQL)

### Setup

1. **Create environment file**

```bash
# Create .env with these values:
ENV=local
DEBUG=true
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app
LOG_LEVEL=INFO
LOG_FORMAT=console
```

2. **Install dependencies**

```bash
uv sync
```

3. **Start PostgreSQL**

```bash
docker compose up -d db
```

4. **Run migrations**

```bash
uv run alembic revision --autogenerate -m "initial"
uv run alembic upgrade head
```

5. **Start the server**

```bash
uv run uvicorn app.main:app --reload
```

6. **Open API docs**: http://localhost:8000/docs

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the full developer guide.

### Quick Reference

| I need to... | Where |
|--------------|-------|
| Add API input/output models | `schema/` |
| Add internal business models | `domain/` |
| Add calculations/rules | `services/*/logic.py` |
| Coordinate operations | `services/*/service.py` |
| Read/write database | `repositories/` |
| Handle HTTP requests | `routes/` |

### Running with Docker

```bash
# Database only (run app locally)
docker compose up -d db

# Everything
docker compose up
```

### Migrations

```bash
# Generate migration
uv run alembic revision --autogenerate -m "description"

# Apply
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Environment (local, test, staging, production) | `local` |
| `DEBUG` | Enable debug mode | `false` |
| `DATABASE_URL` | PostgreSQL connection string | (required) |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (console, json) | `console` |

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

## Response Shape

Keep error responses consistent:

```json
{ "detail": "Human-readable message" }
```

For unexpected failures, the app returns `500` with `{ "detail": "Internal Server Error" }`.

## Production Checklist (minimal)

- Set `ENV=production` and `LOG_FORMAT=json`.
- Provide a strong `DATABASE_URL`.
- Review CORS and allowed hosts for your deployment environment.
- Run migrations before deploying.

## Cloud Run Logging

Cloud Run expects a `severity` field in JSON logs. This template maps `level`
to `severity` and adds a `message` field so ERROR logs show with the correct
severity in Cloud Logging.

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

## License

MIT
