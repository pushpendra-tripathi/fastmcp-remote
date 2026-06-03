# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-06-03

### Added
- `remote-mcp add tool <name>` subcommand to scaffold a new tool stub.
- `--yes / -y`, `--service-name / -s`, `--into` flags on `remote-mcp new`.
- Project-name and tool-name validation (kebab/snake regex, Python keyword check).
- `python -m remote_mcp` entry point (`__main__.py`).
- `Dockerfile` and `.dockerignore` in scaffolded projects.
- Configurable OAuth endpoint paths (`OAUTH_AUTHORIZE_PATH`, `OAUTH_TOKEN_PATH`, `OAUTH_REGISTRATION_PATH`).
- `TELEMETRY_HASH_SALT` for HMAC-salted user-id hashing.
- E2E test that scaffolds + installs + runs the generated test suite.
- Ruff configuration in both the package and the scaffolded template.
- CI matrix expanded to Python 3.10–3.13 and macOS/Windows smoke jobs.

### Changed
- Python floor lowered from 3.12 to 3.10.
- Scaffolded project uses Hatchling (was setuptools); Ruff replaces Pylint.
- `auth.RequireAuthMiddleware` reuses the pooled `httpx.AsyncClient` for the SSE handshake probe.
- `Settings` access is now lazy via `get_settings()`; no import-time side effects.
- `format_error` no longer leaks unknown-exception strings to MCP clients; logs full detail.
- `http_client.py` retry logic deduplicated via a single `_request_with_retry` helper.
- `__version__` is now read from installed package metadata.

### Fixed
- Health/well-known/asset path bypass tightened (no longer matches `/healthcheck-leaky`).
- Removed dead `Authorization` (TitleCase) header lookup branch (Starlette headers are case-insensitive).
- OIDC discovery payload no longer impersonates OAuth-2.0 metadata.

## [0.1.2] — 2026-06-02

- Version bump only.

## [0.1.1] — 2026-05-31

- Split `server.py` monolith into `app.py` / `views/` / `middleware/` layers.

## [0.1.0] — 2026-05-31

- Initial release.
