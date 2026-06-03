import pytest
from typer.testing import CliRunner

from remote_mcp.cli import _derive_context, _validate_project_name, _validate_tool_name, app

runner = CliRunner()


def test_derive_context_basic():
    ctx = _derive_context("my-project", "My Project")
    assert ctx["project_slug"] == "my_project"
    assert ctx["class_prefix"] == "MyProject"
    assert ctx["project_name"] == "my-project"
    assert ctx["service_name"] == "My Project"


def test_derive_context_multi_word_kebab():
    ctx = _derive_context("my-awesome-tool", "My Awesome Tool")
    assert ctx["project_slug"] == "my_awesome_tool"
    assert ctx["class_prefix"] == "MyAwesomeTool"


def test_version_flag():
    from remote_mcp import __version__

    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


@pytest.mark.parametrize("name", ["good", "my-project", "my-awesome-tool", "tool123", "abc-1"])
def test_validate_project_name_ok(name):
    assert _validate_project_name(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        "1starts-with-digit",
        "-leading-hyphen",
        "trailing-hyphen-",
        "double--hyphen",
        "UpperCase",
        "has_underscore",
        "has space",
        "has.dot",
        "x" * 100,
    ],
)
def test_validate_project_name_rejects(name):
    import typer as _typer

    with pytest.raises(_typer.BadParameter):
        _validate_project_name(name)


def test_validate_tool_name_normalises_hyphen():
    assert _validate_tool_name("my-tool") == "my_tool"


def test_validate_tool_name_rejects_keyword():
    import typer as _typer

    with pytest.raises(_typer.BadParameter):
        _validate_tool_name("class")


def test_new_command_yes_skips_prompt(monkeypatch, tmp_path):
    calls = []

    def fake_scaffold(target_dir, context):
        calls.append((target_dir, context))

    monkeypatch.setattr("remote_mcp.cli.scaffold_project", fake_scaffold)
    result = runner.invoke(app, ["new", "my-project", "--yes", "--into", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0][1]["project_slug"] == "my_project"


def test_new_command_service_name_flag(monkeypatch, tmp_path):
    calls = []

    def fake_scaffold(target_dir, context):
        calls.append((target_dir, context))

    monkeypatch.setattr("remote_mcp.cli.scaffold_project", fake_scaffold)
    result = runner.invoke(
        app,
        ["new", "my-project", "-y", "-s", "Custom Name", "--into", str(tmp_path / "out")],
    )
    assert result.exit_code == 0
    assert calls[0][1]["service_name"] == "Custom Name"


def test_new_command_validates_name(tmp_path):
    result = runner.invoke(app, ["new", "Bad_Name", "--yes", "--into", str(tmp_path / "out")])
    assert result.exit_code != 0


def test_add_tool_command_creates_file(tmp_path):
    # Bootstrap minimal fake project.
    project = tmp_path / "demo"
    (project / "src").mkdir(parents=True)
    (project / "src" / "server.py").write_text("# stub", encoding="utf-8")
    result = runner.invoke(app, ["add", "tool", "my_tool", "-p", str(project)])
    assert result.exit_code == 0, result.output
    assert (project / "src" / "tools" / "my_tool.py").exists()


def test_add_tool_rejects_non_project(tmp_path):
    result = runner.invoke(app, ["add", "tool", "x", "-p", str(tmp_path)])
    assert result.exit_code != 0


def test_new_command_calls_scaffold(monkeypatch, tmp_path):
    calls = []

    def fake_scaffold(target_dir, context):
        calls.append((target_dir, context))

    monkeypatch.setattr("remote_mcp.cli.scaffold_project", fake_scaffold)
    result = runner.invoke(app, ["new", "my-project"], input="my-project\nMy Project\n")
    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0][1]["project_slug"] == "my_project"
    assert calls[0][1]["class_prefix"] == "MyProject"


def test_new_command_handles_existing_dir(monkeypatch):
    def raises(target_dir, context):
        raise FileExistsError("Directory already exists: my-project")

    monkeypatch.setattr("remote_mcp.cli.scaffold_project", raises)
    result = runner.invoke(app, ["new", "my-project"], input="my-project\nMy Project\n")
    assert result.exit_code == 1
