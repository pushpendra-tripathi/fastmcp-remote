from __future__ import annotations

import logging
from typing import Any

import jwt as pyjwt
from jwt import PyJWKClient

from fastmcp import Context

logger = logging.getLogger(__name__)


def extract_bearer_token(ctx: Context) -> str:
    """
    Extract the OAuth Bearer token from the MCP request context.

    Returns the full Authorization header value (``Bearer <token>``).

    Raises:
        ValueError: If no valid Authorization Bearer header is present.
    """
    headers = {}
    try:
        request_context = getattr(ctx, "request_context", None)
        request = getattr(request_context, "request", None) if request_context else None
        raw_headers = getattr(request, "headers", None) if request else None
        if raw_headers is not None:
            headers = raw_headers
    except Exception as e:
        logger.debug("Exception extracting headers: %s", e)

    # Starlette/httpx headers are case-insensitive. Plain dicts (tests, custom
    # transports) may use Title-case — handle both.
    auth_header = headers.get("authorization") or headers.get("Authorization") or ""

    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            return f"Bearer {token}"

    raise ValueError("Missing Authorization header. The LLM client must authenticate via OAuth.")


_jwks_client = None


def _get_jwks_client() -> PyJWKClient:
    """Lazily construct a cached PyJWKClient from settings."""
    global _jwks_client
    if _jwks_client is None:
        from src.config.settings import settings

        _jwks_client = PyJWKClient(settings.oauth_jwks_url)
    return _jwks_client


def verify_jwt(token: str, signing_key: bytes | None = None) -> dict[str, Any]:
    """
    Verify a JWT locally (AUTH_MODE=jwt).

    Checks signature (JWKS), iss, aud, exp. Returns decoded claims.
    ``signing_key`` overrides JWKS lookup (tests).

    Raises:
        jwt.PyJWTError: on any validation failure.
    """
    from src.config.settings import settings

    if signing_key is None:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token).key

    audience = settings.jwt_audience or settings.mcp_public_url
    return pyjwt.decode(
        token,
        signing_key,
        algorithms=["RS256", "ES256"],
        audience=audience,
        issuer=settings.oauth_issuer_url.rstrip("/"),
        options={"require": ["exp", "iss", "aud"]},
    )
