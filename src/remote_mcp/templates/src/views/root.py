"""Landing page view."""

from datetime import datetime

from starlette.requests import Request

from src.config.settings import settings
from src.views import templates


async def root_ui(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "year": datetime.now().year,
            "mcp_public_url": settings.mcp_public_url.removesuffix("/mcp").removesuffix("/sse").rstrip("/"),
            "logo_uri": settings.logo_uri,
        },
    )
