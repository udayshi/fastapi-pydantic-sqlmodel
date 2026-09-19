"""Todo model definition."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


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
