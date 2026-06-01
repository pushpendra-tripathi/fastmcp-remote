# fastmcp-remote — Design Spec

**Date:** 2026-05-31
**Status:** Approved
**Author:** Pushpendra Tripathi
**Repo:** github.com/pushpendra-tripathi/fastmcp-remote

---

## Problem

Building a production-ready remote MCP server requires solving the same hard problems every time: OAuth pass-through auth, RFC 8414/9728 discovery endpoints, auth handshake validation, telemetry, retry logic, shared HTTP client pooling, structured errors, and a test suite that passes on day one.

FastMCP's own CLI has no `new`/`init` command for servers. Render's one-click templates are explicitly not production-ready for OAuth. Nothing exists that generates a working remote MCP server from a single command.

---

## Solution

`fastmcp-remote` — a PyPI-published CLI tool. Two prompts, one command, a fully working remote MCP server.

```bash
pip install fastmcp-remote   # or pipx install fastmcp-remote
fastmcp-remote new my-project
```

---

## Approach: Pure Scaffold (Copy-on-Create)

Generated projects have **no runtime dependency on `fastmcp-remote`**. All infrastructure files are rendered from Jinja2 templates and written into the new project directory. The user owns every line of code.

Rationale: Auth/telemetry code is not framework internals — it's the core of the server. Users need to read, audit, and modify it. Copy-on-create keeps it auditable and dependency-free.

---

## Architecture: `fastmcp-remote` Package

```
fastmcp-remote/
├── src/
│   └── fastmcp_remote/
│       ├── __init__.py
│       ├── cli.py                   # typer app — `new` command entry point
│       ├── scaffold.py              # walks templates/, renders .j2, copies verbatim
│       └── templates/
│           ├── src/
│           │   ├── __init__.py
│           │   ├── server.py.j2
│           │   ├── config/
│           │   │   ├── __init__.py
│           │   │   └── settings.py.j2
│           │   ├── core/
│           │   │   ├── __init__.py
│           │   │   ├── app_state.py          # verbatim
│           │   │   ├── auth.py               # verbatim
│           │   │   ├── errors.py.j2          # class_prefix substitution
│           │   │   ├── formatters.py         # verbatim
│           │   │   ├── http_client.py        # verbatim
│           │   │   ├── telemetry.py          # verbatim
│           │   │   └── utils.py              # verbatim
│           │   ├── tools/
│           │   │   ├── __init__.py
│           │   │   └── example.py.j2
│           │   ├── resources/
│           │   │   └── __init__.py
│           │   └── skills/
│           │       └── __init__.py
│           ├── tests/
│           │   ├── conftest.py.j2
│           │   ├── test_auth.py              # verbatim
│           │   ├── test_middleware.py.j2
│           │   └── test_telemetry.py.j2
│           ├── templates/
│           │   └── index.html.j2
│           ├── asgi.py                       # verbatim
│           ├── pyproject.toml.j2
│           ├── env.example.j2
│           ├── .gitignore                    # verbatim
│           ├── .pylintrc                     # verbatim
│           └── DEPLOYMENT.md.j2
├── tests/
│   └── test_scaffold.py
├── pyproject.toml                            # hatch build backend
└── README.md
```

**Template rendering rule:**
- Files ending in `.j2` → rendered with Jinja2 context, written without the `.j2` extension
- All other files → copied verbatim, byte-identical

---

## CLI UX

**Install:**
```bash
pipx install fastmcp-remote   # recommended
# or
pip install fastmcp-remote
```

**Scaffold:**
```bash
fastmcp-remote new my-project
```

**Interactive prompts (typer + rich):**
```
 FastMCP Remote Server Generator

 Project name    [my-project]:
 Service name    [My Project]:
```

Two prompts only. Project name drives directory name, package slug, entry point.
Service name drives `FastMCP("My Project")`, landing page, error class prefix.

**Post-scaffold output:**
```
 Scaffolding my-project...  ✓

 Done! Next steps:
   cd my-project
   python -m venv venv && source venv/bin/activate
   pip install -e ".[dev]"
   cp env.example .env
   uvicorn asgi:application --reload --port 8001 --lifespan on
```

**Additional commands:**
```bash
fastmcp-remote --version
fastmcp-remote --help
```

---

## Jinja2 Template Context

```python
{
    "project_slug": "my_project",      # snake_case — package name, imports
    "project_name": "my-project",      # kebab-case — dir name, pyproject name
    "service_name": "My Project",      # human name — FastMCP(), landing page
    "class_prefix": "MyProject",       # PascalCase — error class names
}
```

Derived automatically from the two prompts:
- `project_slug` = `project_name.replace("-", "_")`
- `class_prefix` = `"".join(w.capitalize() for w in project_name.split("-"))`

---

## Generated Project Structure

```
my-project/
├── src/
│   ├── __init__.py
│   ├── server.py              # FastMCP("My Project"), middleware, routes
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── app_state.py       # lifespan, shared httpx.AsyncClient
│   │   ├── auth.py            # extract_bearer_token()
│   │   ├── errors.py          # MyProjectError hierarchy
│   │   ├── formatters.py      # format_error() stub
│   │   ├── http_client.py     # api_get, api_post + tenacity retry
│   │   ├── telemetry.py       # anonymized JSONL telemetry
│   │   └── utils.py           # @tool_handler, prepare_tool()
│   ├── tools/
│   │   ├── __init__.py
│   │   └── example.py         # echo tool — @tool_handler demo
│   ├── resources/
│   │   └── __init__.py
│   └── skills/
│       └── __init__.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_middleware.py
│   └── test_telemetry.py
├── templates/
│   └── index.html
├── asgi.py
├── pyproject.toml
├── env.example
├── .gitignore
├── .pylintrc
└── DEPLOYMENT.md
```

**Not generated:** CLAUDE.md, AGENTS.md, requirements.txt — user's choice.

---

## Generated Settings Design

All env vars have safe defaults. Nothing requires configuration to start the server locally.

```python
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

    # Auth probe — opt-in, validates token on SSE handshake via backend call
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
```

---

## Example Tool (Generated)

Demonstrates `@tool_handler` pattern without assuming any backend:

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

Mounted in `server.py`:
```python
from src.tools.example import example_router
mcp.mount(example_router)
```

---

## Infrastructure Included (Ready to Use, Not Forced)

| Module | What it provides | Required? |
|--------|-----------------|-----------|
| `core/auth.py` | `extract_bearer_token(ctx)` | Yes — used by middleware |
| `core/http_client.py` | `api_get`, `api_post` + retry | No — only for API proxy tools |
| `core/app_state.py` | Shared `httpx.AsyncClient` via lifespan | No — only for API proxy tools |
| `core/errors.py` | `MyProjectError` hierarchy | Yes — used by `@tool_handler` |
| `core/telemetry.py` | Anonymized JSONL event log | Yes — wired into middleware |
| `core/utils.py` | `@tool_handler`, `prepare_tool()` | Yes — decorator for all tools |
| `core/formatters.py` | `format_error()` stub | Yes — used by `@tool_handler` |

---

## Testing

### `fastmcp-remote` package tests (`tests/test_scaffold.py`)

Three scenarios:
1. **Default run** — assert complete file tree, key content substitutions (`MyProject`, `my_project`, `my-project`)
2. **Custom service name** — assert PascalCase derivation correct
3. **Target dir exists** — assert raises error before any files written (atomic: all-or-nothing)

### Generated project tests (ship with every scaffold)

| File | Coverage |
|------|---------|
| `test_auth.py` | `extract_bearer_token` — valid, missing, malformed header |
| `test_middleware.py` | `RequireAuthMiddleware` — 401 on missing token, bypass on health/well-known, passthrough with valid token |
| `test_telemetry.py` | `hash_token` stability, `record_event` never raises |

All three pass `pytest tests/ -v` with zero configuration out of the box.

---

## `fastmcp-remote` Package Metadata

```toml
[project]
name = "fastmcp-remote"
version = "0.1.0"
description = "One command to a production-ready remote MCP server"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Pushpendra Tripathi" }]
keywords = ["mcp", "fastmcp", "remote", "oauth", "scaffold", "cli"]
dependencies = [
    "typer>=0.12",
    "rich>=14.0",
    "jinja2>=3.1",
]

[project.scripts]
fastmcp-remote = "fastmcp_remote.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## CI / Publishing

```
.github/workflows/
├── ci.yml        # pytest on push + PR (Python 3.12, 3.13)
└── publish.yml   # hatch build + PyPI trusted publisher on tag v*
```

PyPI trusted publisher — no stored API tokens. Triggered by `git tag v0.1.0 && git push --tags`.

---

## What's Out of Scope

- `fastmcp-remote update` — no template update propagation (user owns the code)
- `fastmcp-remote add-tool` — no incremental scaffolding
- Non-Python targets
- Copier integration
