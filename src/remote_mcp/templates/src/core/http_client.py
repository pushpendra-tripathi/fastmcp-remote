import json
import logging
from typing import Any, Optional

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


async def _do_get(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    params: Optional[dict[str, Any]],
) -> dict[str, Any]:
    response = await client.get(
        path,
        headers={"Authorization": auth_header},
        params=params,
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


async def api_get(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Authenticated GET with retry on transient failures (3 attempts, exponential backoff)."""
    logger.debug("GET %s params=%s", path, params)
    try:
        async for attempt in _retrying():
            with attempt:
                return await _do_get(client, path, auth_header, params)
    except (AuthError, ForbiddenError, RateLimitError, BackendError):
        raise
    except RetryError as e:
        raise BackendError("Backend unreachable after retries", details=str(e)) from e
    except json.JSONDecodeError as e:
        raise BackendError("Failed to parse JSON response from backend", details=str(e)) from e
    except httpx.RequestError as e:
        raise BackendError(f"Network error contacting backend: {e}") from e
    except Exception as e:
        raise BackendError(f"Unexpected error during API request: {e}") from e
    raise BackendError("api_get exited retry loop without result")


async def _do_post(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    json_body: Optional[dict[str, Any]],
    form_data: Optional[dict[str, Any]],
) -> dict[str, Any]:
    if json_body is not None:
        response = await client.post(
            path,
            headers={"Authorization": auth_header, "Content-Type": "application/json"},
            json=json_body,
        )
    else:
        response = await client.post(
            path,
            headers={"Authorization": auth_header},
            data=form_data,
        )
    _raise_for_status(response)
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        return response.json()
    return {"status": "ok", "content_type": content_type}


async def api_post(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    json_body: Optional[dict[str, Any]] = None,
    form_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Authenticated POST with retry on transient failures."""
    if json_body is None and form_data is None:
        raise ValueError("api_post requires either json_body or form_data")
    logger.debug("POST %s", path)
    try:
        async for attempt in _retrying():
            with attempt:
                return await _do_post(client, path, auth_header, json_body, form_data)
    except (AuthError, ForbiddenError, RateLimitError, BackendError):
        raise
    except RetryError as e:
        raise BackendError("Backend unreachable after retries", details=str(e)) from e
    except httpx.RequestError as e:
        raise BackendError(f"Network error contacting backend: {e}") from e
    except Exception as e:
        raise BackendError(f"Unexpected error during API request: {e}") from e
    raise BackendError("api_post exited retry loop without result")


async def api_patch(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    json_body: dict[str, Any],
) -> dict[str, Any]:
    """Authenticated PATCH with retry on transient failures."""
    logger.debug("PATCH %s", path)

    async def _do() -> dict[str, Any]:
        response = await client.patch(
            path,
            headers={"Authorization": auth_header, "Content-Type": "application/json"},
            json=json_body,
        )
        _raise_for_status(response)
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            return response.json()
        return {"status": "ok"}

    try:
        async for attempt in _retrying():
            with attempt:
                return await _do()
    except (AuthError, ForbiddenError, RateLimitError, BackendError):
        raise
    except RetryError as e:
        raise BackendError("Backend unreachable after retries", details=str(e)) from e
    except httpx.RequestError as e:
        raise BackendError(f"Network error contacting backend: {e}") from e
    except Exception as e:
        raise BackendError(f"Unexpected error: {e}") from e
    raise BackendError("api_patch exited retry loop without result")


async def api_put(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    json_body: dict[str, Any],
) -> dict[str, Any]:
    """Authenticated PUT with retry on transient failures."""
    logger.debug("PUT %s", path)

    async def _do() -> dict[str, Any]:
        response = await client.put(
            path,
            headers={"Authorization": auth_header, "Content-Type": "application/json"},
            json=json_body,
        )
        _raise_for_status(response)
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            return response.json()
        return {"status": "ok"}

    try:
        async for attempt in _retrying():
            with attempt:
                return await _do()
    except (AuthError, ForbiddenError, RateLimitError, BackendError):
        raise
    except RetryError as e:
        raise BackendError("Backend unreachable after retries", details=str(e)) from e
    except httpx.RequestError as e:
        raise BackendError(f"Network error contacting backend: {e}") from e
    except Exception as e:
        raise BackendError(f"Unexpected error: {e}") from e
    raise BackendError("api_put exited retry loop without result")


async def api_delete(
    client: httpx.AsyncClient,
    path: str,
    auth_header: str,
    json_body: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Authenticated DELETE with optional JSON body and retry on transient failures.

    Uses client.request("DELETE", ...) rather than client.delete() because
    httpx rejects json= on the shorthand delete() method.
    """
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
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            return response.json()
        return {"status": "ok"}

    try:
        async for attempt in _retrying():
            with attempt:
                return await _do()
    except (AuthError, ForbiddenError, RateLimitError, BackendError):
        raise
    except RetryError as e:
        raise BackendError("Backend unreachable after retries", details=str(e)) from e
    except httpx.RequestError as e:
        raise BackendError(f"Network error contacting backend: {e}") from e
    except Exception as e:
        raise BackendError(f"Unexpected error: {e}") from e
    raise BackendError("api_delete exited retry loop without result")


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
    try:
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
    except (AuthError, ForbiddenError, RateLimitError, BackendError):
        raise
    except httpx.RequestError as e:
        raise BackendError(f"Network error during upload: {e}") from e
    except Exception as e:
        raise BackendError(f"Unexpected error during upload: {e}") from e
