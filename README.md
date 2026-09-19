# Todo App Development Documentation

A Test-Driven Development (TDD) approach to building a todo app using FastAPI, SQLModel, and PostgreSQL.

## Prerequisites

- **Python:** 3.14+
- **Package Manager:** `uv` (required for running Python)
- **Databases:**
  - PostgreSQL (for development and production)
  - SQLite (for unit and integration tests, in-memory)

---

## Phase 1: Project Setup

### Step 1.1: Initialize Project Directory

```bash
mkdir todo_app
cd todo_app
```

### Step 1.2: Initialize uv Project

```bash
uv init --python 3.14
```

### Step 1.3: Create Virtual Environment

```bash
uv venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

### Step 1.4: Install Core Dependencies

```bash
uv add \
  fastapi \
  uvicorn \
  sqlmodel \
  psycopg2-binary \
  python-dotenv \
  pytest \
  pytest-asyncio \
  httpx
```

### Step 1.4.1: Important - Create __init__.py files

Python needs `__init__.py` files in all package directories for proper module discovery. This is **critical** for pytest to find your modules.

```bash
# Create __init__.py in all test directories
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

**Why this matters:** Without these files, pytest cannot import modules from your `app` package and will throw `ModuleNotFoundError: No module named 'app'`.

### Step 1.5: Create Project Structure

```bash
mkdir -p app/models
mkdir -p app/routes
mkdir -p app/schemas
mkdir -p app/database
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p logs
touch .env
touch .env.example
touch README.md
touch Makefile
```

### Step 1.6: Create .env File

```bash
# .env (for development - never commit this)
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db
TEST_DATABASE_URL=sqlite:///:memory:
LOG_LEVEL=INFO
```

### Step 1.7: Create .env.example File

```bash
# .env.example (template for developers)
DATABASE_URL=postgresql://user:password@localhost:5432/todo_db
TEST_DATABASE_URL=sqlite:///:memory:
LOG_LEVEL=INFO
```

### Step 1.8: Initialize Git

```bash
git init
echo ".env" >> .gitignore
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo "logs/" >> .gitignore
```

---

## Phase 2: Database Setup

### Step 2.1: Setup PostgreSQL (Development)

```bash
# macOS with Homebrew
brew install postgresql
brew services start postgresql

# or use Docker
docker run --name postgres_todo \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=todo_db \
  -p 5432:5432 \
  -d postgres:latest
```

### Step 2.2: Create Database Configuration Module

Create `app/database/config.py`:

```python
"""Database configuration and session management."""
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/todo_db")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

def get_engine():
    """Get database engine based on environment."""
    if "sqlite" in DATABASE_URL.lower():
        return create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
    return create_engine(DATABASE_URL, echo=True)

engine = get_engine()

def create_db_and_tables() -> None:
    """Create database tables."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    with Session(engine) as session:
        yield session
```

### Step 2.3: Create __init__.py for database module

Create `app/database/__init__.py`:

```python
"""Database module."""
from app.database.config import create_db_and_tables, get_session, engine

__all__ = ["create_db_and_tables", "get_session", "engine"]
```

---

## Phase 3: Data Models (TDD Approach)

### Step 3.1: Write Tests First for Todo Model

Create `tests/unit/test_todo_model.py`:

```python
"""Unit tests for Todo model."""
import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from app.models.todo import Todo


@pytest.fixture
def session() -> Session:
    """Create in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_todo_creation(session: Session) -> None:
    """Test creating a todo."""
    todo = Todo(title="Test Task", description="Test Description", completed=False)
    session.add(todo)
    session.commit()
    session.refresh(todo)

    assert todo.id is not None
    assert todo.title == "Test Task"
    assert todo.description == "Test Description"
    assert todo.completed is False


def test_todo_required_fields(session: Session) -> None:
    """Test todo requires title field."""
    todo = Todo(title="Task", completed=False)
    session.add(todo)
    session.commit()
    session.refresh(todo)

    assert todo.title == "Task"
    assert todo.description is None


def test_todo_completion_toggle() -> None:
    """Test toggling todo completion status."""
    todo = Todo(title="Task", completed=False)
    assert todo.completed is False

    todo.completed = True
    assert todo.completed is True
```

**A few things to keep in mind:**

- Import `SQLModel` from the `sqlmodel` package, not from `app.models.todo`.
- Import every class used by the module, such as `Todo`.
- Add return type hints to all functions: `-> None` for test functions and `-> Session` for fixtures.
- Remove duplicate imports inside fixtures.

### Step 3.2: Create Todo Model

Create `app/models/todo.py`:

```python
"""Todo model definition."""
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


def get_utc_now() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


class Todo(SQLModel, table=True):
    """Todo item model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)
```

**Why this pattern?**
- `datetime.now(timezone.utc)` is the modern approach (avoids deprecation warning)
- Uses timezone-aware datetime objects (best practice for Python 3.14+)
- Works with Python 3.14+ without any deprecation warnings
- Replaces deprecated `datetime.utcnow()` which is scheduled for removal

**Datetime Deprecation Issue (Learning Note):**
Python 3.12+ deprecated datetime.utcnow() because it returns naive datetime (no timezone info). The solution is to use datetime.now(timezone.utc) which:
- Returns timezone-aware datetime in UTC
- Is the official recommended approach
- Works with all Python versions 3.10+
- Pairs well with SQLModel and database operations

**Before (deprecated):**
```python
from datetime import datetime
created_at: datetime = Field(default_factory=datetime.utcnow)
```

**After (correct):**
```python
from datetime import datetime, timezone

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

created_at: datetime = Field(default_factory=get_utc_now)
```

This pattern eliminates deprecation warnings and ensures proper timezone handling.

### Step 3.3: Create __init__.py for models

Create `app/models/__init__.py`:

```python
"""Models module."""
from app.models.todo import Todo

__all__ = ["Todo"]
```

### Step 3.4: Run Model Tests

```bash
uv run pytest tests/unit/test_todo_model.py -v
```

**Expected Output:**
```
tests/unit/test_todo_model.py::test_todo_creation PASSED         [33%]
tests/unit/test_todo_model.py::test_todo_required_fields PASSED  [66%]
tests/unit/test_todo_model.py::test_todo_completion_toggle PASSED [100%]

3 passed in 0.26s
```

**Troubleshooting: If you get "ModuleNotFoundError: No module named 'app'"**
- Make sure you created all __init__.py files in test directories (Step 1.4.1)
- Verify pyproject.toml has [tool.pytest.ini_options] with pythonpath = ["."]
- Run: mkdir -p tests && touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py

---

## Phase 4: Schema Definitions

### Step 4.1: Write Tests for Schemas

Create `tests/unit/test_todo_schema.py`:

```python
"""Unit tests for Todo schemas."""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse


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
        updated_at=datetime.now(timezone.utc)
    )
    response = TodoResponse.model_validate(todo)
    assert response.id == 1
    assert response.title == "Task"
```

### Step 4.2: Create Todo Schemas

Create `app/schemas/todo.py`:

```python
"""Pydantic schemas for request/response validation."""
from typing import Optional
from datetime import datetime
from pydantic import Field, field_validator, ConfigDict
from sqlmodel import SQLModel


class TodoCreate(SQLModel):
    """Schema for creating a todo."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "title": "Buy groceries",
            "description": "Milk, eggs, bread"
        }
    })

    title: str = Field(min_length=1, description="Todo title (required)")
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Todo description (optional)"
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Ensure title is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()


class TodoUpdate(SQLModel):
    """Schema for updating a todo."""
    title: Optional[str] = Field(
        None,
        min_length=1,
        description="Todo title (optional)"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Todo description (optional)"
    )
    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Ensure title is not empty or whitespace only if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Title cannot be empty or whitespace only")
            return v.strip()
        return v


class TodoResponse(SQLModel):
    """Schema for todo response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    completed: bool
    created_at: datetime
    updated_at: datetime
```

**Key Learning Points:**
- Use Field() with min_length and max_length for constraints
- Use field_validator() for custom validation logic
- Use ConfigDict for Pydantic v2 configuration (not class Config)
- Use model_validate() instead of from_orm() (from_orm() is deprecated)
- Validators should raise ValueError for invalid data
- Always add return type hints to all functions

### Step 4.3: Create __init__.py for schemas

Create `app/schemas/__init__.py`:

```python
"""Schemas module."""
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse

__all__ = ["TodoCreate", "TodoUpdate", "TodoResponse"]
```

### Step 4.4: Run Schema Tests

```bash
uv run pytest tests/unit/test_todo_schema.py -v
```

Expected output:

```
tests/unit/test_todo_schema.py::test_todo_create_schema PASSED
tests/unit/test_todo_schema.py::test_todo_create_requires_title PASSED
tests/unit/test_todo_schema.py::test_todo_create_rejects_whitespace_only PASSED
tests/unit/test_todo_schema.py::test_todo_create_strips_whitespace PASSED
tests/unit/test_todo_schema.py::test_todo_update_schema PASSED
tests/unit/test_todo_schema.py::test_todo_update_allows_none PASSED
tests/unit/test_todo_schema.py::test_todo_response_schema PASSED

7 passed in 0.20s
```

**Troubleshooting: If you see "DID NOT RAISE ValueError" error**

This error means validation is not configured on the schema. The test expects ValidationError to be raised, but the schema accepts empty strings.

Root Cause: String type in Python includes empty strings (""). Pydantic needs explicit constraints to reject invalid values.

Solution: Add Field constraints and validators:

Before (no validation):
```python
class TodoCreate(SQLModel):
    title: str  # Accepts empty strings
```

After (with validation):
```python
from pydantic import Field, field_validator

class TodoCreate(SQLModel):
    title: str = Field(min_length=1)  # Reject empty strings

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()
```

Update tests to expect ValidationError:
```python
from pydantic import ValidationError

def test_todo_create_requires_title() -> None:
    with pytest.raises(ValidationError):  # Use ValidationError, not ValueError
        TodoCreate(title="")
```

Key learning: ValidationError is a subclass of ValueError. Pydantic raises ValidationError (not ValueError) when validation fails.

---

## Phase 5: Database Operations (Repository Pattern)

### Step 5.1: Write Tests for Todo Repository

Create `tests/unit/test_todo_repository.py`:

```python
"""Unit tests for Todo repository."""
import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from app.models.todo import Todo
from app.database.repository import TodoRepository


@pytest.fixture
def session() -> Session:
    """Create in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_todo(session: Session) -> None:
    """Test creating a todo via repository."""
    repo = TodoRepository(session)
    todo = repo.create(title="Test", description="Desc")

    assert todo.id is not None
    assert todo.title == "Test"


def test_get_todo_by_id(session: Session) -> None:
    """Test retrieving todo by ID."""
    repo = TodoRepository(session)
    created_todo = repo.create(title="Task", description="Desc")

    retrieved = repo.get_by_id(created_todo.id)
    assert retrieved is not None
    assert retrieved.title == "Task"


def test_list_todos(session: Session) -> None:
    """Test listing all todos."""
    repo = TodoRepository(session)
    repo.create(title="Task 1", description="Desc 1")
    repo.create(title="Task 2", description="Desc 2")

    todos = repo.list_all()
    assert len(todos) == 2


def test_update_todo(session: Session) -> None:
    """Test updating a todo."""
    repo = TodoRepository(session)
    created = repo.create(title="Old", description="Old")

    updated = repo.update(created.id, title="New", completed=True)
    assert updated.title == "New"
    assert updated.completed is True


def test_delete_todo(session: Session) -> None:
    """Test deleting a todo."""
    repo = TodoRepository(session)
    created = repo.create(title="Task")

    repo.delete(created.id)
    retrieved = repo.get_by_id(created.id)
    assert retrieved is None
```

**Key Learning Points:**
- Always add return type hints to fixture functions (-> Session)
- Import SQLModel from sqlmodel (not from app.models.todo)
- Add return type hints to all test functions (-> None)

### Step 5.2: Create Todo Repository

Create `app/database/repository.py`:

```python
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
```

### Step 5.3: Run Repository Tests

```bash
uv run pytest tests/unit/test_todo_repository.py -v
```

Expected output:

```
tests/unit/test_todo_repository.py::test_create_todo PASSED
tests/unit/test_todo_repository.py::test_get_todo_by_id PASSED
tests/unit/test_todo_repository.py::test_list_todos PASSED
tests/unit/test_todo_repository.py::test_update_todo PASSED
tests/unit/test_todo_repository.py::test_delete_todo PASSED

5 passed in 0.46s
```

**Important Learning - Type Hints for SQLModel**

Type Hint Warning: "Expected type list[Todo], got Sequence[Todo] instead"

Root Cause: SQLModel's session.exec().all() returns Sequence, not list. Type hints must match actual return type.

Solution - Use Modern Python 3.14+ Type Hints:

Before (incorrect):
```python
from typing import List
def list_all(self) -> List[Todo]:
    return self.session.exec(statement).all()  # Returns Sequence, not List
```

After (correct):
```python
def list_all(self) -> list[Todo]:
    return list(self.session.exec(statement).all())  # Convert to list
```

Key Changes:
1. Use lowercase list[T] instead of List[T] (Python 3.14+ syntax)
2. Remove "from typing import List"
3. Wrap with list() constructor: list(self.session.exec(statement).all())
4. Add -> None return type to __init__ methods

Python 3.14+ Type Hint Syntax:
- List[T] -> list[T]
- Dict[K, V] -> dict[K, V]
- Optional[T] -> T | None
- Union[A, B] -> A | B

This ensures type correctness and follows modern Python standards.

---

## Phase 6: API Routes (TDD Approach)

### Step 6.1: Write Integration Tests for Routes

Create `tests/integration/test_todo_routes.py`:

```python
"""Integration tests for todo routes."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool
from app.main import app, get_session
from app.models.todo import Todo

@pytest.fixture
def session():
    """Create in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Todo.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def client(session: Session):
    """Create test client with in-memory database."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    return TestClient(app)

def test_create_todo(client: TestClient):
    """Test POST /todos endpoint."""
    response = client.post(
        "/todos",
        json={"title": "Test Task", "description": "Test Desc"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["id"] is not None

def test_get_all_todos(client: TestClient):
    """Test GET /todos endpoint."""
    client.post("/todos", json={"title": "Task 1"})
    client.post("/todos", json={"title": "Task 2"})

    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_todo_by_id(client: TestClient):
    """Test GET /todos/{id} endpoint."""
    create_response = client.post("/todos", json={"title": "Task"})
    todo_id = create_response.json()["id"]

    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Task"

def test_update_todo(client: TestClient):
    """Test PATCH /todos/{id} endpoint."""
    create_response = client.post("/todos", json={"title": "Old"})
    todo_id = create_response.json()["id"]

    response = client.patch(
        f"/todos/{todo_id}",
        json={"title": "Updated", "completed": True}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["completed"] is True

def test_delete_todo(client: TestClient):
    """Test DELETE /todos/{id} endpoint."""
    create_response = client.post("/todos", json={"title": "Task"})
    todo_id = create_response.json()["id"]

    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204

    get_response = client.get(f"/todos/{todo_id}")
    assert get_response.status_code == 404

def test_create_todo_missing_title(client: TestClient):
    """Test creating todo without title returns 422."""
    response = client.post("/todos", json={"description": "No title"})
    assert response.status_code == 422
```

### Step 6.2: Create Todo Routes

Create `app/routes/todo.py`:

```python
"""Todo API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from app.database.config import get_session
from app.database.repository import TodoRepository

router = APIRouter(prefix="/todos", tags=["todos"])

@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    session: Session = Depends(get_session)
) -> TodoResponse:
    """Create a new todo."""
    repo = TodoRepository(session)
    db_todo = repo.create(title=todo.title, description=todo.description)
    return TodoResponse.from_orm(db_todo)

@router.get("", response_model=List[TodoResponse])
def list_todos(session: Session = Depends(get_session)) -> List[TodoResponse]:
    """Get all todos."""
    repo = TodoRepository(session)
    todos = repo.list_all()
    return [TodoResponse.from_orm(todo) for todo in todos]

@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(
    todo_id: int,
    session: Session = Depends(get_session)
) -> TodoResponse:
    """Get todo by ID."""
    repo = TodoRepository(session)
    todo = repo.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoResponse.from_orm(todo)

@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    session: Session = Depends(get_session)
) -> TodoResponse:
    """Update a todo."""
    repo = TodoRepository(session)
    todo = repo.update(
        todo_id,
        title=todo_update.title,
        description=todo_update.description,
        completed=todo_update.completed
    )
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoResponse.from_orm(todo)

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    session: Session = Depends(get_session)
) -> None:
    """Delete a todo."""
    repo = TodoRepository(session)
    success = repo.delete(todo_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
```

### Step 6.3: Create __init__.py for routes

Create `app/routes/__init__.py`:

```python
"""Routes module."""
from app.routes.todo import router as todo_router

__all__ = ["todo_router"]
```

### Step 6.4: Run Integration Tests

```bash
uv run pytest tests/integration/test_todo_routes.py -v
```

---

## Phase 7: Main Application Setup

### Step 7.1: Create Logging Configuration

Create `app/logger.py`:

```python
"""Logging configuration."""
import logging
import os
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def setup_logger(name: str) -> logging.Logger:
    """Setup logger with consistent format."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = setup_logger(__name__)
```

### Step 7.2: Create Main Application

Create `app/main.py`:

```python
"""FastAPI application factory and configuration."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.config import create_db_and_tables, get_session
from app.routes.todo import router as todo_router
from app.logger import logger

app = FastAPI(
    title="Todo App API",
    description="A simple todo app built with FastAPI and SQLModel",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    """Initialize database on startup."""
    logger.info("Starting up...")
    create_db_and_tables()
    logger.info("Database tables created successfully")

@app.on_event("shutdown")
def on_shutdown() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down...")

# Include routes
app.include_router(todo_router)

@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

### Step 7.3: Create app/__init__.py

Create `app/__init__.py`:

```python
"""Todo app package."""
```

---

## Phase 8: Makefile for Automation

Create `Makefile`:

```makefile
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
	uv run python app/main.py

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
```

---

## Phase 9: Configure pyproject.toml

Update `pyproject.toml` with proper pytest and code quality tool configurations:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --strict-markers"

[tool.black]
line-length = 120
target-version = ["py314"]

[tool.isort]
profile = "black"
line_length = 120

[tool.mypy]
python_version = "3.14"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

**Why this matters:**
- `pythonpath = ["."]` tells pytest where to find the app module
- `testpaths` restricts pytest to only look in tests directory
- Configurations ensure code quality standards across the project

### Common import mistakes

**Wrong:** `from app.models.todo import SQLModel`
- SQLModel is from the `sqlmodel` package, not from your app

**Correct:** `from sqlmodel import SQLModel`

**Wrong:** Forgetting to import classes used in tests
- If you use `Todo(...)` in tests, you MUST import it

**Correct:**
```python
from app.models.todo import Todo
from sqlmodel import Session, create_engine, SQLModel
```

---

## Phase 10: Running the Application

### Step 10.1: Install and Setup

```bash
make install
make db-create
```

### Step 10.2: Run All Tests

```bash
make test
```

Expected output:
```
tests/unit/test_todo_model.py 3 passed
tests/unit/test_todo_schema.py 3 passed
tests/unit/test_todo_repository.py 6 passed
tests/integration/test_todo_routes.py 6 passed
```

### Step 10.3: Start Development Server

```bash
make dev
```

Server will start at `http://localhost:8000`

### Step 10.4: Test API Endpoints

```bash
# Create todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'

# Get all todos
curl http://localhost:8000/todos

# Get todo by ID
curl http://localhost:8000/todos/1

# Update todo
curl -X PATCH http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete todo
curl -X DELETE http://localhost:8000/todos/1

# Health check
curl http://localhost:8000/health
```

### Step 10.5: View API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Phase-by-Phase Status

Current Implementation Status:

Phase 3 - Data Models: COMPLETE (3/3 tests passing)
Phase 4 - Schema Definitions: COMPLETE (7/7 tests passing)
Phase 5 - Database Repository: COMPLETE (5/5 tests passing)
Phase 6 - API Routes: READY
Phase 7 - Main Application: READY
Phase 8 - Makefile: READY
Phase 9 - Configuration: READY
Phase 10 - Running Application: READY

Total: 15/15 tests passing, 0 warnings

---

## Session Learning Updates

This section documents all fixes and learnings applied during development. All information is self-contained below.

### Issue 1: ModuleNotFoundError: No module named 'app'
Status: FIXED

Problem: pytest cannot import modules from your app package and throws `ModuleNotFoundError: No module named 'app'`

Root Cause: Missing __init__.py files in test directories prevents Python from recognizing them as packages.

Solution:
```bash
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

Also update pyproject.toml to add pytest configuration:
```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --strict-markers"
```

The pythonpath = ["."] is critical - it tells pytest where to find the app module.

### Issue 2: Datetime Deprecation Warning
Status: FIXED

Problem: Warning "datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version"

Root Cause: Python 3.12+ deprecated datetime.utcnow() in favor of timezone-aware objects.

Solution:
```python
from datetime import datetime, timezone

def get_utc_now() -> datetime:
    """Get current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)

class Todo(SQLModel, table=True):
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)
```

Why this works:
- datetime.now(timezone.utc) returns timezone-aware datetime in UTC
- Is the official recommended approach in Python 3.12+
- Eliminates deprecation warnings
- Works perfectly with SQLModel and databases

### Issue 3: ValidationError Not Raised (Phase 4)
Status: FIXED

Problem: Test fails with "DID NOT RAISE ValueError"

Root Cause: Schema had no validation constraints. Pydantic allows empty strings by default.

Solution: Add Field constraints and validators to schema:
```python
from pydantic import Field, field_validator, ConfigDict
from sqlmodel import SQLModel

class TodoCreate(SQLModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"title": "Buy groceries", "description": "Milk, eggs, bread"}
    })

    title: str = Field(min_length=1, description="Todo title")
    description: str | None = Field(None, max_length=1000)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()
```

Update tests to expect ValidationError:
```python
from pydantic import ValidationError

def test_todo_create_requires_title() -> None:
    with pytest.raises(ValidationError):  # ValidationError, not ValueError
        TodoCreate(title="")
```

Also update schema to use Pydantic v2 patterns:
- Use ConfigDict instead of class Config
- Use model_validate() instead of from_orm()
- Use field_validator instead of validator

Key learning: ValidationError is a subclass of ValueError. Pydantic raises ValidationError (not ValueError) when validation constraints are violated.

### Issue 4: Type Hint Warning (Sequence vs list) - Phase 5
Status: FIXED

Problem: Warning "Expected type list[Todo], got Sequence[Todo] instead"

Root Cause: SQLModel's session.exec().all() returns Sequence, not list. Type hints must match actual return type.

Solution in app/database/repository.py:
```python
from typing import Optional
from sqlmodel import Session, select
from app.models.todo import Todo

class TodoRepository:
    def __init__(self, session: Session) -> None:  # Add -> None
        self.session = session

    def list_all(self) -> list[Todo]:  # Use list[Todo] not List[Todo]
        statement = select(Todo)
        return list(self.session.exec(statement).all())  # Wrap with list()
```

Key changes:
1. Use Python 3.14+ syntax: list[T] instead of List[T]
2. Remove "from typing import List"
3. Wrap session.exec().all() with list() constructor
4. Add -> None return type to __init__ methods

Python 3.14+ Type Hint Modern Syntax:
- List[T] -> list[T]
- Dict[K, V] -> dict[K, V]
- Optional[T] -> T | None
- Union[A, B] -> A | B

### Issue 5: Missing Return Type Hints
Status: FIXED

Problem: Functions lack return type hints

Root Cause: Type hints improve code clarity and help type checkers find bugs.

Solution: Add return type hints to ALL functions:
```python
# Test functions
def test_todo_creation(session: Session) -> None:
    """Test creating a todo."""
    pass

# Fixture functions
@pytest.fixture
def session() -> Session:
    """Create in-memory SQLite session for testing."""
    pass

# Repository methods
def list_all(self) -> list[Todo]:
    """Get all todos."""
    pass

# __init__ methods
def __init__(self, session: Session) -> None:
    """Initialize repository with database session."""
    pass
```

Guidelines:
- Test functions: -> None
- Fixture functions: -> the_type_they_return
- Methods: -> ReturnType or -> None
- __init__ methods: -> None
- Repository methods: -> Model or -> list[Model] or -> Optional[Model]

This follows CLAUDE.md strict type hint requirements and helps catch bugs early.

---

## Summary

This guide walks through a TDD-based todo app built with Python 3.14, FastAPI, and SQLModel. It uses PostgreSQL
for development and production, SQLite for tests, and a Makefile for common development tasks.

---

## Notes and conventions

### Package Structure
- Create `__init__.py` in ALL package directories (app/, tests/, tests/unit/, tests/integration/)
- Without them, pytest cannot import your modules

### Import Rules
| Wrong | Correct | Why |
|---------|----------|-----|
| `from app.models.todo import SQLModel` | `from sqlmodel import SQLModel` | SQLModel is from sqlmodel package |
| `from app.models.todo import Session` | `from sqlmodel import Session` | Session is from sqlmodel package |
| Use `Todo` without importing | `from app.models.todo import Todo` | Must import what you use |
| Missing return types | Add `-> None` or `-> Type` | Required by CLAUDE.md strict mode |

### Configuration
- Update `pyproject.toml` with `[tool.pytest.ini_options]` including `pythonpath = ["."]`
- This tells pytest where to find the app module
- Add black, isort, and mypy configurations for code quality

### Testing Pattern (TDD)
1. **Red**: Write tests first (they fail)
2. **Green**: Write minimum code to pass tests
3. **Refactor**: Improve code without changing tests
4. Always run tests after changes: `uv run pytest tests/ -v`

---

## Session Learning Updates: Issue 8 - Deprecated on_event Lifecycle Handlers

### Problem

When running the application or tests, you see deprecation warnings:

```
DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.

Read more about it in the
[FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).
```

This occurs when using the old `@app.on_event()` decorator pattern for startup and shutdown logic.

### Root Cause

FastAPI has deprecated the `@app.on_event("startup")` and `@app.on_event("shutdown")` decorators in favor of modern lifespan async context managers. The old pattern is still functional but generates deprecation warnings and will eventually be removed.

### Complete Solution

Replace the old on_event decorators with a modern lifespan async context manager.

**Before (deprecated):**

```python
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
def on_startup() -> None:
    """Initialize database on startup."""
    logger.info("Starting up...")
    create_db_and_tables()
    logger.info("Database tables created successfully")

@app.on_event("shutdown")
def on_shutdown() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down...")
```

**After (modern with proper type hints):**

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: startup and shutdown events."""
    # Startup: Initialize database
    logger.info("Starting up...")
    create_db_and_tables()
    logger.info("Database tables created successfully")

    # Serve the application
    yield

    # Shutdown: Cleanup
    logger.info("Shutting down...")


app = FastAPI(
    title="Todo App API",
    description="A simple todo app built with FastAPI and SQLModel",
    version="1.0.0",
    lifespan=lifespan
)
```

### Understanding Lifespan Async Context Managers

**How it works:**

1. **Import asynccontextmanager**: Use Python's contextlib for decorator
2. **Import AsyncGenerator**: From typing for proper type hints
3. **Create async function**: Define `async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:`
4. **Startup logic**: Code before `yield` runs when app starts
5. **Yield**: Signals that startup is complete, app is ready to serve
6. **Shutdown logic**: Code after `yield` runs when app shuts down

**Type Hints for Lifespan:**
- Use `AsyncGenerator[None, None]` as return type
- This tells type checkers the function is an async generator
- The `@asynccontextmanager` decorator converts it to an async context manager
- Satisfies both the decorator's requirements and type checkers (IDE warnings gone)

**Visual flow:**

```
Application starts
    |
lifespan() executes startup code (before yield)
    |
yield - app ready to serve
    |
Application runs and handles requests
    |
Application stops
    |
lifespan() executes shutdown code (after yield)
    |
Application exits
```

### Why Modern Lifespan is Better

1. **Single context**: Both startup and shutdown in one place (easier to understand)
2. **Proper cleanup**: Guaranteed to run cleanup code even if startup fails
3. **Resource safety**: Follows Python async context manager best practices
4. **Future-proof**: Old pattern will be removed in future FastAPI versions
5. **No deprecation warnings**: Clean test output and logs

### Real-World Example

For database initialization and cleanup:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import create_engine, Session

@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Manage database lifecycle."""
    # Startup: Create database and tables
    print("Initializing database...")
    create_db_and_tables()  # Your database setup function
    print("Database ready")

    yield  # App runs here

    # Shutdown: Cleanup connections
    print("Closing database connections...")
    # Any cleanup code here
    print("Shutdown complete")


app = FastAPI(lifespan=lifespan)
```

### Middleware Type Hints: Starlette vs FastAPI

**Why use Starlette's CORSMiddleware?**

FastAPI re-exports Starlette's middleware for convenience, but Starlette's version has better type hints for `app.add_middleware()`.

**Before (type checker may warn):**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, ...)  # May show type hints warning
```

**After (clean type hints):**
```python
from starlette.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, ...)  # Proper typing
```

Both work identically at runtime - this is purely for better type checking.

### Complete Fixed app/main.py

```python
"""FastAPI application factory and configuration."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.database.config import create_db_and_tables, get_session
from app.routes.todo import router as todo_router
from app.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: startup and shutdown events."""
    # Startup: Initialize database
    logger.info("Starting up...")
    create_db_and_tables()
    logger.info("Database tables created successfully")

    # Serve the application
    yield

    # Shutdown: Cleanup
    logger.info("Shutting down...")


app = FastAPI(
    title="Todo App API",
    description="A simple todo app built with FastAPI and SQLModel",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(todo_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

### Testing

Run tests to verify no deprecation warnings:

```bash
uv run pytest tests/ -v
```

Expected output (clean with no warnings):

```
======================== 21 passed in 0.47s ========================
```

### Common Patterns

**Multiple startup tasks:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    # Task 1: Initialize database
    create_db_and_tables()

    # Task 2: Load configuration
    config = load_config()
    app.state.config = config

    # Task 3: Connect to external service
    await connect_to_external_api()

    yield

    # Cleanup in reverse order
    await disconnect_from_external_api()
    await cleanup_config()
    # Database cleanup if needed
```

**Error handling:**

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    try:
        logger.info("Starting up...")
        create_db_and_tables()
        logger.info("Startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    try:
        logger.info("Shutting down...")
        # Cleanup
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
```

### Type Hints Best Practices

**For lifespan function:**
- Import `AsyncGenerator` from typing
- Use `-> AsyncGenerator[None, None]` as return type
- This satisfies type checkers and the @asynccontextmanager decorator
- The first `None` = yield type (None for lifespan), second `None` = send type
- This eliminates all IDE type hints warnings

**For middleware:**
- Import from `starlette.middleware.cors` instead of `fastapi.middleware.cors`
- Starlette's CORSMiddleware has better type hints for `app.add_middleware()`
- Both work identically at runtime, but Starlette provides cleaner typing

**For endpoints:**
- Use specific return types: `dict[str, str]` not `dict`
- Use Python 3.14+ syntax: `list[T]`, `dict[K, V]`, `T | None`

### Key Learning Points

1. **Modern FastAPI**: Always use lifespan async context managers, not @app.on_event()
2. **Async context manager**: Uses @asynccontextmanager decorator and yield
3. **Single place**: Startup and shutdown code together (easier to maintain)
4. **Proper ordering**: Cleanup runs even if startup encounters errors
5. **No deprecation warnings**: Clean and professional test output
6. **Future-proof**: Follows current FastAPI best practices
7. **Type hints matter**: Use `AsyncGenerator[None, None]` for proper IDE support
8. **IDE warnings eliminated**: Correct type hints remove all type checker warnings
9. **Use Starlette imports**: More reliable typing for middleware
10. **Specific types**: Use `dict[str, str]` not `dict`, `list[T]` not `List[T]`

### pyproject.toml Update

Remove the on_event warning filter since we fixed the issue:

**Before:**
```toml
filterwarnings = [
    "ignore:Using `httpx` with `starlette.testclient` is deprecated",
    "ignore:The anyio.abc.BlockingPortal alias is deprecated",
    "ignore::DeprecationWarning:fastapi.applications",  # Removed this
]
```

**After:**
```toml
filterwarnings = [
    "ignore:Using `httpx` with `starlette.testclient` is deprecated",
    "ignore:The anyio.abc.BlockingPortal alias is deprecated",
]
```

---

## Session Learning Updates: Issue 7 - Pytest Deprecation Warnings from External Libraries

### Problem

When running pytest, you see deprecation warnings from external libraries:

```
DeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated
```

These warnings come from FastAPI/Starlette test client dependencies, not your code. They clutter test output and make it harder to spot real issues.

### Root Cause

FastAPI's TestClient has internal deprecations in its dependencies:
- Starlette's testclient still uses older httpx version
- Anyio has deprecated internal aliases
- These are not your responsibility but should be suppressed in test output

### Complete Solution

Add warning filters to `pyproject.toml` in the `[tool.pytest.ini_options]` section:

**Before (with warnings):**

```
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --strict-markers"
```

**After (warnings suppressed):**

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --strict-markers"
filterwarnings = [
    "ignore:Using `httpx` with `starlette.testclient` is deprecated",
    "ignore:The anyio.abc.BlockingPortal alias is deprecated",
    "ignore::DeprecationWarning:fastapi.applications",
]
```

### Understanding filterwarnings

The `filterwarnings` option in pytest filters out specified warning patterns:

**Syntax:** `"action:message:category:module:lineno"`

Examples:

```toml
# Ignore by exact message
"ignore:Using `httpx` with `starlette.testclient` is deprecated"

# Ignore by category and module (::DeprecationWarning:module_name)
"ignore::DeprecationWarning:fastapi.applications"

# Ignore all deprecation warnings (not recommended - you'll miss real issues)
"ignore::DeprecationWarning"
```

### Best Practices for filterwarnings

1. **Be specific**: Filter exact messages or module patterns, not broad categories
2. **Document why**: Add comments explaining why each warning is filtered
3. **Only filter external code**: Never suppress warnings from your own code
4. **Review periodically**: External libraries may fix deprecations in new versions

**Recommended filterwarnings with comments:**

```toml
filterwarnings = [
    # External: Starlette testclient still uses deprecated httpx import style
    "ignore:Using `httpx` with `starlette.testclient` is deprecated",
    # External: Anyio has internal deprecated aliases
    "ignore:The anyio.abc.BlockingPortal alias is deprecated",
    # External: FastAPI uses deprecated on_event lifecycle (fixed in newer versions)
    "ignore::DeprecationWarning:fastapi.applications",
]
```

### Testing

Run tests to verify warnings are suppressed:

```bash
uv run pytest tests/ -v
```

Expected output (clean with no external warnings):

```
======================== 21 passed in 0.37s ========================
```

Any remaining warnings should be from YOUR code, which you should investigate and fix.

### Common Warnings You SHOULD NOT Ignore

These are warnings from your own code that need investigation:

```
# DON'T IGNORE - This is YOUR code issue
DeprecationWarning in app/main.py:23: on_event is deprecated

# DON'T IGNORE - This is YOUR code issue
DeprecationWarning in tests/unit/test_todo_schema.py:45: deprecated pattern used

# DON'T IGNORE - This is YOUR code issue
PendingDeprecationWarning: Some method will be removed in future version
```

For on_event deprecation in YOUR code, use modern lifespan handlers instead (for future FastAPI updates).

### Complete pyproject.toml [tool.pytest.ini_options] Section

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --strict-markers"
filterwarnings = [
    "ignore:Using `httpx` with `starlette.testclient` is deprecated",
    "ignore:The anyio.abc.BlockingPortal alias is deprecated",
    "ignore::DeprecationWarning:fastapi.applications",
]
```

### Key Learning Points

1. **Pytest filterwarnings**: Use to suppress external library deprecation warnings
2. **Be specific**: Target exact messages or modules, not broad categories
3. **Only external**: Filter warnings from dependencies, never from your code
4. **Review regularly**: Check suppressed warnings when upgrading dependencies
5. **Clean output matters**: Helps you spot real issues in your code

---

## Session Learning Updates: Issue 6 - Deprecated from_orm() Method

### Problem

When running Phase 6 integration tests, you may see this deprecation warning:

```
obj.from_orm(data) was deprecated in SQLModel 0.0.14, you should instead use obj.model_validate(data).
```

This occurs in routes where `TodoResponse.from_orm(todo)` is used to convert database models to response schemas.

### Root Cause

SQLModel 0.0.14+ deprecated the `from_orm()` method in favor of `model_validate()` from Pydantic v2. The `.from_orm()` method works but generates deprecation warnings.

### Complete Solution

Update all route functions in `app/routes/todo.py` to use `model_validate()` instead of `from_orm()`.

**Before (deprecated):**

```python
from typing import List

@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    session: Session = Depends(get_session)
) -> TodoResponse:
    """Create a new todo."""
    repo = TodoRepository(session)
    db_todo = repo.create(title=todo.title, description=todo.description)
    return TodoResponse.from_orm(db_todo)  # DEPRECATED

@router.get("", response_model=List[TodoResponse])
def list_todos(session: Session = Depends(get_session)) -> List[TodoResponse]:
    """Get all todos."""
    repo = TodoRepository(session)
    todos = repo.list_all()
    return [TodoResponse.from_orm(todo) for todo in todos]  # DEPRECATED
```

**After (correct):**

```python
@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    session: Session = Depends(get_session)
) -> TodoResponse:
    """Create a new todo."""
    repo = TodoRepository(session)
    db_todo = repo.create(title=todo.title, description=todo.description)
    return TodoResponse.model_validate(db_todo)  # CORRECT

@router.get("", response_model=list[TodoResponse])
def list_todos(session: Session = Depends(get_session)) -> list[TodoResponse]:
    """Get all todos."""
    repo = TodoRepository(session)
    todos = repo.list_all()
    return [TodoResponse.model_validate(todo) for todo in todos]  # CORRECT
```

**Key Changes:**
1. Replace `.from_orm(db_todo)` with `.model_validate(db_todo)` in all route handlers
2. Change `List[TodoResponse]` to `list[TodoResponse]` (Python 3.14+ syntax)
3. Remove `from typing import List` import

**All 4 occurrences to fix in app/routes/todo.py:**
- Line 20: `create_todo()` route - create endpoint
- Line 27: `list_todos()` route - get all endpoint
- Line 39: `get_todo()` route - get by ID endpoint
- Line 57: `update_todo()` route - patch endpoint

### Implementation Details

**What is model_validate()?**

`model_validate()` is the Pydantic v2 method for converting ORM models to Pydantic models:

```python
# SQLModel hybrid model (works with both ORM and Pydantic)
todo: Todo = repo.get_by_id(1)  # Database model with ORM attributes

# Convert to response schema for API response
response = TodoResponse.model_validate(todo)  # Pydantic model with API fields
```

**Why model_validate() instead of from_orm()?**

- **Standards Compliance**: `model_validate()` is the standard Pydantic v2 method
- **Future Compatibility**: FastAPI and SQLModel recommend this approach
- **No Deprecation Warnings**: Eliminates all warnings in test output
- **Consistency**: Same method used in schemas (as shown in Phase 4)

### Testing

Run Phase 6 integration tests to verify the fix:

```bash
uv run pytest tests/integration/test_todo_routes.py -v
```

Expected output:

```
test_create_todo PASSED
test_get_all_todos PASSED
test_get_todo_by_id PASSED
test_update_todo PASSED
test_delete_todo PASSED
test_create_todo_missing_title PASSED

6 passed in 0.52s
```

No deprecation warnings about `from_orm()` should appear.

### Complete Fixed Routes File

File: `app/routes/todo.py`

```python
"""Todo API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from app.database.config import get_session
from app.database.repository import TodoRepository

router = APIRouter(prefix="/todos", tags=["todos"])

@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate,
    session: Session = Depends(get_session)
) -> TodoResponse:
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
def get_todo(
    todo_id: int,
    session: Session = Depends(get_session)
) -> TodoResponse:
    """Get todo by ID."""
    repo = TodoRepository(session)
    todo = repo.get_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoResponse.model_validate(todo)

@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    session: Session = Depends(get_session)
) -> TodoResponse:
    """Update a todo."""
    repo = TodoRepository(session)
    todo = repo.update(
        todo_id,
        title=todo_update.title,
        description=todo_update.description,
        completed=todo_update.completed
    )
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    return TodoResponse.model_validate(todo)

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    session: Session = Depends(get_session)
) -> None:
    """Delete a todo."""
    repo = TodoRepository(session)
    success = repo.delete(todo_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
```

### Key Learning Points

1. **Pydantic v2 standard**: Use `model_validate()` for all ORM-to-Pydantic conversions
2. **SQLModel is hybrid**: SQLModel models work with both ORM and Pydantic v2 methods
3. **Type hints consistency**: Use Python 3.14+ lowercase syntax (list[T] not List[T])
4. **No exceptions needed**: `model_validate()` doesn't require try-catch for SQLModel objects
5. **Deprecation warnings**: Always address deprecation warnings to stay compatible with future versions

---

## Troubleshooting Quick Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'app'` | Missing `__init__.py` | Create `tests/__init__.py`, `tests/unit/__init__.py` |
| `NameError: name 'Todo' is not defined` | Todo not imported | Add `from app.models.todo import Todo` |
| Pytest can't find tests | Wrong testpaths config | Set `testpaths = ["tests"]` in pyproject.toml |
| Type hints missing warnings | Functions lack return types | Add `-> None` to all test functions |

---

## Session Learning Updates: Issue 10 - Linting & Code Quality Fixes

### Problem

When running `make lint`, numerous pylint warnings appear:
- Missing final newlines in files
- Unused imports (get_session, Todo, pytest)
- Redefining outer scope variables (session, client in tests)
- Wrong import order (standard imports should come before third-party)
- Duplicate code in test fixtures

### Root Cause

Multiple issues:
1. Files missing final newlines (C0304 violation)
2. Importing unused modules
3. Test functions shadowing fixture names (pytest pattern)
4. Non-standard import ordering
5. Repeated session fixture code across test files

### Complete Solution

**1. Fix Final Newline Issues**

Add newlines to end of all files missing them:
- `app/database/config.py`
- `app/database/__init__.py`
- `app/models/__init__.py`
- `app/models/todo.py`
- `app/schemas/__init__.py`
- `app/schemas/todo.py`
- `app/routes/todo.py`
- `tests/unit/test_todo_*.py`
- `tests/integration/test_todo_routes.py`

**2. Fix Import Order (app/database/config.py)**

Import standard library (`os`, `from typing`) BEFORE third-party imports:

```python
# Before (wrong order)
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
import os
from dotenv import load_dotenv

# After (correct order)
import os
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine
```

**3. Remove Unused Imports**

- `app/main.py`: Remove unused `get_session` import
- `app/routes/todo.py`: Remove unused `Todo` import
- Test files: Remove unused `pytest` import

Before:
```python
from app.database.config import create_db_and_tables, get_session
from app.models.todo import Todo
```

After:
```python
from app.database.config import create_db_and_tables
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate
```

**4. Fix Unused Parameter in Lifespan**

The `app` parameter in lifespan function is unused by pylint. Prefix with underscore:

```python
# Before
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:

# After
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
```

**5. Fix Redefined-Outer-Name Warnings (Pytest Pattern)**

Pytest fixtures with same name as parameters cause this warning. This is a pytest pattern and safe to suppress.

Add pylint disable comment to each test function:

```python
def test_create_todo(session: Session) -> None:  # pylint: disable=redefined-outer-name
    """Test creating a todo via repository."""
    repo = TodoRepository(session)
    # ...
```

**6. Fix Duplicate Code - Create Shared Fixture**

Create `tests/conftest.py` with shared session fixture:

```python
"""Shared pytest fixtures for all tests."""
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


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
```

Remove duplicate fixture code from:
- `tests/unit/test_todo_model.py`
- `tests/unit/test_todo_repository.py`
- `tests/integration/test_todo_routes.py`

**7. Fix Import in Integration Tests**

get_session is in app.database.config, not app.main:

```python
# Before (wrong)
from app.main import app, get_session

# After (correct)
from app.database.config import get_session
from app.main import app
```

### Testing Results

Run linting:
```bash
make lint
```

Expected output (10.00/10 score):
```
-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 9.94/10, +0.06)
```

Run tests:
```bash
make test
```

Expected output:
```
======================== 21 passed in 0.81s ========================
```

### Complete Fixed Files Summary

**app/logger.py:**
- Renamed internal `logger` variable to `log` to avoid shadowing outer scope
- Fixed import organization

**app/main.py:**
- Removed unused `get_session` import
- Renamed `app` parameter to `_app` in lifespan function
- Changed import from `fastapi.middleware.cors` to `starlette.middleware.cors`

**app/database/config.py:**
- Fixed import order: standard library first, then third-party
- Added final newline

**app/routes/todo.py:**
- Removed unused `Todo` import
- Reorganized imports alphabetically
- Added final newline

**tests/conftest.py (NEW):**
- Shared session fixture for all tests
- Eliminates duplicate code

**tests/unit/test_todo_model.py:**
- Removed duplicate session fixture (now uses conftest.py)
- Added pylint disable comments for redefined-outer-name
- Removed unused pytest import

**tests/unit/test_todo_repository.py:**
- Removed duplicate session fixture (now uses conftest.py)
- Added pylint disable comments for all test functions
- Removed unused pytest import
- Fixed variable name from `session` to `session_instance` in with block

**tests/integration/test_todo_routes.py:**
- Removed duplicate session fixture (now uses conftest.py)
- Fixed get_session import (from app.database.config, not app.main)
- Added pylint disable comments for all test functions
- Fixed variable name from `session` to `session_instance`

**app/database/__init__.py, app/models/__init__.py, app/schemas/__init__.py, app/models/todo.py, app/schemas/todo.py, tests/unit/test_todo_schema.py:**
- Added missing final newlines

### Key Learning Points

1. **Pylint score**: Improved from 8.86/10 to 10.00/10
2. **Import order matters**: Standard library, blank line, third-party packages, blank line, then local imports
3. **Fixture shadowing**: pytest fixtures are safe to shadow (common pattern)
4. **DRY principle**: Extract common test fixtures to conftest.py
5. **File formatting**: Always end files with newline for POSIX compliance
6. **Type hints**: Always add `-> None` return type, prefix unused parameters with `_`

### Pylint Configuration in pyproject.toml

```toml
[tool.pylint.messages_control]
disable = [
    "C0111",  # Missing docstring
    "R0913",  # Too many arguments
]

[tool.pylint.format]
max-line-length = 120
```

---

## Follow the phases sequentially to build the complete todo app.
