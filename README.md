# TDD FastAPI SQLModel Todo API

A small Todo API built with FastAPI, SQLModel, PostgreSQL, and a test-driven development workflow. The repository is
organised as a working application plus step-by-step implementation guides.

## Documentation

- [Build the Todo API with TDD](docs/tdd-fastapi.md) — project setup, database configuration, models, schemas,
  repositories, routes, testing, and quality checks.
- [Redis-backed sessions with TDD](docs/redis-session.md) — a test-first plan for secure, server-side Redis sessions.

## Requirements

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL for local development and production

The test suite uses in-memory SQLite, so PostgreSQL is not required to run tests.

## Quick start

Install the locked project dependencies:

```bash
uv sync
```

Set a PostgreSQL password in your current shell without adding it to a file:

```bash
printf "PostgreSQL password: "
read -r -s POSTGRES_PASSWORD
printf "\n"
export POSTGRES_PASSWORD
```

Create `.env` with your local connection details:

```dotenv
POSTGRES_USER=user
POSTGRES_DB=todo_db
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}
TEST_DATABASE_URL=sqlite:///:memory:
LOG_LEVEL=INFO
```

For a local PostgreSQL container, see the [database setup section](docs/tdd-fastapi.md#step-21-setup-postgresql-development)
of the TDD guide. Keep `.env` and secrets out of version control.

## Run the API

```bash
uv run uvicorn app.main:app --reload
```

The API is served at `http://127.0.0.1:8000`. Check it with:

```bash
curl http://127.0.0.1:8000/health
```

Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` while the server is running.

## Test and quality commands

```bash
uv run pytest
make test
make test-unit
make test-integration
make lint
make format
```

`make test` runs the unit and integration suites. The detailed TDD guide explains the tests and implementation sequence.

## API overview

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health check |
| `POST` | `/todos` | Create a todo |
| `GET` | `/todos` | List todos |
| `GET` | `/todos/{todo_id}` | Get one todo |
| `PATCH` | `/todos/{todo_id}` | Update a todo |
| `DELETE` | `/todos/{todo_id}` | Delete a todo |

Redis sessions are documented but are not enabled in the application yet. Follow the
[Redis session guide](docs/redis-session.md) to add them test-first.
