.PHONY: help install setup test test-unit test-integration run dev db-create db-drop db-reset lint format clean

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make setup            - Setup project (install + database setup)"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make run              - Run production server"
	@echo "  make dev              - Run development server with reload"
	@echo "  make db-create        - Create database"
	@echo "  make db-drop          - Drop database"
	@echo "  make db-reset         - Reset database"
	@echo "  make lint             - Lint code"
	@echo "  make format           - Format code"
	@echo "  make clean            - Clean up cache files"

install:
	uv pip install -r requirements.txt

setup: install db-reset
	@echo "Project setup complete!"

test: test-unit test-integration
	@echo "All tests passed!"

test-unit:
	uv run pytest tests/unit -v

test-integration:
	uv run pytest tests/integration -v

run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

db-create:
	@echo "Creating database..."
	createdb todo_db 2>/dev/null || true

db-drop:
	@echo "Dropping database..."
	dropdb todo_db 2>/dev/null || true

db-reset: db-drop db-create
	@echo "Database reset complete!"

lint:
	uv run pylint app tests

format:
	uv run black app tests
	uv run isort app tests

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	rm -rf .coverage htmlcov
