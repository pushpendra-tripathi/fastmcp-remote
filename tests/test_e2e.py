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


@pytest.mark.slow
def test_scaffolded_project_pytest_passes(tmp_path):
    """Full e2e: scaffold + pip install + run the generated test suite.

    Skipped unless explicitly selected with `pytest -m slow` because it
    downloads FastMCP and its deps (~30s on a warm cache).
    """
    target = tmp_path / "demo-mcp"
    scaffold_project(target, CONTEXT)

    venv = target / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, timeout=120)
    pip = venv / ("Scripts" if os.name == "nt" else "bin") / "pip"
    py = venv / ("Scripts" if os.name == "nt" else "bin") / "python"
    subprocess.run(
        [str(pip), "install", "-e", ".[dev]"],
        cwd=target,
        check=True,
        timeout=600,
    )
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
