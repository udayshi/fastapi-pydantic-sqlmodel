"""Unit tests for Todo model."""

from sqlmodel import Session

from app.models.todo import Todo


def test_todo_creation(session: Session) -> None:  # pylint: disable=redefined-outer-name
    """Test creating a todo."""
    todo = Todo(title="Test Task", description="Test Description", completed=False)
    session.add(todo)
    session.commit()
    session.refresh(todo)

    assert todo.id is not None
    assert todo.title == "Test Task"
    assert todo.description == "Test Description"
    assert todo.completed is False


def test_todo_required_fields(session: Session) -> None:  # pylint: disable=redefined-outer-name
    """Test todo requires title field."""
    todo = Todo(title="Task", completed=False)
    session.add(todo)
    session.commit()
    session.refresh(todo)

    assert todo.title == "Task"
    assert todo.description is None


def test_todo_completion_toggle() -> None:  # pylint: disable=redefined-outer-name
    """Test toggling todo completion status."""
    todo = Todo(title="Task", completed=False)
    assert todo.completed is False

    todo.completed = True
    assert todo.completed is True
