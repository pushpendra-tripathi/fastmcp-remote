# remote-mcp

One command to a production-ready remote MCP server.

[![PyPI](https://img.shields.io/pypi/v/remote-mcp)](https://pypi.org/project/remote-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/remote-mcp)](https://pypi.org/project/remote-mcp/)
[![CI](https://github.com/pushpendra-tripathi/remote-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/pushpendra-tripathi/remote-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

Building a remote MCP server means solving the same hard problems every time: OAuth pass-through, RFC 8414/9728 discovery endpoints, middleware stack, telemetry, retry logic, and a test suite that passes on day one.

`remote-mcp` scaffolds all of it from two prompts. Generated projects have **zero runtime dependency** on this package — every file is yours to read, audit, and modify.

## Install

```bash
pipx install remote-mcp   # recommended
# or
pip install remote-mcp
```

## Usage

```bash
remote-mcp new my-project
```

```
  FastMCP Remote Server Generator

  Project name    [my-project]:
  Service name    [My Project]:

  Scaffolding my-project...  ✓

  Done! Next steps:
    cd my-project
    python -m venv venv && source venv/bin/activate
    pip install -e ".[dev]"
    cp env.example .env
    uvicorn asgi:application --reload --port 8001 --lifespan on
```

Server is live at `http://localhost:8001`. MCP endpoint: `http://localhost:8001/sse`.

## What you get

```
my-project/
├── src/
│   ├── server.py              # FastMCP("My Project") instance + tool mounts
│   ├── app.py                 # Starlette factory — routes, middleware, ASGI wiring
│   ├── config/settings.py     # Pydantic BaseSettings — all config via env vars
│   ├── core/
│   │   ├── auth.py            # extract_bearer_token() — OAuth pass-through
│   │   ├── errors.py          # MyProjectError hierarchy
│   │   ├── http_client.py     # api_get/post/patch/put/delete/upload + tenacity retry
│   │   ├── telemetry.py       # anonymized SHA-256 JSONL event log
│   │   └── handlers.py        # @tool_handler decorator, get_client_and_token()
│   ├── middleware/
│   │   ├── auth.py            # RequireAuthMiddleware — Bearer enforcement + probe
│   │   └── telemetry.py       # TelemetryMiddleware — auth failures, connections
│   ├── views/
│   │   ├── health.py          # GET /health
│   │   ├── oauth.py           # RFC 8414 + RFC 9728 discovery endpoints
│   │   └── root.py            # landing page at /
│   └── tools/example.py       # echo tool — your first tool, ready to replace
├── tests/
│   ├── test_auth.py           # extract_bearer_token edge cases
│   ├── test_middleware.py      # auth bypass, 401 on missing token
│   └── test_telemetry.py      # hash_token stability, record_event never raises
├── templates/index.html       # landing page served at /
├── asgi.py                    # production ASGI entrypoint
├── env.example                # all env vars with safe defaults
├── pyproject.toml
└── DEPLOYMENT.md              # Render / Railway / Fly.io deploy guide
```

## Included infrastructure

| Module | What it provides |
|--------|-----------------|
| `core/auth.py` | `extract_bearer_token(ctx)` — forward Bearer token verbatim to your backend |
| `core/http_client.py` | `api_get`, `api_post`, `api_patch`, `api_put`, `api_delete`, `api_upload` — pooled httpx client with tenacity retry |
| `core/errors.py` | `MyProjectError` + Auth, Forbidden, Validation, Backend, RateLimit subclasses |
| `core/telemetry.py` | Rotating JSONL log, user IDs hashed (SHA-256, non-reversible) |
| `core/handlers.py` | `@tool_handler` — catches errors, formats responses, records telemetry |
| `middleware/auth.py` | CORS → Auth → optional backend token probe on SSE connect |
| `middleware/telemetry.py` | Connection-level event recording (auth failures, rate limits, SSE connects) |
| `views/` | Health, OAuth discovery (RFC 8414 + 9728), landing page — each in its own file |

Nothing is forced on you. Delete what you don't need.

## Adding a tool

Open `src/tools/example.py` — it's already wired up as a working echo tool. Replace it or add alongside it:

```python
# src/tools/my_tool.py
from fastmcp import FastMCP, Context
from src.core.handlers import tool_handler, get_client_and_token

my_router = FastMCP("my-tool")

@my_router.tool()
@tool_handler
async def my_tool(param: str, ctx: Context) -> str:
    client, auth_header = await get_client_and_token(ctx)
    response = await client.get("/some/endpoint", headers={"Authorization": auth_header})
    return response.json()
```

Mount it in `src/server.py`:

```python
from src.tools.my_tool import my_router
mcp.mount(my_router)
```

## Connecting to Claude

**Claude.ai (web):** Settings → Connectors → Add → Custom → Web
- URL: `https://your-server.example.com/mcp/sse`

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "my-project": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://your-server.example.com/mcp/sse"]
    }
  }
}
```

**Claude Code:**
```bash
claude mcp add my-project --transport http https://your-server.example.com/mcp/sse
```

## Configuration

Copy `env.example` to `.env` and edit. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://api.example.com` | Your upstream API |
| `MCP_PUBLIC_URL` | `http://localhost:8001/mcp` | Public MCP URL (in landing page) |
| `OAUTH_ISSUER_URL` | `http://localhost:8001` | OAuth issuer for RFC 8414 discovery |
| `AUTH_PROBE_ENABLED` | `false` | Validate token against backend on SSE connect |
| `AUTH_PROBE_PATH` | `/health/` | Endpoint used for token probe |
| `LOGO_URI` | `` | Logo shown in OAuth discovery (optional) |
| `ALLOWED_ORIGINS` | `https://claude.ai,...` | CORS origins |

Full variable list and deploy instructions in `DEPLOYMENT.md`.

## How it works

`remote-mcp` renders Jinja2 templates into your project directory at scaffold time. After that, it's gone — no version pinning, no update command, no hidden runtime. You own every line.

## Requirements

- Python ≥ 3.10 (this CLI). Generated project supports the same range.
- FastMCP ≥ 3.0 (installed in the generated project, not this package)

## License

MIT — see [LICENSE](LICENSE).
