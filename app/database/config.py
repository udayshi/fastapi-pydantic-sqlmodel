"""Database configuration and session management."""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

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
