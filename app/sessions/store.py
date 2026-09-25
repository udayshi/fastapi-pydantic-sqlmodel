"""Redis persistence for server-side session data."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Protocol


SessionData = dict[str, int | str | bool]


class SessionStore(Protocol):
    """Persistence contract used by the session middleware."""

    def load(self, session_id: str) -> SessionData | None:
        """Return session data for an identifier."""

    def save(self, session_id: str, data: Mapping[str, int | str | bool]) -> None:
        """Persist session data for an identifier."""

    def delete(self, session_id: str) -> None:
        """Delete session data for an identifier."""


class RedisClient(Protocol):
    """The subset of the synchronous Redis client used by the store."""

    def get(self, name: str) -> str | bytes | None:
        """Return the value for a key."""

    def setex(self, name: str, time: int, value: str) -> object:
        """Set a value with an expiry in seconds."""

    def delete(self, *names: str) -> object:
        """Delete one or more keys."""


class RedisSessionStore:
    """Store JSON-serializable session data under a namespaced Redis key."""

    def __init__(self, client: RedisClient, prefix: str, ttl_seconds: int) -> None:
        """Configure a session store backed by a Redis client."""
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._client = client
        self._prefix = prefix
        self._ttl_seconds = ttl_seconds

    def load(self, session_id: str) -> SessionData | None:
        """Return valid session data, or None when it is absent or invalid."""
        raw_value = self._client.get(self._key(session_id))
        if raw_value is None:
            return None
        try:
            decoded = raw_value.decode() if isinstance(raw_value, bytes) else raw_value
            data = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict) or not all(isinstance(key, str) for key in data):
            return None
        if not all(isinstance(value, (str, int, bool)) for value in data.values()):
            return None
        return data

    def save(self, session_id: str, data: Mapping[str, int | str | bool]) -> None:
        """Persist session data and refresh its expiry."""
        self._client.setex(self._key(session_id), self._ttl_seconds, json.dumps(dict(data)))

    def delete(self, session_id: str) -> None:
        """Remove a session from Redis."""
        self._client.delete(self._key(session_id))

    def _key(self, session_id: str) -> str:
        """Return the Redis key for a session identifier."""
        return f"{self._prefix}{session_id}"
