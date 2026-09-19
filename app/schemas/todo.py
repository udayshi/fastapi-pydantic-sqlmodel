"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, Field, field_validator
from sqlmodel import SQLModel


class TodoCreate(SQLModel):
    """Schema for creating a todo."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"title": "Buy groceries", "description": "Milk, eggs, bread"}}
    )

    title: str = Field(min_length=1, description="Todo title (required)")
    description: Optional[str] = Field(None, max_length=1000, description="Todo description (optional)")

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Ensure title is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()


class TodoUpdate(SQLModel):
    """Schema for updating a todo."""

    title: Optional[str] = Field(None, min_length=1, description="Todo title (optional)")
    description: Optional[str] = Field(None, max_length=1000, description="Todo description (optional)")
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
