"""Todo API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database.config import get_session
from app.database.repository import TodoRepository
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, session: Session = Depends(get_session)) -> TodoResponse:
    """Create a new todo."""
    repo = TodoRepository(session)
    db_todo = repo.create(title=todo.title, description=todo.description)
    return TodoResponse.model_validate(db_todo)


@router.get("", response_model=list[TodoResponse])
def list_todos(session: Session = Depends(get_session)) -> list[TodoResponse]:
    """Get all todos."""
    repo = TodoRepository(session)
    todos = repo.list_all()
    return [TodoResponse.model_validate(todo) for todo in todos]


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, session: Session = Depends(get_session)) -> TodoResponse:
    """Get todo by ID."""
    repo = TodoRepository(session)
    todo = repo.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoResponse.model_validate(todo)


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate, session: Session = Depends(get_session)) -> TodoResponse:
    """Update a todo."""
    repo = TodoRepository(session)
    todo = repo.update(
        todo_id, title=todo_update.title, description=todo_update.description, completed=todo_update.completed
    )
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoResponse.model_validate(todo)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, session: Session = Depends(get_session)) -> None:
    """Delete a todo."""
    repo = TodoRepository(session)
    success = repo.delete(todo_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
