"""FastAPI application factory and configuration."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from redis import Redis
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.database.config import create_db_and_tables
from app.logger import logger
from app.routes.todo import router as todo_router
from app.sessions.middleware import RedisSessionMiddleware
from app.sessions.store import RedisSessionStore


def get_session_secret() -> str:
    """Return the secret used to sign browser session identifiers."""
    session_secret = os.getenv("SESSION_SECRET")
    if not session_secret:
        raise RuntimeError("SESSION_SECRET environment variable is required")
    return session_secret


def get_session_ttl_seconds() -> int:
    """Return a validated session lifetime in seconds."""
    ttl_seconds = int(os.getenv("SESSION_TTL_SECONDS", "1800"))
    if ttl_seconds <= 0:
        raise RuntimeError("SESSION_TTL_SECONDS must be positive")
    return ttl_seconds


SESSION_SECRET = get_session_secret()
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "todo_session")
SESSION_TTL_SECONDS = get_session_ttl_seconds()
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: startup and shutdown events."""
    # Startup: Initialize database
    logger.info("Starting up...")
    create_db_and_tables()
    logger.info("Database tables created successfully")
    if not hasattr(_app.state, "session_store"):
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise RuntimeError("REDIS_URL environment variable is required")
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        _app.state.session_store = RedisSessionStore(
            redis_client,
            prefix="todo:session:",
            ttl_seconds=SESSION_TTL_SECONDS,
        )

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
app.add_middleware(
    RedisSessionMiddleware,
    secret_key=SESSION_SECRET,
    cookie_name=SESSION_COOKIE_NAME,
    ttl_seconds=SESSION_TTL_SECONDS,
    cookie_secure=SESSION_COOKIE_SECURE,
)

# Include routes
app.include_router(todo_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/session")
def get_session(request: Request) -> dict[str, int]:
    """Increment and return the current session's visit count."""
    visits = int(request.state.session.get("visits", 0)) + 1
    request.state.session["visits"] = visits
    request.state.session['by']='uday'
    return {"visits": visits}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
