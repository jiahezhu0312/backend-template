.PHONY: install dev lint typecheck clean

# Setup
install:
	uv sync --extra dev

# Development
dev:
	uv run uvicorn app.main:app --reload

# Code quality
lint:
	uv run ruff check .

typecheck:
	uv run pyright

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
