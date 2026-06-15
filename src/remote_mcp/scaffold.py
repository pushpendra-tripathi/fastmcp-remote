from __future__ import annotations

import contextlib
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).parent / "templates"
SNIPPETS_DIR = Path(__file__).parent / "snippets"

# Dotfiles/dot-dirs can't ship inside a wheel reliably. Store them without the
# leading dot and rename path segments on copy.
_SEGMENT_RENAMES: dict[str, str] = {
    "gitignore": ".gitignore",
    "dockerignore": ".dockerignore",
    "github": ".github",
}


def _output_path(target_dir: Path, relative: Path, *, strip_j2: bool) -> Path:
    parts = [_SEGMENT_RENAMES.get(p, p) for p in relative.parts]
    out = target_dir / Path(*parts)
    if strip_j2:
        out = out.with_suffix("")
    return out


def _jinja_env(loader_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(loader_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,
    )


def scaffold_project(target_dir: Path, context: dict) -> None:
    """
    Render all templates into target_dir.

    .j2 files are rendered with Jinja2 and written without the .j2 extension.
    All other files are copied verbatim (dotfile renames applied).
    Raises FileExistsError (without writing anything) if target_dir already exists
    and is not empty.
    """
    target_dir = Path(target_dir)
    if target_dir.exists() and any(target_dir.iterdir()):
        raise FileExistsError(f"Target directory already exists and is not empty: {target_dir}")

    env = _jinja_env(TEMPLATES_DIR)
    created_root = not target_dir.exists()
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    try:
        for template_path in sorted(TEMPLATES_DIR.rglob("*")):
            if template_path.is_dir():
                continue

            relative = template_path.relative_to(TEMPLATES_DIR)

            if template_path.suffix == ".j2":
                output_path = _output_path(target_dir, relative, strip_j2=True)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                template = env.get_template(str(relative).replace("\\", "/"))
                output_path.write_text(template.render(**context), encoding="utf-8")
            else:
                output_path = _output_path(target_dir, relative, strip_j2=False)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(template_path, output_path)
            written.append(output_path)
    except BaseException:
        # If we created the target_dir, wipe it entirely. Otherwise (--into .
        # or pre-existing empty dir), only remove files we wrote — never
        # touch pre-existing user files.
        if created_root:
            shutil.rmtree(target_dir, ignore_errors=True)
        else:
            for p in written:
                with contextlib.suppress(OSError):
                    p.unlink()
        raise


def scaffold_tool(project_dir: Path, tool_name: str) -> Path:
    """
    Add a new tool stub to an existing scaffolded project.

    Returns the path of the file created.
    Raises FileExistsError if the tool file already exists.
    """
    project_dir = Path(project_dir)
    tools_dir = project_dir / "src" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    output_path = tools_dir / f"{tool_name}.py"
    if output_path.exists():
        raise FileExistsError(f"Tool file already exists: {output_path}")

    env = _jinja_env(SNIPPETS_DIR)
    template = env.get_template("tool.py.j2")
    output_path.write_text(template.render(tool_name=tool_name), encoding="utf-8")
    return output_path
