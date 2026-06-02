"""OAuth metadata views (RFC 8414 / RFC 9728)."""

from starlette.requests import Request
from starlette.responses import JSONResponse

from src.config.settings import settings


async def oauth_protected_resource(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "resource": settings.mcp_public_url.rstrip("/"),
            "authorization_servers": [settings.oauth_issuer_url.rstrip("/")],
            "bearer_methods_supported": ["header"],
            "scopes_supported": ["read"],
        }
    )


async def oauth_discovery(_: Request) -> JSONResponse:
    issuer = settings.oauth_issuer_url.rstrip("/")
    payload = {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/o/authorize/",
        "token_endpoint": f"{issuer}/o/token/",
        "registration_endpoint": f"{issuer}/o/register/",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "code_challenge_methods_supported": ["S256"],
        "scopes_supported": ["read"],
        "access_token_lifetime": 36000,
    }
    if settings.logo_uri:
        payload["logo_uri"] = settings.logo_uri
    return JSONResponse(payload)
