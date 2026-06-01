# fastmcp-remote Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `fastmcp-remote`, a CLI tool that scaffolds a production-ready remote MCP server from two prompts.

**Architecture:** Pure scaffold (copy-on-create). `fastmcp-remote new <name>` asks two questions, renders Jinja2 templates into a new project directory. Generated projects have zero runtime dependency on `fastmcp-remote`. Source of truth for template content is the `eninesites_mcp` project at `/Users/pushpendratripathi/Workspace/1e9advisors/eninesites_mcp`.

**Tech Stack:** Python 3.12+, typer, rich, jinja2, hatchling (build backend), pytest

---

## File Map

### Package files (fastmcp-remote itself)

| Path | Responsibility |
|------|---------------|
| `pyproject.toml` | Package metadata, hatchling build, entry point `fastmcp-remote` |
| `src/fastmcp_remote/__init__.py` | Version string |
| `src/fastmcp_remote/cli.py` | typer app — `new` command, interactive prompts |
| `src/fastmcp_remote/scaffold.py` | `scaffold_project(target, context)` — walk templates, render `.j2`, copy verbatim |
| `tests/test_scaffold.py` | File tree, substitutions, no EnineSites refs, error on existing dir |
| `tests/test_cli.py` | CLI invocation via typer.testing.CliRunner |
| `README.md` | Install + quickstart |
| `.github/workflows/ci.yml` | pytest on push/PR |
| `.github/workflows/publish.yml` | hatch build + PyPI trusted publisher on `v*` tag |

### Template files (live under `src/fastmcp_remote/templates/`)

| Template path | Output file | Type |
|--------------|-------------|------|
| `src/__init__.py` | `src/__init__.py` | verbatim (empty) |
| `src/server.py.j2` | `src/server.py` | Jinja2 |
| `src/config/__init__.py` | `src/config/__init__.py` | verbatim (empty) |
| `src/config/settings.py.j2` | `src/config/settings.py` | Jinja2 |
| `src/core/__init__.py` | `src/core/__init__.py` | verbatim (empty) |
| `src/core/app_state.py` | `src/core/app_state.py` | verbatim |
| `src/core/auth.py` | `src/core/auth.py` | verbatim |
| `src/core/errors.py.j2` | `src/core/errors.py` | Jinja2 |
| `src/core/formatters.py.j2` | `src/core/formatters.py` | Jinja2 |
| `src/core/http_client.py` | `src/core/http_client.py` | verbatim |
| `src/core/telemetry.py.j2` | `src/core/telemetry.py` | Jinja2 |
| `src/core/utils.py.j2` | `src/core/utils.py` | Jinja2 |
| `src/tools/__init__.py` | `src/tools/__init__.py` | verbatim (empty) |
| `src/tools/example.py` | `src/tools/example.py` | verbatim |
| `src/resources/__init__.py` | `src/resources/__init__.py` | verbatim (empty) |
| `src/skills/__init__.py` | `src/skills/__init__.py` | verbatim (empty) |
| `tests/conftest.py` | `tests/conftest.py` | verbatim |
| `tests/test_auth.py` | `tests/test_auth.py` | verbatim |
| `tests/test_middleware.py` | `tests/test_middleware.py` | verbatim |
| `tests/test_telemetry.py` | `tests/test_telemetry.py` | verbatim |
| `templates/index.html.j2` | `templates/index.html` | Jinja2 |
| `asgi.py` | `asgi.py` | verbatim |
| `pyproject.toml.j2` | `pyproject.toml` | Jinja2 |
| `env.example.j2` | `env.example` | Jinja2 |
| `.gitignore` | `.gitignore` | verbatim |
| `.pylintrc` | `.pylintrc` | verbatim |
| `DEPLOYMENT.md.j2` | `DEPLOYMENT.md` | Jinja2 |

**Jinja2 context dict** (derived from two CLI prompts):
```python
{
    "project_name": "my-project",      # kebab-case — dir name, pyproject name
    "project_slug": "my_project",      # snake_case — package, imports, logger
    "service_name": "My Project",      # human — FastMCP(), landing page
    "class_prefix": "MyProject",       # PascalCase — error class names
}
# Derivation:
# project_slug = project_name.replace("-", "_")
# class_prefix = "".join(w.capitalize() for w in project_name.split("-"))
```

**Important:** `templates/index.html.j2` contains Starlette Jinja2 variables (`{{ mcp_public_url }}`, `{{ year }}`) that must NOT be rendered at scaffold time. Wrap them with `{% raw %}...{% endraw %}` in the .j2 file.

---

## Task 1: Bootstrap package

**Files:**
- Create: `pyproject.toml`
- Create: `src/fastmcp_remote/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "fastmcp-remote"
version = "0.1.0"
description = "One command to a production-ready remote MCP server"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Pushpendra Tripathi" }]
keywords = ["mcp", "fastmcp", "remote", "oauth", "scaffold", "cli"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "typer>=0.12",
    "rich>=14.0",
    "jinja2>=3.1",
]

[project.scripts]
fastmcp-remote = "fastmcp_remote.cli:app"

[project.urls]
Homepage = "https://github.com/pushpendra-tripathi/fastmcp-remote"
Repository = "https://github.com/pushpendra-tripathi/fastmcp-remote"

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov>=6",
]

[tool.hatch.build.targets.wheel]
packages = ["src/fastmcp_remote"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.black]
line-length = 100
target-version = ["py312"]
```

- [ ] **Step 2: Create `src/fastmcp_remote/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Create virtual environment and install**

```bash
cd /Users/pushpendratripathi/Workspace/personal_projects/fastmcp-remote
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Expected: `Successfully installed fastmcp-remote-0.1.0`

- [ ] **Step 4: Verify CLI entry point is registered**

```bash
fastmcp-remote --help
```

Expected: error about missing `cli.py` OR `No commands registered` — just confirm the command is found.

---

## Task 2: TDD — write failing scaffold tests

**Files:**
- Create: `tests/test_scaffold.py`

- [ ] **Step 1: Create `tests/test_scaffold.py`**

```python
import pytest
from pathlib import Path
from fastmcp_remote.scaffold import scaffold_project

CONTEXT = {
    "project_name": "test-project",
    "project_slug": "test_project",
    "service_name": "Test Project",
    "class_prefix": "TestProject",
}

EXPECTED_FILES = [
    "asgi.py",
    "pyproject.toml",
    "env.example",
    "DEPLOYMENT.md",
    ".gitignore",
    ".pylintrc",
    "src/__init__.py",
    "src/server.py",
    "src/config/__init__.py",
    "src/config/settings.py",
    "src/core/__init__.py",
    "src/core/app_state.py",
    "src/core/auth.py",
    "src/core/errors.py",
    "src/core/formatters.py",
    "src/core/http_client.py",
    "src/core/telemetry.py",
    "src/core/utils.py",
    "src/tools/__init__.py",
    "src/tools/example.py",
    "src/resources/__init__.py",
    "src/skills/__init__.py",
    "tests/conftest.py",
    "tests/test_auth.py",
    "tests/test_middleware.py",
    "tests/test_telemetry.py",
    "templates/index.html",
]


def test_scaffold_creates_expected_files(tmp_path):
    target = tmp_path / "test-project"
    scaffold_project(target, CONTEXT)
    for f in EXPECTED_FILES:
        assert (target / f).exists(), f"Missing: {f}"


def test_scaffold_substitutes_class_prefix_in_errors(tmp_path):
    target = tmp_path / "test-project"
    scaffold_project(target, CONTEXT)
    content = (target / "src/core/errors.py").read_text()
    assert "class TestProjectError(Exception)" in content
    assert "class AuthError(TestProjectError)" in content
    assert "class BackendError(TestProjectError)" in content


def test_scaffold_substitutes_class_prefix_in_utils(tmp_path):
    target = tmp_path / "test-project"
    scaffold_project(target, CONTEXT)
    content = (target / "src/core/utils.py").read_text()
    assert "from src.core.errors import TestProjectError" in content
    assert "except TestProjectError as e:" in content


def test_scaffold_substitutes_service_name_in_server(tmp_path):
    target = tmp_path / "test-project"
    scaffold_project(target, CONTEXT)
    content = (target / "src/server.py").read_text()
    assert 'FastMCP("Test Project"' in content
    assert '"service": "Test Project MCP"' in content


def test_scaffold_substitutes_project_slug_in_pyproject(tmp_path):
    target = tmp_path / "test-project"
    scaffold_project(target, CONTEXT)
    content = (target / "pyproject.toml").read_text()
    assert 'name = "test-project"' in content
    assert 'test_project = "src.server:run"' in content


def test_scaffold_substitutes_project_slug_in_telemetry(tmp_path):
    target = tmp_path / "test-project"
    scaffold_project(target, CONTEXT)
    content = (target / "src/core/telemetry.py").read_text()
    assert '"test_project_telemetry"' in content


def test_scaffold_no_eninesites_references(tmp_path):
    target = tmp_path / "test-project"
    scaffold_project(target, CONTEXT)
    for path in target.rglob("*.py"):
        content = path.read_text()
        assert "EnineSites" not in content, f"Found EnineSites in {path.relative_to(target)}"
        assert "eninesites" not in content, f"Found eninesites in {path.relative_to(target)}"
    for path in target.rglob("*.toml"):
        content = path.read_text()
        assert "eninesites" not in content.lower(), f"Found eninesites in {path.relative_to(target)}"


def test_scaffold_index_html_has_service_name(tmp_path):
    target = tmp_path / "test-project"
    scaffold_project(target, CONTEXT)
    content = (target / "templates/index.html").read_text()
    assert "Test Project" in content
    assert "{{ mcp_public_url }}" in content   # Starlette var must pass through
    assert "{{ year }}" in content              # Starlette var must pass through


def test_scaffold_fails_if_target_exists(tmp_path):
    target = tmp_path / "test-project"
    target.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        scaffold_project(target, CONTEXT)


def test_scaffold_no_partial_write_on_error(tmp_path):
    target = tmp_path / "test-project"
    target.mkdir()
    try:
        scaffold_project(target, CONTEXT)
    except FileExistsError:
        pass
    assert list(target.iterdir()) == []
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
pytest tests/test_scaffold.py -v
```

Expected: `ImportError: cannot import name 'scaffold_project' from 'fastmcp_remote.scaffold'`

---

## Task 3: Implement scaffold.py

**Files:**
- Create: `src/fastmcp_remote/scaffold.py`

- [ ] **Step 1: Create `src/fastmcp_remote/scaffold.py`**

```python
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).parent / "templates"


def scaffold_project(target_dir: Path, context: dict) -> None:
    """
    Render all templates into target_dir.

    .j2 files are rendered with Jinja2 and written without the .j2 extension.
    All other files are copied verbatim.
    Raises FileExistsError (without writing anything) if target_dir already exists.
    """
    if target_dir.exists():
        raise FileExistsError(f"Directory already exists: {target_dir}")

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )

    target_dir.mkdir(parents=True)

    for template_path in sorted(TEMPLATES_DIR.rglob("*")):
        if template_path.is_dir():
            continue

        relative = template_path.relative_to(TEMPLATES_DIR)

        if template_path.suffix == ".j2":
            output_path = target_dir / relative.with_suffix("")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            template = env.get_template(str(relative).replace("\\", "/"))
            output_path.write_text(template.render(**context), encoding="utf-8")
        else:
            output_path = target_dir / relative
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template_path, output_path)
```

- [ ] **Step 2: Create the templates directory structure**

```bash
mkdir -p src/fastmcp_remote/templates/src/config
mkdir -p src/fastmcp_remote/templates/src/core
mkdir -p src/fastmcp_remote/templates/src/tools
mkdir -p src/fastmcp_remote/templates/src/resources
mkdir -p src/fastmcp_remote/templates/src/skills
mkdir -p src/fastmcp_remote/templates/tests
mkdir -p src/fastmcp_remote/templates/templates
```

- [ ] **Step 3: Run tests — verify they still fail with a clear error**

```bash
pytest tests/test_scaffold.py::test_scaffold_creates_expected_files -v
```

Expected: `AssertionError: Missing: asgi.py` (scaffold runs, directory created, but no template files yet)

---

## Task 4: Verbatim template files

**Files to create under `src/fastmcp_remote/templates/`**

These files are copied byte-for-byte into the generated project. Generic (no EnineSites references).

- [ ] **Step 1: Create all empty `__init__.py` files**

```bash
touch src/fastmcp_remote/templates/src/__init__.py
touch src/fastmcp_remote/templates/src/config/__init__.py
touch src/fastmcp_remote/templates/src/core/__init__.py
touch src/fastmcp_remote/templates/src/tools/__init__.py
touch src/fastmcp_remote/templates/src/resources/__init__.py
touch src/fastmcp_remote/templates/src/skills/__init__.py
```

- [ ] **Step 2: Create `src/fastmcp_remote/templates/src/core/auth.py`**

```python
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
    headers: dict = {}
    try:
        request_context = getattr(ctx, "request_context", None)
        request = getattr(request_context, "request", None) if request_context else None
        raw_headers = getattr(request, "headers", None) if request else None
        if raw_headers is not None:
            headers = raw_headers
    except Exception as e:
        logger.debug("Exception extracting headers: %s", e)

    auth_header = headers.get("authorization") or headers.get("Authorization") or ""

    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            logger.debug("Bearer token extracted from Authorization header")
            return f"Bearer {token}"

    raise ValueError("Missing Authorization header. The LLM client must authenticate via OAuth.")
```

- [ ] **Step 3: Create `src/fastmcp_remote/templates/src/core/app_state.py`**

```python
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

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
```

- [ ] **Step 4: Create `src/fastmcp_remote/templates/src/core/http_client.py`**

```python
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

from src.core.errors import AuthError, BackendError, PermissionError, RateLimitError

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
        raise PermissionError(f"Access forbidden (403): {body}")
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
    except (AuthError, PermissionError, RateLimitError, BackendError):
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
    except (AuthError, PermissionError, RateLimitError, BackendError):
        raise
    except RetryError as e:
        raise BackendError("Backend unreachable after retries", details=str(e)) from e
    except httpx.RequestError as e:
        raise BackendError(f"Network error contacting backend: {e}") from e
    except Exception as e:
        raise BackendError(f"Unexpected error during API request: {e}") from e
    raise BackendError("api_post exited retry loop without result")
```

- [ ] **Step 5: Create `src/fastmcp_remote/templates/src/tools/example.py`**

```python
from fastmcp import Context, FastMCP

from src.core.utils import tool_handler

example_router = FastMCP("example")


@example_router.tool()
@tool_handler
async def echo(message: str, ctx: Context) -> str:
    """Echo a message back. Replace with your first real tool."""
    return f"Echo: {message}"
```

- [ ] **Step 6: Create `src/fastmcp_remote/templates/asgi.py`**

```python
"""
Production ASGI entry point for Uvicorn / Gunicorn + Uvicorn workers.

Usage:
  # Development
  uvicorn asgi:application --reload --host 127.0.0.1 --port 8001 --lifespan on

  # Production (multi-worker)
  uvicorn asgi:application --host 0.0.0.0 --port 8001 --workers 4 --lifespan on
"""

from src.server import app as application  # noqa: F401
```

- [ ] **Step 7: Create `src/fastmcp_remote/templates/tests/conftest.py`**

```python
import pytest
from starlette.testclient import TestClient


@pytest.fixture(scope="session")
def test_client():
    """Shared TestClient. FastMCP's session manager forbids multiple lifespans."""
    from src.server import app

    with TestClient(app) as c:
        yield c
```

- [ ] **Step 8: Create `src/fastmcp_remote/templates/tests/test_auth.py`**

```python
import pytest

from src.core.auth import extract_bearer_token


class _MockRequest:
    def __init__(self, headers):
        self.headers = headers


class _MockRequestContext:
    def __init__(self, headers):
        self.request = _MockRequest(headers)


class _MockContext:
    def __init__(self, headers):
        self.request_context = _MockRequestContext(headers)


def test_extract_bearer_token_valid():
    ctx = _MockContext({"authorization": "Bearer mytoken123"})
    result = extract_bearer_token(ctx)
    assert result == "Bearer mytoken123"


def test_extract_bearer_token_missing_header():
    ctx = _MockContext({})
    with pytest.raises(ValueError, match="Missing Authorization header"):
        extract_bearer_token(ctx)


def test_extract_bearer_token_malformed_scheme():
    ctx = _MockContext({"authorization": "Basic sometoken"})
    with pytest.raises(ValueError, match="Missing Authorization header"):
        extract_bearer_token(ctx)


def test_extract_bearer_token_empty_bearer():
    ctx = _MockContext({"authorization": "Bearer "})
    with pytest.raises(ValueError, match="Missing Authorization header"):
        extract_bearer_token(ctx)


def test_extract_bearer_token_case_insensitive_header():
    ctx = _MockContext({"Authorization": "Bearer MYTOKEN"})
    result = extract_bearer_token(ctx)
    assert result == "Bearer MYTOKEN"
```

- [ ] **Step 9: Create `src/fastmcp_remote/templates/tests/test_middleware.py`**

```python
import pytest


@pytest.fixture
def client(test_client):
    return test_client


def test_health_bypasses_auth(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_well_known_bypasses_auth(client):
    r = client.get("/.well-known/oauth-authorization-server")
    assert r.status_code == 200


def test_root_ui_bypasses_auth(client):
    r = client.get("/")
    assert r.status_code != 401


def test_sse_missing_auth_returns_401(client):
    r = client.get("/sse")
    assert r.status_code == 401
    assert r.headers.get("www-authenticate", "").lower().startswith("bearer")
    assert "Authorization" in r.json()["error"]


def test_options_request_passes_through(client):
    r = client.options(
        "/sse",
        headers={
            "Origin": "https://claude.ai",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code in (200, 204)
```

- [ ] **Step 10: Create `src/fastmcp_remote/templates/tests/test_telemetry.py`**

```python
import json

import pytest

from src.core.telemetry import TelemetryEvent, hash_token, telemetry_service


def test_hash_token_stable_for_same_token():
    a = hash_token("Bearer abc123")
    b = hash_token("Bearer abc123")
    assert a == b
    assert len(a) == 16


def test_hash_token_different_for_different_tokens():
    assert hash_token("Bearer abc") != hash_token("Bearer def")


def test_hash_token_strips_bearer_prefix():
    assert hash_token("Bearer abc123") == hash_token("abc123")


def test_hash_token_anonymous_for_empty():
    assert hash_token("") == "anonymous"
    assert hash_token("Bearer ") == "anonymous"


def test_hash_token_does_not_contain_raw_token():
    raw = "supersecrettoken_xyz"
    h = hash_token(f"Bearer {raw}")
    assert raw not in h
    assert "Bearer" not in h


def test_event_json_excludes_none_fields():
    e = TelemetryEvent(event_type="connection", user_id="abc", path="/sse")
    payload = e.model_dump_json(exclude_none=True)
    parsed = json.loads(payload)
    assert parsed["event_type"] == "connection"
    assert "tool_name" not in parsed


@pytest.mark.asyncio
async def test_record_event_no_raise_when_disabled():
    e = TelemetryEvent(event_type="connection", user_id="abc")
    await telemetry_service.record_event(e)
```

- [ ] **Step 11: Copy `.gitignore` from eninesites_mcp**

```bash
cp /Users/pushpendratripathi/Workspace/1e9advisors/eninesites_mcp/.gitignore \
   src/fastmcp_remote/templates/.gitignore
```

- [ ] **Step 12: Copy `.pylintrc` from eninesites_mcp**

```bash
cp /Users/pushpendratripathi/Workspace/1e9advisors/eninesites_mcp/.pylintrc \
   src/fastmcp_remote/templates/.pylintrc
```

---

## Task 5: Jinja2 templates — errors, utils, formatters

**Files:**
- Create: `src/fastmcp_remote/templates/src/core/errors.py.j2`
- Create: `src/fastmcp_remote/templates/src/core/utils.py.j2`
- Create: `src/fastmcp_remote/templates/src/core/formatters.py.j2`

- [ ] **Step 1: Create `src/fastmcp_remote/templates/src/core/errors.py.j2`**

```python
from typing import Optional


class {{ class_prefix }}Error(Exception):
    http_status: int = 500
    error_code: str = "{{ project_slug | upper }}_ERROR"

    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.details = details

    def to_dict(self) -> dict:
        d = {"error": self.error_code, "message": str(self)}
        if self.details:
            d["details"] = self.details
        return d

    def to_mcp_string(self) -> str:
        msg = f"❌ **{self.error_code}**: {self}"
        if self.details:
            msg += f"\n\n**Details**: {self.details}"
        return msg


class AuthError({{ class_prefix }}Error):
    http_status = 401
    error_code = "AUTH_ERROR"

    def to_mcp_string(self) -> str:
        return (
            f"🔐 **Authentication Required**\n\n"
            f"{self}\n\n"
            f"**How to fix**: Pass your API token in the "
            f"`Authorization: Bearer <token>` header."
        )


class PermissionError({{ class_prefix }}Error):
    http_status = 403
    error_code = "PERMISSION_DENIED"

    def to_mcp_string(self) -> str:
        return (
            f"🚫 **Insufficient Permissions**\n\n"
            f"{self}\n\n"
            f"Your account may not include access to this resource."
        )


class ValidationError({{ class_prefix }}Error):
    http_status = 422
    error_code = "VALIDATION_ERROR"


class BackendError({{ class_prefix }}Error):
    http_status = 502
    error_code = "BACKEND_ERROR"


class RateLimitError({{ class_prefix }}Error):
    http_status = 429
    error_code = "RATE_LIMITED"

    def to_mcp_string(self) -> str:
        return (
            "⚡ **Rate Limited**\n\n"
            "Too many requests. Please wait a moment before retrying."
        )
```

- [ ] **Step 2: Create `src/fastmcp_remote/templates/src/core/utils.py.j2`**

```python
import logging
from functools import wraps
from typing import Any, Tuple

from fastmcp import Context

from src.core.app_state import get_http_client
from src.core.auth import extract_bearer_token
from src.core.errors import {{ class_prefix }}Error
from src.core.formatters import format_error

logger = logging.getLogger(__name__)


def tool_handler(func):
    """Decorator for tool functions: unified error handling + telemetry."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        ctx = kwargs.get("ctx")
        if not ctx:
            ctx = next((a for a in args if isinstance(a, Context)), None)

        from time import perf_counter

        from src.core.auth import extract_bearer_token
        from src.core.telemetry import TelemetryEvent, hash_token, telemetry_service

        start_time = perf_counter()
        user_id = "anonymous"

        try:
            if ctx:
                auth_header = extract_bearer_token(ctx)
                user_id = hash_token(auth_header)
        except Exception:
            pass

        try:
            result = await func(*args, **kwargs)
            latency_ms = (perf_counter() - start_time) * 1000

            await telemetry_service.record_event(
                TelemetryEvent(
                    event_type="tool_call",
                    user_id=user_id,
                    tool_name=func.__name__,
                    success=True,
                    latency_ms=round(latency_ms, 2),
                    response_size_bytes=len(str(result)),
                )
            )
            return result

        except {{ class_prefix }}Error as e:
            latency_ms = (perf_counter() - start_time) * 1000
            await telemetry_service.record_event(
                TelemetryEvent(
                    event_type="tool_call",
                    user_id=user_id,
                    tool_name=func.__name__,
                    success=False,
                    error_type=e.__class__.__name__,
                    latency_ms=round(latency_ms, 2),
                )
            )
            if ctx:
                await ctx.error(str(e))
            return format_error(e)

        except (RuntimeError, TypeError, ValueError, KeyError, AttributeError) as e:
            latency_ms = (perf_counter() - start_time) * 1000
            await telemetry_service.record_event(
                TelemetryEvent(
                    event_type="tool_call",
                    user_id=user_id,
                    tool_name=func.__name__,
                    success=False,
                    error_type=e.__class__.__name__,
                    latency_ms=round(latency_ms, 2),
                )
            )
            logger.exception("Unexpected error in %s: %s", func.__name__, e)
            return format_error(e)

    return wrapper


async def prepare_tool(ctx: Context) -> Tuple[Any, str]:
    """Common tool preamble: returns (http_client, auth_header). Use for API proxy tools."""
    client = get_http_client(ctx)
    auth_header = extract_bearer_token(ctx)
    return client, auth_header
```

- [ ] **Step 3: Create `src/fastmcp_remote/templates/src/core/formatters.py.j2`**

```python
from src.core.errors import {{ class_prefix }}Error


def format_error(error: Exception) -> str:
    """Format a {{ class_prefix }}Error (or any exception) as a Markdown string for MCP tools."""
    if isinstance(error, {{ class_prefix }}Error):
        return error.to_mcp_string()
    return f"❌ **Unexpected Error**: {error}"
```

- [ ] **Step 4: Run scaffold substitution tests**

```bash
pytest tests/test_scaffold.py::test_scaffold_substitutes_class_prefix_in_errors \
       tests/test_scaffold.py::test_scaffold_substitutes_class_prefix_in_utils \
       -v
```

Expected: PASS (these two tests should now pass)

---

## Task 6: Jinja2 templates — telemetry, settings, server

**Files:**
- Create: `src/fastmcp_remote/templates/src/core/telemetry.py.j2`
- Create: `src/fastmcp_remote/templates/src/config/settings.py.j2`
- Create: `src/fastmcp_remote/templates/src/server.py.j2`

- [ ] **Step 1: Create `src/fastmcp_remote/templates/src/core/telemetry.py.j2`**

```python
import hashlib
import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.config.settings import settings

logger = logging.getLogger(__name__)


class TelemetryEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str
    user_id: Optional[str] = None
    tool_name: Optional[str] = None
    success: Optional[bool] = None
    error_type: Optional[str] = None
    latency_ms: Optional[float] = None
    response_size_bytes: Optional[int] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    path: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


def hash_token(token: str) -> str:
    """Hash an OAuth token to a stable 16-char identifier. Original is not recoverable."""
    if not token:
        return "anonymous"
    raw = token[7:].strip() if token.lower().startswith("bearer ") else token.strip()
    if not raw:
        return "anonymous"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class TelemetryService:
    _instance: Optional["TelemetryService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.enabled = settings.telemetry_enabled
        self._telemetry_logger: Optional[logging.Logger] = None

        if self.enabled:
            self._setup_logger()

        self._initialized = True

    def _setup_logger(self):
        log_path = Path(settings.telemetry_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        self._telemetry_logger = logging.getLogger("{{ project_slug }}_telemetry")
        self._telemetry_logger.setLevel(logging.INFO)
        self._telemetry_logger.propagate = False

        if any(
            getattr(h, "_{{ project_slug }}_telemetry", False)
            for h in self._telemetry_logger.handlers
        ):
            return

        handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=settings.telemetry_max_bytes,
            backupCount=settings.telemetry_backup_count,
        )
        handler._{{ project_slug }}_telemetry = True  # type: ignore[attr-defined]
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._telemetry_logger.addHandler(handler)

        logger.info("Telemetry service initialised at %s", log_path)

    async def record_event(self, event: TelemetryEvent) -> None:
        if not self.enabled or not self._telemetry_logger:
            return
        try:
            self._telemetry_logger.info(event.model_dump_json(exclude_none=True))
        except Exception as e:
            logger.debug("Failed to record telemetry event: %s", e)


telemetry_service = TelemetryService()
```

- [ ] **Step 2: Create `src/fastmcp_remote/templates/src/config/settings.py.j2`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    host: str = "127.0.0.1"
    port: int = 8001
    log_level: str = "INFO"
    log_dir: str = "logs"

    # MCP / OAuth discovery
    mcp_public_url: str = "http://localhost:8001/mcp"
    oauth_issuer_url: str = "http://localhost:8001"
    logo_uri: str = ""   # omitted from OAuth discovery response when empty

    # API backend — optional, only needed for HTTP proxy tools
    api_base_url: str = "https://api.example.com"
    user_agent: str = "{{ project_slug }}-mcp/1.0"

    # Auth probe — opt-in: validates Bearer token on SSE handshake via backend call
    auth_probe_path: str = "/health/"
    auth_probe_enabled: bool = False

    # HTTP client
    http_timeout: float = 90.0
    http_max_connections: int = 100
    http_max_keepalive: int = 20
    allowed_origins: str = "https://claude.ai,https://chatgpt.com,https://cursor.sh"

    # Telemetry
    telemetry_enabled: bool = True
    telemetry_log_path: str = "logs/telemetry.jsonl"
    telemetry_max_bytes: int = 52428800   # 50 MB
    telemetry_backup_count: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
```

- [ ] **Step 3: Create `src/fastmcp_remote/templates/src/server.py.j2`**

```python
import logging
import logging.handlers
import os
from pathlib import Path

import httpx
import uvicorn
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates

from src.config.settings import settings
from src.core.app_state import lifespan

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
logger = logging.getLogger(__name__)


def configure_logging() -> None:
    os.makedirs(settings.log_dir, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if any(getattr(h, "_{{ project_slug }}", False) for h in root.handlers):
        return

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch._{{ project_slug }} = True  # type: ignore[attr-defined]
    root.addHandler(ch)

    fh = logging.handlers.RotatingFileHandler(
        os.path.join(settings.log_dir, "{{ project_slug }}_mcp.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    fh.setFormatter(fmt)
    fh._{{ project_slug }} = True  # type: ignore[attr-defined]
    root.addHandler(fh)


configure_logging()


mcp = FastMCP(
    "{{ service_name }}",
    instructions="""You are connected to the {{ service_name }} MCP server.

## Authentication
All tools require an OAuth Bearer token in the `Authorization: Bearer <token>` header.
""",
    lifespan=lifespan,
)

from src.tools.example import example_router
mcp.mount(example_router)


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "{{ service_name }} MCP", "version": "0.1.0"})


async def oauth_protected_resource(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "resource": settings.mcp_public_url.rstrip("/"),
            "authorization_servers": [settings.oauth_issuer_url.rstrip("/")],
            "bearer_methods_supported": ["header"],
            "scopes_supported": ["read"],
        }
    )


async def root_ui(request: Request):
    from datetime import datetime

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "year": datetime.now().year,
            "mcp_public_url": settings.mcp_public_url.rstrip("/mcp").rstrip("/sse").rstrip("/"),
        },
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


class RequireAuthMiddleware(BaseHTTPMiddleware):
    """
    Enforce OAuth authentication on all requests except health, well-known, root, and OPTIONS.
    If auth_probe_enabled=True, validates the token against the backend on SSE handshake.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if (
            path == "/"
            or path.startswith("/health")
            or ".well-known" in path
            or any(x in path for x in ["favicon", "apple-touch-icon", "android-chrome"])
        ):
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing Authorization header. Token is required."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        if settings.auth_probe_enabled and request.method == "GET" and path.rstrip("/") == "/sse":
            probe_url = f"{settings.api_base_url.rstrip('/')}{settings.auth_probe_path}"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        probe_url,
                        headers={"Authorization": auth_header},
                    )
                    if response.status_code == 401:
                        logger.warning("Rejecting invalid/expired token during handshake.")
                        return JSONResponse(
                            status_code=401,
                            content={
                                "error": "Invalid or expired token. Please authenticate again."
                            },
                            headers={"WWW-Authenticate": "Bearer"},
                        )
            except httpx.RequestError as e:
                logger.error("Network error validating token during handshake: %s", e)
                return JSONResponse(
                    status_code=503,
                    content={"error": f"Token validation unavailable: {e}"},
                )

        return await call_next(request)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Record connection-level events (auth failures, rate limits, SSE connects)."""

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


def _allowed_origins() -> list[str]:
    raw = (settings.allowed_origins or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app():
    logger.info("{{ service_name }} MCP starting...")

    mcp_app = mcp.http_app(path="/sse")

    _app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route(
                "/.well-known/oauth-protected-resource",
                oauth_protected_resource,
                methods=["GET"],
            ),
            Route(
                "/.well-known/oauth-protected-resource/sse",
                oauth_protected_resource,
                methods=["GET"],
            ),
            Route(
                "/sse/.well-known/oauth-protected-resource",
                oauth_protected_resource,
                methods=["GET"],
            ),
            Route(
                "/.well-known/oauth-authorization-server",
                oauth_discovery,
                methods=["GET"],
            ),
            Route(
                "/.well-known/oauth-authorization-server/sse",
                oauth_discovery,
                methods=["GET"],
            ),
            Route(
                "/sse/.well-known/oauth-authorization-server",
                oauth_discovery,
                methods=["GET"],
            ),
            Route("/.well-known/openid-configuration", oauth_discovery, methods=["GET"]),
            Route("/.well-known/openid-configuration/sse", oauth_discovery, methods=["GET"]),
            Route("/sse/.well-known/openid-configuration", oauth_discovery, methods=["GET"]),
            Route("/", root_ui, methods=["GET"]),
        ],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=_allowed_origins(),
                allow_methods=["*"],
                allow_headers=["*"],
            ),
            Middleware(RequireAuthMiddleware),
            Middleware(TelemetryMiddleware),
        ],
        lifespan=mcp_app.lifespan,
    )

    _app.routes.append(Mount("/", app=mcp_app))
    return _app


app = create_app()


def run():
    uvicorn.run(
        "src.server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        lifespan="on",
        reload=True,
    )


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Run substitution tests for these files**

```bash
pytest tests/test_scaffold.py::test_scaffold_substitutes_service_name_in_server \
       tests/test_scaffold.py::test_scaffold_substitutes_project_slug_in_telemetry \
       -v
```

Expected: PASS

---

## Task 7: Jinja2 templates — pyproject, env.example, DEPLOYMENT.md, index.html

**Files:**
- Create: `src/fastmcp_remote/templates/pyproject.toml.j2`
- Create: `src/fastmcp_remote/templates/env.example.j2`
- Create: `src/fastmcp_remote/templates/DEPLOYMENT.md.j2`
- Create: `src/fastmcp_remote/templates/templates/index.html.j2`

- [ ] **Step 1: Create `src/fastmcp_remote/templates/pyproject.toml.j2`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{{ project_name }}"
version = "0.1.0"
description = "{{ service_name }} MCP server"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
keywords = ["mcp", "{{ project_name }}"]
dependencies = [
    "fastmcp>=3.0",
    "httpx>=0.28.1",
    "pydantic>=2.11",
    "pydantic-settings>=2.9",
    "uvicorn[standard]>=0.34",
    "tenacity>=9.0",
    "starlette>=0.47",
    "rich>=14.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.25",
    "respx>=0.22",
    "httpx",
    "pytest-cov>=6",
]

[project.scripts]
{{ project_slug }} = "src.server:run"

[tool.setuptools]
packages = [
    "src",
    "src.config",
    "src.core",
    "src.tools",
    "src.resources",
    "src.skills",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.isort]
profile = "black"
line_length = 100
```

- [ ] **Step 2: Create `src/fastmcp_remote/templates/env.example.j2`**

```
HOST=127.0.0.1
PORT=8001
LOG_LEVEL=INFO

MCP_PUBLIC_URL=https://mcp.example.com/mcp
OAUTH_ISSUER_URL=https://your-auth-server.com

# Only needed for HTTP proxy tools
# API_BASE_URL=https://api.example.com

# Opt-in: validate Bearer token on SSE handshake (requires API_BASE_URL)
# AUTH_PROBE_ENABLED=true
# AUTH_PROBE_PATH=/health/

TELEMETRY_ENABLED=true
ALLOWED_ORIGINS=https://claude.ai,https://chatgpt.com,https://cursor.sh
```

- [ ] **Step 3: Create `src/fastmcp_remote/templates/DEPLOYMENT.md.j2`**

```markdown
# Production Deployment Guide — {{ service_name }} MCP

## Requirements
- Python 3.12+
- Ubuntu 22.04+ / macOS

## Install

```bash
cd /opt/{{ project_name }}
python3 -m venv venv
source venv/bin/activate
pip install .
cp env.example .env
# Edit .env with production values
```

## Systemd

`/etc/systemd/system/{{ project_name }}.service`:

```ini
[Unit]
Description={{ service_name }} MCP Server
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/{{ project_name }}
EnvironmentFile=/opt/{{ project_name }}/.env
ExecStart=/opt/{{ project_name }}/venv/bin/uvicorn asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --lifespan on \
    --proxy-headers \
    --forwarded-allow-ips='*'
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable {{ project_name }}
sudo systemctl start {{ project_name }}
```

## Nginx (SSL/Reverse Proxy)

```nginx
server {
    listen 80;
    server_name mcp.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

## Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install .
COPY asgi.py .
COPY templates/ templates/
CMD ["uvicorn", "asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--lifespan", "on"]
```

## Health Check

```
GET /health → {"status": "ok", "service": "{{ service_name }} MCP", "version": "0.1.0"}
```

## Logs
- Application: `logs/{{ project_slug }}_mcp.log`
- Telemetry: `logs/telemetry.jsonl`
```

- [ ] **Step 4: Create `src/fastmcp_remote/templates/templates/index.html.j2`**

The `{% raw %}` blocks prevent scaffold-time Jinja2 from consuming `{{ mcp_public_url }}` and `{{ year }}`, which are Starlette template variables rendered at request time.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ service_name }} MCP</title>
    <meta name="description" content="Connect {{ service_name }} to Claude, Cursor, or any MCP-compatible AI tool.">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        :root {
            --primary: #1a56db; --primary-hover: #1648c2;
            --charcoal: #212529; --grey: #6c757d;
            --border: #dee2e6; --white: #ffffff;
            --light-bg: #f0f4ff;
            --hero-grad: linear-gradient(170deg, #ffffff 0%, #e8eeff 60%, #d8e4ff 100%);
        }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', system-ui, sans-serif; font-size: 16px; line-height: 1.6; color: var(--charcoal); background: var(--white); }
        .container { max-width: 1140px; margin: 0 auto; padding: 0 2.7rem; }
        header { position: sticky; top: 0; z-index: 100; background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); border-bottom: 1px solid var(--border); }
        .header-inner { display: flex; align-items: center; justify-content: space-between; padding: 0.9rem 0; }
        .logo-link { display: flex; align-items: center; text-decoration: none; font-size: 1.1rem; font-weight: 700; color: var(--charcoal); }
        .nav-right { display: flex; align-items: center; gap: 1.5rem; }
        .nav-right a { font-size: 0.95rem; font-weight: 500; color: var(--charcoal); text-decoration: none; }
        .nav-right a:hover { color: var(--primary); }
        .btn-primary { display: inline-block; background: var(--primary); color: #fff; font-weight: 600; padding: 0.65rem 1.75rem; border-radius: 720px; text-decoration: none; }
        .btn-primary:hover { background: var(--primary-hover); }
        .hero { background: var(--hero-grad); padding: 5.5rem 0 4.5rem; }
        .hero h1 { font-size: 2.75rem; font-weight: 700; line-height: 1.2; margin-bottom: 1.25rem; max-width: 680px; }
        .hero p { font-size: 1.1rem; color: var(--grey); max-width: 600px; margin-bottom: 2rem; }
        main { background: var(--light-bg); }
        .content-area { padding: 3rem 0 5rem; }
        .card { background: var(--white); border: 1px solid var(--border); border-radius: 6px; padding: 2.5rem 2.75rem; margin-bottom: 1.5rem; }
        .card h2 { font-size: 1.35rem; font-weight: 700; margin-bottom: 0.75rem; }
        .card h3 { font-size: 1.05rem; font-weight: 600; margin-top: 2rem; margin-bottom: 0.5rem; }
        .card p { color: var(--grey); font-size: 0.97rem; margin-bottom: 1rem; }
        .card ol, .card ul { color: var(--grey); font-size: 0.97rem; padding-left: 1.4rem; margin-bottom: 1.25rem; }
        .card li { margin-bottom: 0.4rem; }
        .card strong { color: var(--charcoal); }
        code { font-family: monospace; font-size: 0.88em; background: #f1f3f5; color: #c2185b; padding: 0.15rem 0.4rem; border-radius: 4px; }
        .code-block { background: #212529; color: #f8f9fa; border-radius: 6px; padding: 1.25rem 1.5rem; overflow-x: auto; margin: 0.75rem 0 1.25rem; }
        .code-block pre { margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 0.88rem; line-height: 1.6; }
        footer { background: var(--white); border-top: 1px solid var(--border); padding: 2.5rem 0; }
        .footer-inner { display: flex; align-items: center; justify-content: space-between; font-size: 0.88rem; color: var(--grey); }
    </style>
</head>
<body>
    <header>
        <div class="container header-inner">
            <span class="logo-link">{{ service_name }}</span>
            <nav class="nav-right">
                <a href="#connect" class="btn-primary">Connect Now</a>
            </nav>
        </div>
    </header>

    <section class="hero">
        <div class="container">
            <h1>{{ service_name }}, direct to your AI.</h1>
            <p>Connect {{ service_name }} to Claude, Cursor, or any MCP-compatible tool and access your data directly in your AI workflow.</p>
            <a href="#connect" class="btn-primary">Get Connected →</a>
        </div>
    </section>

    <main>
        <div class="container content-area">
            <div class="card">
                <h2>What is MCP?</h2>
                <p>Model Context Protocol (MCP) is an open standard that lets AI tools connect to external data sources. Once an AI tool supports MCP it can connect to any MCP server with just a URL.</p>
            </div>

            <div id="connect" class="card">
                <h2>How to Connect</h2>

                <h3>1. Claude.ai (Web)</h3>
                <ol>
                    <li>Go to <strong>Settings → Connectors</strong>.</li>
                    <li>Click <strong>Add → Custom → Web</strong>.</li>
                    <li>Name: <code>{{ service_name }}</code></li>
                    <li>Remote MCP Server URL: <code>{% raw %}{{ mcp_public_url }}{% endraw %}/sse</code></li>
                    <li>Click <strong>Connect</strong> and follow the OAuth flow.</li>
                </ol>

                <h3>2. Claude Desktop</h3>
                <p>Add to <code>claude_desktop_config.json</code>:</p>
                <div class="code-block"><pre>{
  "mcpServers": {
    "{{ service_name }}": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "{% raw %}{{ mcp_public_url }}{% endraw %}/sse"]
    }
  }
}</pre></div>

                <h3>3. Claude Code (CLI)</h3>
                <div class="code-block"><pre>claude mcp add {{ project_name }} --transport http {% raw %}{{ mcp_public_url }}{% endraw %}/sse</pre></div>

                <h3>4. Other MCP Clients</h3>
                <div class="code-block"><pre>{% raw %}{{ mcp_public_url }}{% endraw %}/sse</pre></div>
            </div>
        </div>
    </main>

    <footer>
        <div class="container footer-inner">
            <span>&copy; {% raw %}{{ year }}{% endraw %} {{ service_name }}. All rights reserved.</span>
        </div>
    </footer>
</body>
</html>
```

- [ ] **Step 5: Run the full scaffold test suite**

```bash
pytest tests/test_scaffold.py -v
```

Expected: All tests PASS.

---

## Task 8: Implement CLI

**Files:**
- Create: `src/fastmcp_remote/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI test first**

Create `tests/test_cli.py`:

```python
from typer.testing import CliRunner
from fastmcp_remote.cli import app

runner = CliRunner()


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_new_command_creates_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new", "my-server"], input="My Server\n")
    assert result.exit_code == 0
    assert (tmp_path / "my-server").is_dir()
    assert (tmp_path / "my-server" / "src" / "server.py").exists()
    assert (tmp_path / "my-server" / "pyproject.toml").exists()


def test_new_command_uses_default_service_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new", "cool-api"], input="\n")  # accept default
    assert result.exit_code == 0
    pyproject = (tmp_path / "cool-api" / "pyproject.toml").read_text()
    assert 'name = "cool-api"' in pyproject


def test_new_command_fails_if_dir_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "existing").mkdir()
    result = runner.invoke(app, ["new", "existing"], input="Existing\n")
    assert result.exit_code != 0
    assert "already exists" in result.output.lower() or "Error" in result.output


def test_new_command_interactive_no_arg(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["new"], input="my-interactive-project\nMy Service\n")
    assert result.exit_code == 0
    assert (tmp_path / "my-interactive-project").is_dir()
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
pytest tests/test_cli.py -v
```

Expected: `ImportError: cannot import name 'app' from 'fastmcp_remote.cli'`

- [ ] **Step 3: Create `src/fastmcp_remote/cli.py`**

```python
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt

from fastmcp_remote import __version__
from fastmcp_remote.scaffold import scaffold_project

app = typer.Typer(
    name="fastmcp-remote",
    help="Scaffold a production-ready remote MCP server.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"fastmcp-remote {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    pass


def _derive_context(project_name: str, service_name: str) -> dict:
    project_slug = project_name.replace("-", "_")
    class_prefix = "".join(w.capitalize() for w in project_name.split("-"))
    return {
        "project_name": project_name,
        "project_slug": project_slug,
        "service_name": service_name,
        "class_prefix": class_prefix,
    }


@app.command()
def new(
    project_name: Optional[str] = typer.Argument(
        None, help="Project name (kebab-case). Used as directory name."
    ),
):
    """Scaffold a new production-ready remote MCP server."""
    if not project_name:
        project_name = Prompt.ask("Project name", default="my-project")

    default_service = " ".join(w.capitalize() for w in project_name.split("-"))
    service_name = Prompt.ask("Service name", default=default_service)

    target = Path.cwd() / project_name
    context = _derive_context(project_name, service_name)

    console.print(f"\nScaffolding [bold]{project_name}[/bold]...", end=" ")

    try:
        scaffold_project(target, context)
    except FileExistsError as e:
        console.print("")
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    console.print("[green]✓[/green]\n")
    console.print("[bold]Done! Next steps:[/bold]")
    console.print(f"  cd {project_name}")
    console.print("  python -m venv venv && source venv/bin/activate")
    console.print('  pip install -e ".[dev]"')
    console.print("  cp env.example .env")
    console.print("  uvicorn asgi:application --reload --port 8001 --lifespan on")
    console.print("")
```

- [ ] **Step 4: Run CLI tests — verify they PASS**

```bash
pytest tests/test_cli.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Smoke-test the CLI manually**

```bash
cd /tmp && fastmcp-remote new smoke-test
# Enter "Smoke Test" as service name
ls smoke-test/
pytest smoke-test/  # run the generated project's own tests (will fail due to missing deps — that's OK)
rm -rf /tmp/smoke-test
```

---

## Task 9: Full test run

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests PASS. Output ends with `X passed`.

- [ ] **Step 2: Verify no eninesites references in source**

```bash
grep -r "eninesites\|EnineSites" src/ tests/ --include="*.py" --include="*.toml" --include="*.j2"
```

Expected: zero matches.

---

## Task 10: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
# fastmcp-remote

One command to a production-ready remote MCP server.

```bash
pip install fastmcp-remote
fastmcp-remote new my-project
```

Two prompts. A fully working server.

---

## What you get

- **OAuth pass-through** — Bearer token extracted from request, forwarded to your backend. No token storage, no session state.
- **RFC 8414 / RFC 9728** — OAuth discovery endpoints served automatically.
- **Auth middleware** — All endpoints require Authorization header. Health and `.well-known` endpoints are open.
- **Optional auth probe** — Set `AUTH_PROBE_ENABLED=true` to validate tokens against your backend on SSE handshake.
- **Telemetry** — Anonymized JSONL log of tool calls, auth failures, connections. Token hashed via SHA-256, never stored raw.
- **Retry logic** — Transient backend failures (5xx, connect errors, timeouts) retried up to 3× with exponential backoff.
- **Shared HTTP client** — One `httpx.AsyncClient` per worker, created at startup. No per-request connection churn.
- **Landing page** — Jinja2 HTML page at `/` with connection instructions.
- **Working tests** — 3 test files pass immediately with zero configuration.

---

## Install

```bash
# Recommended — keeps CLI isolated
pipx install fastmcp-remote

# Or
pip install fastmcp-remote
```

Requires Python 3.12+.

---

## Quickstart

```bash
fastmcp-remote new my-project
cd my-project
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
cp env.example .env
uvicorn asgi:application --reload --port 8001 --lifespan on
```

```bash
# Verify
curl http://localhost:8001/health
# {"status": "ok", "service": "My Project MCP", "version": "0.1.0"}

curl http://localhost:8001/.well-known/oauth-authorization-server
# {"issuer": "http://localhost:8001", ...}

curl http://localhost:8001/sse
# 401 — {"error": "Missing Authorization header. Token is required."}
```

---

## Adding your first tool

```python
# src/tools/my_tool.py
from fastmcp import Context, FastMCP
from src.core.utils import tool_handler

my_router = FastMCP("my-tool")

@my_router.tool()
@tool_handler
async def get_data(item_id: str, ctx: Context) -> str:
    # For API proxy tools, use prepare_tool():
    # from src.core.utils import prepare_tool
    # from src.core.http_client import api_get
    # client, auth_header = await prepare_tool(ctx)
    # data = await api_get(client, f"/api/items/{item_id}", auth_header)
    return f"Got item {item_id}"
```

Mount in `src/server.py`:
```python
from src.tools.my_tool import my_router
mcp.mount(my_router)
```

---

## Configuration reference

All settings are environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Bind host |
| `PORT` | `8001` | Bind port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MCP_PUBLIC_URL` | `http://localhost:8001/mcp` | Public MCP URL (in OAuth discovery) |
| `OAUTH_ISSUER_URL` | `http://localhost:8001` | OAuth issuer URL |
| `LOGO_URI` | `` | Logo URL (omitted from OAuth discovery if empty) |
| `API_BASE_URL` | `https://api.example.com` | Backend URL (for HTTP proxy tools) |
| `AUTH_PROBE_ENABLED` | `false` | Validate token on SSE handshake |
| `AUTH_PROBE_PATH` | `/health/` | Probe endpoint (requires `API_BASE_URL`) |
| `HTTP_TIMEOUT` | `90.0` | HTTP client timeout (seconds) |
| `TELEMETRY_ENABLED` | `true` | Enable JSONL telemetry |
| `ALLOWED_ORIGINS` | `https://claude.ai,...` | CORS allowed origins |

---

## Generated project structure

```
my-project/
├── src/
│   ├── server.py        # FastMCP root, middleware stack, routes
│   ├── config/
│   │   └── settings.py  # All configuration (Pydantic BaseSettings)
│   ├── core/
│   │   ├── auth.py      # extract_bearer_token()
│   │   ├── errors.py    # MyProjectError hierarchy
│   │   ├── http_client.py  # api_get, api_post + retry
│   │   ├── telemetry.py    # Anonymized JSONL telemetry
│   │   └── utils.py     # @tool_handler, prepare_tool()
│   └── tools/
│       └── example.py   # echo tool — shows @tool_handler pattern
├── tests/               # 3 tests pass out of the box
├── asgi.py              # Production ASGI entry point
└── env.example
```

---

## License

MIT
```

---

## Task 11: GitHub Actions

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```bash
mkdir -p .github/workflows
```

```yaml
name: CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: pytest tests/ -v --tb=short
```

- [ ] **Step 2: Create `.github/workflows/publish.yml`**

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install hatch
        run: pip install hatch

      - name: Build
        run: hatch build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 3: Final full test run**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Verify CLI end-to-end from the package**

```bash
fastmcp-remote --version
# fastmcp-remote 0.1.0

cd /tmp && fastmcp-remote new final-test
# Project name: final-test (or just hit Enter)
# Service name: Final Test (or just hit Enter)
ls final-test/
# asgi.py  DEPLOYMENT.md  env.example  pyproject.toml  src/  tests/  templates/
cat final-test/src/core/errors.py | grep "class.*Error"
# class FinalTestError(Exception):
# class AuthError(FinalTestError):
# ...
rm -rf /tmp/final-test
```

---

## Self-Review Notes

- `index.html.j2` uses `{% raw %}` to pass Starlette vars (`{{ mcp_public_url }}`, `{{ year }}`) through scaffold-time Jinja2 rendering unchanged.
- `telemetry.py.j2` uses `handler._{{ project_slug }}_telemetry = True` — rendered to valid Python attribute name (e.g. `handler._my_project_telemetry = True`).
- `server.py.j2` uses `ch._{{ project_slug }} = True` — same pattern, valid after rendering.
- `test_scaffold_no_partial_write_on_error` passes because `scaffold_project` checks `target_dir.exists()` before creating it. The empty pre-created dir has no files written into it.
- Generated `tests/test_telemetry.py` uses `telemetry_service` singleton — safe because tests don't reset it, and `record_event` is no-op-safe when telemetry is disabled.
