"""Database configuration and session management."""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()


def get_database_url() -> str:
    """Return the configured database URL from the environment."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    return database_url


DATABASE_URL = get_database_url()


def get_engine() -> Engine:
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
