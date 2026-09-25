"""Tests for Redis session persistence."""

from app.sessions.store import RedisSessionStore


class FakeRedis:
    """Minimal Redis double that records calls."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        """Return a stored value."""
        return self.values.get(key)

    def setex(self, key: str, seconds: int, value: str) -> None:
        """Store a value and its expiry."""
        self.values[key] = value
        self.ttls[key] = seconds

    def delete(self, key: str) -> None:
        """Delete a value."""
        self.values.pop(key, None)


def test_save_load_and_delete_session() -> None:
    """Session values round-trip through the Redis store."""
    redis = FakeRedis()
    store = RedisSessionStore(redis, prefix="todo:session:", ttl_seconds=1800)

    store.save("session-id", {"visits": 1})

    assert redis.ttls["todo:session:session-id"] == 1800
    assert store.load("session-id") == {"visits": 1}

    store.delete("session-id")

    assert store.load("session-id") is None


def test_load_returns_none_for_missing_or_invalid_json() -> None:
    """Missing and corrupted Redis values are not trusted as sessions."""
    redis = FakeRedis()
    store = RedisSessionStore(redis, prefix="todo:session:", ttl_seconds=1800)
    redis.values["todo:session:broken"] = "not-json"

    assert store.load("missing") is None
    assert store.load("broken") is None