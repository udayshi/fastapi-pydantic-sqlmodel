"""Unit tests for Todo repository."""

from sqlmodel import Session

from app.database.repository import TodoRepository


def test_create_todo(session: Session) -> None:  # pylint: disable=redefined-outer-name
    """Test creating a todo via repository."""
    repo = TodoRepository(session)
    todo = repo.create(title="Test", description="Desc")

    assert todo.id is not None
    assert todo.title == "Test"


def test_get_todo_by_id(session: Session) -> None:  # pylint: disable=redefined-outer-name
    """Test retrieving todo by ID."""
    repo = TodoRepository(session)
    created_todo = repo.create(title="Task", description="Desc")

    retrieved = repo.get_by_id(created_todo.id)
    assert retrieved is not None
    assert retrieved.title == "Task"


def test_list_todos(session: Session) -> None:  # pylint: disable=redefined-outer-name
    """Test listing all todos."""
    repo = TodoRepository(session)
    repo.create(title="Task 1", description="Desc 1")
    repo.create(title="Task 2", description="Desc 2")

    todos = repo.list_all()
    assert len(todos) == 2


def test_update_todo(session: Session) -> None:  # pylint: disable=redefined-outer-name
    """Test updating a todo."""
    repo = TodoRepository(session)
    created = repo.create(title="Old", description="Old")

    updated = repo.update(created.id, title="New", completed=True)
    assert updated.title == "New"
    assert updated.completed is True


def test_delete_todo(session: Session) -> None:  # pylint: disable=redefined-outer-name
    """Test deleting a todo."""
    repo = TodoRepository(session)
    created = repo.create(title="Task")

    repo.delete(created.id)
    retrieved = repo.get_by_id(created.id)
    assert retrieved is None
