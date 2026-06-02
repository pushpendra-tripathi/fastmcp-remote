from remote_mcp.cli import _derive_context, app
from typer.testing import CliRunner

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
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.2" in result.output


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
