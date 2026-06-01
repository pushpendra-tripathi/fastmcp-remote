import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Dotfiles can't ship inside a wheel reliably. Store them without the leading
# dot and rename them on copy so the generated project gets the correct names.
_DOTFILE_RENAMES: dict[str, str] = {
    "gitignore": ".gitignore",
    "pylintrc": ".pylintrc",
}


def scaffold_project(target_dir: Path, context: dict) -> None:
    """
    Render all templates into target_dir.

    .j2 files are rendered with Jinja2 and written without the .j2 extension.
    All other files are copied verbatim (dotfile renames applied).
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

    try:
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
                # Apply dotfile renames at the final path component only.
                parts = list(relative.parts)
                parts[-1] = _DOTFILE_RENAMES.get(parts[-1], parts[-1])
                output_path = target_dir / Path(*parts)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(template_path, output_path)
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise

