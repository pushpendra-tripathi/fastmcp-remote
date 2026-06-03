import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from src.config.settings import settings
from src.core.telemetry import telemetry_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_) -> AsyncIterator[dict]:
    """FastMCP lifespan — creates shared httpx.AsyncClient per worker process."""
    logger.info("MCP server starting up — initialising HTTP client pool...")

    async with httpx.AsyncClient(
        base_url=settings.api_base_url,
        timeout=httpx.Timeout(settings.http_timeout),
        limits=httpx.Limits(
            max_connections=settings.http_max_connections,
            max_keepalive_connections=settings.http_max_keepalive,
        ),
        headers={
            "User-Agent": settings.user_agent,
            "Accept": "application/json",
        },
        follow_redirects=True,
    ) as client:
        logger.info(
            "HTTP client pool ready (max_conn=%s, keepalive=%s)",
            settings.http_max_connections,
            settings.http_max_keepalive,
        )
        yield {"http_client": client, "telemetry": telemetry_service}

    logger.info("MCP server shutting down — HTTP client pool closed.")


def get_http_client(ctx) -> httpx.AsyncClient:
    """Extract shared HTTP client from tool context."""
    try:
        return ctx.request_context.lifespan_context["http_client"]
    except (AttributeError, KeyError, TypeError) as e:
        raise RuntimeError("HTTP client not initialized — lifespan did not run") from e
