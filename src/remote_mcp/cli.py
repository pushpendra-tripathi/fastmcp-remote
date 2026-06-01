from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from remote_mcp.scaffold import scaffold_project

console = Console()

app = typer.Typer(
    name="remote-mcp",
    add_completion=False,
    no_args_is_help=True,
)


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
        help="Show version",
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


@app.command()
def new(
    project_name: str = typer.Argument(..., help="Project directory name (kebab-case)"),
) -> None:
    """Scaffold a new FastMCP remote server."""
    console.print("\n[bold blue]FastMCP Remote Server Generator[/bold blue]\n")

    project_name = typer.prompt("Project name", default=project_name)

    default_service_name = " ".join(w.capitalize() for w in project_name.split("-"))
    service_name = typer.prompt("Service name", default=default_service_name)

    context = _derive_context(project_name, service_name)

    console.print(f"\nScaffolding {project_name}...")

    try:
        scaffold_project(target_dir=Path(project_name), context=context)
    except FileExistsError as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1)

    console.print("[green]✓[/green]")

    next_steps = (
        f'  [cyan]cd {project_name}[/cyan]\n'
        f'  [cyan]python -m venv venv && source venv/bin/activate[/cyan]\n'
        f'  [cyan]pip install -e ".[dev]"[/cyan]\n'
        f'  [cyan]cp env.example .env[/cyan]\n'
        f'  [cyan]uvicorn asgi:application --reload --port 8001 --lifespan on[/cyan]'
    )

    console.print(
        Panel(next_steps, title="[bold]Done! Next steps[/bold]", border_style="green")
    )
