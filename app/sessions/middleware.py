"""Middleware for signed, Redis-backed HTTP sessions."""

from __future__ import annotations

import secrets
from typing import cast

from fastapi import Request
from itsdangerous import BadSignature, URLSafeSerializer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from app.sessions.store import SessionData, SessionStore


class RedisSessionMiddleware(BaseHTTPMiddleware):
    """Load a server-side session and persist it after each request."""

    def __init__(
        self,
        app: ASGIApp,
        secret_key: str,
        cookie_name: str,
        ttl_seconds: int,
        cookie_secure: bool,
    ) -> None:
        """Configure signed-cookie and expiry settings for sessions."""
        super().__init__(app)
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._serializer = URLSafeSerializer(secret_key=secret_key, salt="todo-session")
        self._cookie_name = cookie_name
        self._ttl_seconds = ttl_seconds
        self._cookie_secure = cookie_secure

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Attach the session to the request and save changes in the response."""
        store = self._get_store(request)
        session_id = self._load_session_id(request)
        session = store.load(session_id) if session_id else None
        if session is None:
            session_id = secrets.token_urlsafe(32)
            session = {}

        request.state.session = session
        response = await call_next(request)
        store.save(session_id, cast(SessionData, request.state.session))
        response.set_cookie(
            key=self._cookie_name,
            value=self._serializer.dumps(session_id),
            max_age=self._ttl_seconds,
            httponly=True,
            secure=self._cookie_secure,
            samesite="lax",
            path="/",
        )
        return response

    def _get_store(self, request: Request) -> SessionStore:
        """Return the store configured during application startup."""
        store = getattr(request.app.state, "session_store", None)
        if store is None:
            raise RuntimeError("Session store is not configured")
        return cast(SessionStore, store)

    def _load_session_id(self, request: Request) -> str | None:
        """Return a verified session identifier from the request cookie."""
        signed_session_id = request.cookies.get(self._cookie_name)
        if signed_session_id is None:
            return None
        try:
            session_id = self._serializer.loads(signed_session_id)
        except BadSignature:
            return None
        return session_id if isinstance(session_id, str) else None
