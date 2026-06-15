"""End-to-end smoke test for the scaffolded project.

This is slow because it builds a venv and installs FastMCP. Skip in fast loops:
    pytest -m "not slow"
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from remote_mcp.scaffold import scaffold_project, scaffold_tool

CONTEXT = {
    "project_name": "demo-mcp",
    "project_slug": "demo_mcp",
    "service_name": "Demo MCP",
    "class_prefix": "DemoMcp",
    "auth_mode": "passthrough",
    "github_owner": "YOUR-GITHUB-USERNAME",
    "legacy_sse": False,
}


def _python_files_compile(project_dir: Path) -> tuple[int, list[Path]]:
    """Byte-compile every generated .py to catch syntax errors. Cheap, no install."""
    failed: list[Path] = []
    count = 0
    for py in project_dir.rglob("*.py"):
        count += 1
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(py)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failed.append(py)
            print(result.stderr)
    return count, failed


def test_scaffolded_project_compiles(tmp_path):
    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)
    total, failed = _python_files_compile(target)
    assert total > 0
    assert failed == [], f"Files failed to compile: {failed}"


def test_scaffolded_project_has_dockerfile(tmp_path):
    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)
    assert (target / "Dockerfile").exists()
    assert (target / ".dockerignore").exists()


def test_scaffolded_project_has_no_pylintrc(tmp_path):
    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)
    assert not (target / ".pylintrc").exists()
    assert not (target / "pylintrc").exists()


def test_scaffolded_pyproject_uses_hatchling(tmp_path):
    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)
    content = (target / "pyproject.toml").read_text(encoding="utf-8")
    assert "hatchling" in content
    assert "setuptools" not in content


def test_scaffold_tool_creates_file(tmp_path):
    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)
    created = scaffold_tool(target, "search")
    assert created == target / "src" / "tools" / "search.py"
    content = created.read_text(encoding="utf-8")
    assert "search_router = FastMCP" in content
    assert "@tool_handler" in content


def test_scaffold_tool_rejects_duplicate(tmp_path):
    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)
    scaffold_tool(target, "search")
    with pytest.raises(FileExistsError):
        scaffold_tool(target, "search")


def test_legacy_sse_scaffold_compiles(tmp_path):
    ctx = dict(CONTEXT, legacy_sse=True)
    target = tmp_path / "legacy-mcp"
    scaffold_project(target, ctx)
    total, failed = _python_files_compile(target)
    assert total > 0
    assert failed == [], f"Files failed to compile: {failed}"


def test_auth_mode_none_scaffold_compiles(tmp_path):
    ctx = dict(CONTEXT, auth_mode="none")
    target = tmp_path / "none-mcp"
    scaffold_project(target, ctx)
    total, failed = _python_files_compile(target)
    assert total > 0
    assert failed == [], f"Files failed to compile: {failed}"


def _install_venv(target: Path) -> Path:
    """Create venv + install project. Returns python executable path."""
    venv = target / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, timeout=120)
    pip = venv / ("Scripts" if os.name == "nt" else "bin") / "pip"
    subprocess.run([str(pip), "install", "-e", ".[dev]"], cwd=target, check=True, timeout=600)
    return venv / ("Scripts" if os.name == "nt" else "bin") / "python"


def _wait_for_health(base_url: str, timeout_s: float = 30.0) -> None:
    import time
    import urllib.request

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"Server at {base_url} did not become healthy")


@pytest.mark.slow
def test_booted_server_spec_compliance(tmp_path):
    """Boot the generated server twice (passthrough, none) and assert spec behavior."""
    import json
    import socket
    import urllib.error
    import urllib.request

    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)
    py = _install_venv(target)
    with socket.socket() as _s:
        _s.bind(("127.0.0.1", 0))
        port = _s.getsockname()[1]
    base = f"http://127.0.0.1:{port}"

    def boot(env_extra):
        env = dict(os.environ, PORT=str(port), HOST="127.0.0.1", **env_extra)
        return subprocess.Popen(
            [str(py), "-m", "uvicorn", "asgi:application", "--port", str(port), "--lifespan", "on"],
            cwd=target,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    # passthrough: 401 with resource_metadata
    proc = boot({"AUTH_MODE": "passthrough"})
    try:
        _wait_for_health(base)
        try:
            urllib.request.urlopen(f"{base}/mcp", timeout=5)
            raise AssertionError("expected 401")
        except urllib.error.HTTPError as e:
            assert e.code == 401
            www = e.headers.get("WWW-Authenticate", "")
            assert 'resource_metadata="' in www, www
        # Origin rejection
        req = urllib.request.Request(f"{base}/mcp", headers={"Origin": "https://evil.example.com"})
        try:
            urllib.request.urlopen(req, timeout=5)
            raise AssertionError("expected 403")
        except urllib.error.HTTPError as e:
            assert e.code == 403
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    # none: MCP initialize succeeds without auth
    proc = boot({"AUTH_MODE": "none"})
    try:
        _wait_for_health(base)
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "e2e", "version": "0.0.1"},
                },
            }
        ).encode()
        req = urllib.request.Request(
            f"{base}/mcp",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            assert r.status == 200
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@pytest.mark.slow
def test_scaffolded_project_pytest_passes(tmp_path):
    """Full e2e: scaffold + pip install + run the generated test suite.

    Skipped unless explicitly selected with `pytest -m slow` because it
    downloads FastMCP and its deps (~30s on a warm cache).
    """
    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)

    py = _install_venv(target)
    result = subprocess.run(
        [str(py), "-m", "pytest", "tests/", "-q"],
        cwd=target,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
