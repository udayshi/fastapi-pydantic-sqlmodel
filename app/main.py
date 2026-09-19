"""FastAPI application factory and configuration."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.database.config import create_db_and_tables
from app.logger import logger
from app.routes.todo import router as todo_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
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
    lifespan=lifespan,
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
