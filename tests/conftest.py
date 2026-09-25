"""Shared pytest fixtures for all tests."""

import os
from collections.abc import Generator, Mapping

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from dotenv import  load_dotenv
load_dotenv()

# This must be set before pytest imports application modules. `load_dotenv()` does
# not overwrite an existing environment variable, so the test suite never opens
# the PostgreSQL connection configured in the developer's `.env` file.
os.environ["DATABASE_URL"] = "sqlite://"
#os.environ["SESSION_SECRET"] = "test-session-secret"


class MemorySessionStore:
    """In-memory session persistence shared by tests without Redis."""

    def __init__(self) -> None:
        self.data: dict[str, dict[str, int | str | bool]] = {}

    def load(self, session_id: str) -> dict[str, int | str | bool] | None:
        """Load a session by identifier."""
        return self.data.get(session_id)

    def save(self, session_id: str, data: Mapping[str, int | str | bool]) -> None:
        """Save a session by identifier."""
        self.data[session_id] = dict(data)

    def delete(self, session_id: str) -> None:
        """Delete a session by identifier."""
        self.data.pop(session_id, None)


@pytest.fixture(autouse=True)
def session_store() -> Generator[None, None, None]:
    """Configure an in-memory session store for every test."""
    from app.main import app

    app.state.session_store = MemorySessionStore()
    yield
    if hasattr(app.state, "session_store"):
        del app.state.session_store


@pytest.fixture
def session() -> Session:
    """Create in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session_instance:
        yield session_instance
