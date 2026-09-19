"""Repository pattern for database operations."""

from typing import Optional

from sqlmodel import Session, select

from app.models.todo import Todo


class TodoRepository:
    """Repository for Todo model operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session."""
        self.session = session

    def create(self, title: str, description: Optional[str] = None) -> Todo:
        """Create a new todo."""
        todo = Todo(title=title, description=description)
        self.session.add(todo)
        self.session.commit()
        self.session.refresh(todo)
        return todo

    def get_by_id(self, todo_id: int) -> Optional[Todo]:
        """Get todo by ID."""
        return self.session.get(Todo, todo_id)

    def list_all(self) -> list[Todo]:
        """Get all todos."""
        statement = select(Todo)
        return list(self.session.exec(statement).all())

    def update(
        self,
        todo_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Optional[Todo]:
        """Update a todo."""
        todo = self.session.get(Todo, todo_id)
        if not todo:
            return None

        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
        if completed is not None:
            todo.completed = completed

        self.session.add(todo)
        self.session.commit()
        self.session.refresh(todo)
        return todo

    def delete(self, todo_id: int) -> bool:
        """Delete a todo."""
        todo = self.session.get(Todo, todo_id)
        if not todo:
            return False

        self.session.delete(todo)
        self.session.commit()
        return True
