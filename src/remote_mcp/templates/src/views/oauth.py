"""OAuth metadata views (RFC 8414 / RFC 9728)."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse

from src.config.settings import settings


def _scopes() -> list[str]:
    return [s.strip() for s in settings.oauth_scopes_supported.split(",") if s.strip()] or ["read"]


async def oauth_protected_resource(_: Request) -> JSONResponse:
    """RFC 9728 — OAuth 2.0 Protected Resource Metadata."""
    return JSONResponse(
        {
            "resource": settings.mcp_public_url.rstrip("/"),
            "authorization_servers": [settings.oauth_issuer_url.rstrip("/")],
            "bearer_methods_supported": ["header"],
            "scopes_supported": _scopes(),
        }
    )


async def oauth_discovery(_: Request) -> JSONResponse:
    """RFC 8414 — OAuth 2.0 Authorization Server Metadata."""
    issuer = settings.oauth_issuer_url.rstrip("/")

    def _join(path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return f"{issuer}{path if path.startswith('/') else '/' + path}"

    payload = {
        "issuer": issuer,
        "authorization_endpoint": _join(settings.oauth_authorize_path),
        "token_endpoint": _join(settings.oauth_token_path),
        "registration_endpoint": _join(settings.oauth_registration_path),
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": _scopes(),
    }
    if settings.logo_uri:
        payload["logo_uri"] = settings.logo_uri
    return JSONResponse(payload)
