"""Tests for database configuration."""

import pytest

from app.database.config import get_database_url


def test_get_database_url_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return the database URL supplied through the environment."""
    expected_url = "sqlite:///configured.db"
    monkeypatch.setenv("DATABASE_URL", expected_url)

    assert get_database_url() == expected_url


def test_get_database_url_rejects_missing_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise a clear error when the database URL is not configured."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL environment variable is required"):
        get_database_url()
