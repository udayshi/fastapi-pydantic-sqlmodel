"""Integration tests for Redis-backed sessions."""

from collections.abc import Mapping

import pytest
from fastapi.testclient import TestClient

from app.main import app


class MemorySessionStore:
    """In-memory implementation for route tests."""

    def __init__(self) -> None:
        self.data: dict[str, dict[str, int | str | bool]] = {}

    def load(self, session_id: str) -> dict[str, int | str | bool] | None:
        """Load a session."""
        return self.data.get(session_id)

    def save(self, session_id: str, data: Mapping[str, int | str | bool]) -> None:
        """Save a session."""
        self.data[session_id] = dict(data)

    def delete(self, session_id: str) -> None:
        """Delete a session."""
        self.data.pop(session_id, None)


@pytest.fixture
def client() -> TestClient:
    """Return a client using an in-memory session store."""
    app.state.session_store = MemorySessionStore()
    with TestClient(app) as test_client:
        yield test_client
    del app.state.session_store


def test_session_counter_is_preserved_for_the_same_client(client: TestClient) -> None:
    """A session is created once and restored from its cookie."""
    assert client.get("/session").json() == {"visits": 1}
    assert client.get("/session").json() == {"visits": 2}


def test_tampered_session_cookie_starts_a_new_session(client: TestClient) -> None:
    """An invalid signed cookie cannot select another user's session."""
    client.cookies.set("todo_session", "not-a-valid-signature")

    response = client.get("/session")

    assert response.status_code == 200
    assert response.json() == {"visits": 1}