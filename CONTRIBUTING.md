# Contributing

Thanks for considering a contribution. This package is small; PRs are welcome.

## Quick start

```bash
git clone https://github.com/pushpendra-tripathi/remote-mcp.git
cd remote-mcp
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Local sanity check

```bash
remote-mcp new demo --yes --into /tmp/demo
cd /tmp/demo
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Coding conventions

- Python ≥ 3.10. Use modern typing (`list[str]`, `X | None`).
- `ruff check src tests` and `ruff format src tests` must pass.
- Generated code (under `src/remote_mcp/templates/`) must remain dependency-free
  on the `remote-mcp` package itself.

## Tests

- `tests/` covers the CLI and scaffolder.
- The slow e2e test (`-m slow`) scaffolds a project into a tmp dir and runs its
  test suite. Skip with `pytest -m "not slow"` for fast iteration.

## Releasing

1. Bump version in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Tag `vX.Y.Z` and push. GitHub Actions publishes to PyPI via Trusted Publisher.

## Reporting issues

File a GitHub issue with:
- `remote-mcp --version`
- `python --version`
- Minimal repro (project name + command run)
- Full traceback

## Code of Conduct

Be kind. Assume good faith. Disagreement is fine; personal attacks are not.
