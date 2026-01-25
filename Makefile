.PHONY: dev dev-down dev-logs db-shell migrate migrate-new lint typecheck format clean

# Development
dev:
	docker compose up -d

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f app

db-shell:
	docker compose exec db psql -U postgres -d app

# Database migrations
migrate:
	docker compose exec app alembic upgrade head

migrate-new:
	@read -p "Migration message: " msg; \
	docker compose exec app alembic revision --autogenerate -m "$$msg"

# Code quality (optional - not enforced)
lint:
	uv run ruff check .

typecheck:
	uv run pyright

# Cleanup
clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
