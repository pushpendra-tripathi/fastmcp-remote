"""TelemetryMiddleware — connection-level event recording."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Record auth failures, rate limits, and SSE connection events."""

    async def dispatch(self, request: Request, call_next):
        from src.core.telemetry import TelemetryEvent, hash_token, telemetry_service

        path = request.url.path
        method = request.method
        user_id = "anonymous"

        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                user_id = hash_token(auth_header)
            except Exception:
                pass

        response = await call_next(request)

        event_type = None
        if response.status_code == 401:
            event_type = "auth_failure"
        elif response.status_code == 429:
            event_type = "rate_limit"
        elif method == "GET" and path.rstrip("/") == "/sse":
            event_type = "connection"

        if event_type:
            await telemetry_service.record_event(
                TelemetryEvent(
                    event_type=event_type,
                    user_id=user_id,
                    client_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    path=path,
                    extra={"method": method, "status": response.status_code},
                )
            )

        return response
