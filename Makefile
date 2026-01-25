.PHONY: dev dev-down dev-logs lint typecheck clean

# Development
dev:
	docker compose up -d

dev-down:
	docker compose down

dev-logs:
	docker compose logs -f app

# Code quality
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
