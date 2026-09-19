"""Unit tests for Todo schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate


def test_todo_create_schema() -> None:
    """Test TodoCreate schema validation."""
    todo = TodoCreate(title="New Task", description="Task Description")
    assert todo.title == "New Task"
    assert todo.description == "Task Description"


def test_todo_create_requires_title() -> None:
    """Test TodoCreate requires non-empty title."""
    with pytest.raises(ValidationError):
        TodoCreate(title="")


def test_todo_create_rejects_whitespace_only() -> None:
    """Test TodoCreate rejects whitespace-only title."""
    with pytest.raises(ValidationError):
        TodoCreate(title="   ")


def test_todo_create_strips_whitespace() -> None:
    """Test TodoCreate strips whitespace from title."""
    todo = TodoCreate(title="  Task  ")
    assert todo.title == "Task"


def test_todo_update_schema() -> None:
    """Test TodoUpdate schema."""
    todo = TodoUpdate(title="Updated", completed=True)
    assert todo.title == "Updated"
    assert todo.completed is True


def test_todo_update_allows_none() -> None:
    """Test TodoUpdate allows None values."""
    todo = TodoUpdate()
    assert todo.title is None
    assert todo.description is None
    assert todo.completed is None


def test_todo_response_schema() -> None:
    """Test TodoResponse schema."""
    todo = Todo(
        id=1,
        title="Task",
        description="Desc",
        completed=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    response = TodoResponse.model_validate(todo)
    assert response.id == 1
    assert response.title == "Task"
