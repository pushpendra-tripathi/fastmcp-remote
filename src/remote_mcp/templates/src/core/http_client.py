from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from src.core.errors import AuthError, BackendError, ForbiddenError, RateLimitError

logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUSES = {502, 503, 504}


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError)):
        return True
    if isinstance(exc, BackendError):
        details = getattr(exc, "details", "") or ""
        return any(
            f"HTTP {s}" in details or f"HTTP {s}" in str(exc) for s in _RETRYABLE_HTTP_STATUSES
        )
    return False


def _retrying() -> AsyncRetrying:
    return AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    status = response.status_code
    try:
        body = response.text[:500]
    except Exception:
        body = "<unreadable>"

    if status == 401:
        raise AuthError("Backend rejected token as invalid (401)")
    if status == 403:
        raise ForbiddenError(f"Access forbidden (403): {body}")
    if status == 429:
        raise RateLimitError("Backend rate limit hit — retry after a moment")
    raise BackendError(f"Backend returned HTTP {status}", details=body)


def _parse_json_or_status(response: httpx.Response) -> dict[str, Any]:
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        return response.json()
    return {"status": "ok", "content_type": content_type}


async def _request_with_retry(
    name: str,
    do_call: Callable[[], Awaitable[dict[str, Any]]],
    *,
    retry: bool = True,
) -> dict[str, Any]:
    """Run an HTTP call with shared error handling. Optional retry on transient errors."""
    try:
        if not retry:
            return await do_call()
        async for attempt in _retrying():
            with attempt:
                return await do_call()
    except (AuthError, ForbiddenError, RateLimitError, BackendError):
        raise
    except RetryError as e:
        raise BackendError("Backend unreachable after retries", details=str(e)) from e
    except json.JSONDecodeError as e:
        raise BackendError("Failed to parse JSON response from backend", details=str(e)) from e
    except httpx.RequestError as e:
        raise BackendError(f"Network error contacting backend: {e}") from e
    except Exception as e:
        raise BackendError(f"Unexpected error during {name}: {e}") from e
    raise BackendError(f"{name} exited retry loop without result")


async def api_get(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Authenticated GET with retry on transient failures."""
    logger.debug("GET %s params=%s", path, params)

    async def _do() -> dict[str, Any]:
        response = await client.get(
            path, headers={"Authorization": auth_header}, params=params
        )
        _raise_for_status(response)
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            return response.json()
        return {
            "error": "Non-JSON response",
            "content_type": content_type,
            "hint": "The endpoint may have returned a file.",
        }

    return await _request_with_retry("api_get", _do)


async def api_post(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    json_body: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Authenticated POST with retry on transient failures."""
    if json_body is None and form_data is None:
        raise ValueError("api_post requires either json_body or form_data")
    logger.debug("POST %s", path)

    async def _do() -> dict[str, Any]:
        if json_body is not None:
            response = await client.post(
                path,
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                json=json_body,
            )
        else:
            response = await client.post(
                path, headers={"Authorization": auth_header}, data=form_data
            )
        _raise_for_status(response)
        return _parse_json_or_status(response)

    return await _request_with_retry("api_post", _do)


def _make_json_body_call(method: str) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def call(
        client: httpx.AsyncClient,
        path: str,
        auth_header: str,
        json_body: dict[str, Any],
    ) -> dict[str, Any]:
        logger.debug("%s %s", method, path)

        async def _do() -> dict[str, Any]:
            response = await client.request(
                method,
                path,
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                json=json_body,
            )
            _raise_for_status(response)
            return _parse_json_or_status(response)

        return await _request_with_retry(f"api_{method.lower()}", _do)

    call.__name__ = f"api_{method.lower()}"
    return call


api_patch = _make_json_body_call("PATCH")
api_put = _make_json_body_call("PUT")


async def api_delete(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Authenticated DELETE with optional JSON body and retry on transient failures."""
    logger.debug("DELETE %s", path)

    async def _do() -> dict[str, Any]:
        headers: dict[str, str] = {"Authorization": auth_header}
        extra: dict[str, Any] = {}
        if json_body is not None:
            headers["Content-Type"] = "application/json"
            extra["content"] = json.dumps(json_body).encode()
        response = await client.request("DELETE", path, headers=headers, **extra)
        if response.status_code == 204:
            return {"status": "deleted"}
        _raise_for_status(response)
        return _parse_json_or_status(response)

    return await _request_with_retry("api_delete", _do)


async def api_upload(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    filename: str,
    file_bytes: bytes,
    content_type: str = "application/octet-stream",
) -> dict[str, Any]:
    """Authenticated multipart file upload. No retry — not idempotent."""
    logger.debug("UPLOAD %s filename=%s size=%d", path, filename, len(file_bytes))

    async def _do() -> dict[str, Any]:
        response = await client.post(
            path,
            headers={"Authorization": auth_header},
            files={"file": (filename, file_bytes, content_type)},
        )
        _raise_for_status(response)
        ct = response.headers.get("content-type", "")
        if ct.startswith("application/json"):
            data = response.json()
            if isinstance(data, list):
                if not data:
                    raise BackendError("Upload API returned empty list")
                return data[0]
            return data
        return {"status": "ok", "content_type": ct}

    return await _request_with_retry("api_upload", _do, retry=False)
