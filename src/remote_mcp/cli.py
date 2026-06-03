from __future__ import annotations

import keyword
import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from remote_mcp.scaffold import scaffold_project, scaffold_tool

console = Console()

app = typer.Typer(
    name="remote-mcp",
    add_completion=False,
    no_args_is_help=True,
    help="Scaffold a production-ready remote MCP server.",
)

add_app = typer.Typer(
    name="add",
    no_args_is_help=True,
    help="Add a new component (e.g. tool) to an existing scaffolded project.",
)
app.add_typer(add_app, name="add")


# kebab-case: starts with lowercase letter, lowercase/digit/hyphen, no double hyphen,
# does not end with hyphen. Length 2-64.
_KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_SNAKE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def _validate_project_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise typer.BadParameter("Project name cannot be empty.")
    if len(name) > 64:
        raise typer.BadParameter("Project name too long (max 64 chars).")
    if not _KEBAB_RE.match(name):
        raise typer.BadParameter(
            f"Invalid project name: {name!r}. "
            "Must be kebab-case: lowercase letters, digits, hyphens; "
            "start with a letter; no leading/trailing/double hyphens."
        )
    slug = name.replace("-", "_")
    if keyword.iskeyword(slug) or keyword.issoftkeyword(slug):
        raise typer.BadParameter(f"Project name conflicts with Python keyword: {slug!r}.")
    return name


def _validate_tool_name(name: str) -> str:
    name = name.strip().replace("-", "_")
    if not name:
        raise typer.BadParameter("Tool name cannot be empty.")
    if not _SNAKE_RE.match(name):
        raise typer.BadParameter(
            f"Invalid tool name: {name!r}. Must be snake_case (lowercase letters, digits, underscores; "
            "start with a letter or underscore)."
        )
    if keyword.iskeyword(name) or keyword.issoftkeyword(name):
        raise typer.BadParameter(f"Tool name conflicts with Python keyword: {name!r}.")
    return name


def version_callback(value: bool) -> None:
    if value:
        from remote_mcp import __version__

        typer.echo(f"remote-mcp {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    pass


def _derive_context(project_name: str, service_name: str) -> dict[str, str]:
    project_slug = project_name.replace("-", "_")
    class_prefix = "".join(w.capitalize() for w in project_name.split("-"))
    return {
        "project_name": project_name,
        "project_slug": project_slug,
        "service_name": service_name,
        "class_prefix": class_prefix,
    }


def _default_service_name(project_name: str) -> str:
    return " ".join(w.capitalize() for w in project_name.split("-"))


@app.command()
def new(
    project_name: str = typer.Argument(..., help="Project directory name (kebab-case)"),
    service_name: str | None = typer.Option(
        None, "--service-name", "-s", help="Human-readable service name (default: derived from project_name)."
    ),
    into: Path | None = typer.Option(
        None, "--into", help="Target directory (default: ./<project_name>)."
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip interactive prompts; use defaults / provided flags."
    ),
) -> None:
    """Scaffold a new FastMCP remote server."""
    console.print("\n[bold blue]FastMCP Remote Server Generator[/bold blue]\n")

    if not yes:
        project_name = typer.prompt("Project name", default=project_name)
    project_name = _validate_project_name(project_name)

    if service_name is None:
        default_sn = _default_service_name(project_name)
        service_name = default_sn if yes else typer.prompt("Service name", default=default_sn)
    service_name = service_name.strip() or _default_service_name(project_name)

    target_dir = into if into is not None else Path(project_name)

    context = _derive_context(project_name, service_name)

    console.print(f"\nScaffolding [cyan]{project_name}[/cyan] into [cyan]{target_dir}[/cyan]...")

    try:
        scaffold_project(target_dir=target_dir, context=context)
    except FileExistsError as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1) from exc

    console.print("[green]✓ Scaffold complete[/green]")

    next_steps = (
        f"  [cyan]cd {target_dir}[/cyan]\n"
        f"  [cyan]python -m venv venv && source venv/bin/activate[/cyan]\n"
        f'  [cyan]pip install -e ".\\[dev]"[/cyan]\n'
        f"  [cyan]cp env.example .env[/cyan]\n"
        f"  [cyan]uvicorn asgi:application --reload --port 8001 --lifespan on[/cyan]"
    )
    console.print(Panel(next_steps, title="[bold]Done! Next steps[/bold]", border_style="green"))


@add_app.command("tool")
def add_tool_cmd(
    tool_name: str = typer.Argument(..., help="Tool name (snake_case)"),
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-p", help="Project directory (default: cwd)."
    ),
) -> None:
    """Add a new tool stub to an existing scaffolded project."""
    tool_name = _validate_tool_name(tool_name)

    if not (project_dir / "src" / "server.py").exists():
        console.print(
            f"[red]Error: {project_dir} does not look like a scaffolded remote-mcp project "
            "(no src/server.py).[/red]"
        )
        raise typer.Exit(1)

    try:
        created_path = scaffold_tool(project_dir=project_dir, tool_name=tool_name)
    except FileExistsError as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1) from exc

    console.print(f"[green]✓ Created {created_path}[/green]")
    console.print(
        Panel(
            f"  [cyan]from src.tools.{tool_name} import {tool_name}_router[/cyan]\n"
            f"  [cyan]mcp.mount({tool_name}_router)[/cyan]",
            title="[bold]Mount in src/server.py[/bold]",
            border_style="green",
        )
    )
