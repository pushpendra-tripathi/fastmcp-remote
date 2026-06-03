from __future__ import annotations

import logging

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
