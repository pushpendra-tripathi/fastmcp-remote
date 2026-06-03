
import pytest

from remote_mcp.scaffold import scaffold_project

CONTEXT = {
    "project_name": "my-project",
    "project_slug": "my_project",
    "service_name": "My Project",
    "class_prefix": "MyProject",
}


def test_scaffold_produces_complete_file_tree(tmp_path):
    target = tmp_path / "my-project"
    scaffold_project(target, CONTEXT)

    # Core server files
    assert (target / "src" / "server.py").exists()
    assert (target / "src" / "app.py").exists()

    # Views
    assert (target / "src" / "views" / "__init__.py").exists()
    assert (target / "src" / "views" / "health.py").exists()
    assert (target / "src" / "views" / "oauth.py").exists()
    assert (target / "src" / "views" / "root.py").exists()

    # Middleware
    assert (target / "src" / "middleware" / "__init__.py").exists()
    assert (target / "src" / "middleware" / "auth.py").exists()
    assert (target / "src" / "middleware" / "telemetry.py").exists()

    # Core
    assert (target / "src" / "core" / "errors.py").exists()
    assert (target / "src" / "core" / "telemetry.py").exists()
    assert (target / "src" / "config" / "settings.py").exists()

    # Project root
    assert (target / "pyproject.toml").exists()
    assert (target / "asgi.py").exists()
    assert (target / "tests" / "conftest.py").exists()

    # No .j2 files should appear in output tree
    j2_files = list(target.rglob("*.j2"))
    assert j2_files == [], f"Unexpected .j2 files in output: {j2_files}"


def test_scaffold_key_content_substitutions(tmp_path):
    target = tmp_path / "my-project"
    scaffold_project(target, CONTEXT)

    errors_content = (target / "src" / "core" / "errors.py").read_text()
    assert "MyProjectError" in errors_content
    assert "MY_PROJECT_ERROR" in errors_content
    assert "EnineSites" not in errors_content
    assert "{{ class_prefix }}" not in errors_content

    telemetry_content = (target / "src" / "core" / "telemetry.py").read_text()
    assert "my_project_telemetry" in telemetry_content
    assert "{{ project_slug }}" not in telemetry_content

    server_content = (target / "src" / "server.py").read_text()
    assert "My Project" in server_content
    assert "{{ service_name }}" not in server_content

    app_content = (target / "src" / "app.py").read_text()
    assert "My Project" in app_content
    assert "src.app:app" in app_content
    assert "{{ service_name }}" not in app_content

    auth_content = (target / "src" / "middleware" / "auth.py").read_text()
    assert "My Project" in auth_content
    assert "_UNPROTECTED_EXACT" in auth_content
    assert "{{ service_name }}" not in auth_content

    health_content = (target / "src" / "views" / "health.py").read_text()
    assert "My Project" in health_content
    assert "{{ service_name }}" not in health_content

    assert "src.app import app" in (target / "asgi.py").read_text()
    assert "src.app import app" in (target / "tests" / "conftest.py").read_text()

    pyproject_content = (target / "pyproject.toml").read_text()
    assert 'name = "my-project"' in pyproject_content

    settings_content = (target / "src" / "config" / "settings.py").read_text()
    assert "user_agent" in settings_content

    env_example_content = (target / "env.example").read_text()
    assert "my_project-mcp/1.0" in env_example_content


def test_scaffold_custom_service_name_class_prefix(tmp_path):
    context = {
        "project_name": "my-awesome-tool",
        "project_slug": "my_awesome_tool",
        "service_name": "My Awesome Tool",
        "class_prefix": "MyAwesomeTool",
    }
    target = tmp_path / "my-awesome-tool"
    scaffold_project(target, context)

    errors_content = (target / "src" / "core" / "errors.py").read_text()
    assert "MyAwesomeTool" in errors_content


def test_scaffold_non_empty_dir_raises(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "untouchable.txt").write_text("dont delete me")

    with pytest.raises(FileExistsError):
        scaffold_project(existing, CONTEXT)

    # Pre-existing file must remain untouched
    assert (existing / "untouchable.txt").read_text() == "dont delete me"


def test_scaffold_empty_dir_succeeds(tmp_path):
    """Allow scaffolding into an existing empty directory (e.g. --into .)."""
    target = tmp_path / "empty"
    target.mkdir()
    scaffold_project(target, CONTEXT)
    assert (target / "src" / "server.py").exists()
