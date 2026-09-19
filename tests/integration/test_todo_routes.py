"""Integration tests for todo routes."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.database.config import get_session
from app.main import app


@pytest.fixture
def client(session: Session) -> TestClient:
    """Create test client with in-memory database."""

    def get_session_override() -> Session:
        return session

    app.dependency_overrides[get_session] = get_session_override
    return TestClient(app)


def test_create_todo(client: TestClient) -> None:  # pylint: disable=redefined-outer-name
    """Test POST /todos endpoint."""
    response = client.post("/todos", json={"title": "Test Task", "description": "Test Desc"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["id"] is not None


def test_get_all_todos(client: TestClient) -> None:  # pylint: disable=redefined-outer-name
    """Test GET /todos endpoint."""
    client.post("/todos", json={"title": "Task 1"})
    client.post("/todos", json={"title": "Task 2"})

    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_todo_by_id(client: TestClient) -> None:  # pylint: disable=redefined-outer-name
    """Test GET /todos/{id} endpoint."""
    create_response = client.post("/todos", json={"title": "Task"})
    todo_id = create_response.json()["id"]

    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Task"


def test_update_todo(client: TestClient) -> None:  # pylint: disable=redefined-outer-name
    """Test PATCH /todos/{id} endpoint."""
    create_response = client.post("/todos", json={"title": "Old"})
    todo_id = create_response.json()["id"]

    response = client.patch(f"/todos/{todo_id}", json={"title": "Updated", "completed": True})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["completed"] is True


def test_delete_todo(client: TestClient) -> None:  # pylint: disable=redefined-outer-name
    """Test DELETE /todos/{id} endpoint."""
    create_response = client.post("/todos", json={"title": "Task"})
    todo_id = create_response.json()["id"]

    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204

    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404


def test_create_todo_missing_title(client: TestClient) -> None:  # pylint: disable=redefined-outer-name
    """Test creating todo without title returns 422."""
    response = client.post("/todos", json={"description": "No title"})
    assert response.status_code == 422
