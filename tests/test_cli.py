import pytest
from typer.testing import CliRunner

from remote_mcp.cli import _validate_project_name, _validate_tool_name, app, derive_context

runner = CliRunner()


def testderive_context_basic():
    ctx = derive_context("my-project", "My Project")
    assert ctx["project_slug"] == "my_project"
    assert ctx["class_prefix"] == "MyProject"
    assert ctx["project_name"] == "my-project"
    assert ctx["service_name"] == "My Project"


def testderive_context_multi_word_kebab():
    ctx = derive_context("my-awesome-tool", "My Awesome Tool")
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
    result = runner.invoke(app, ["new", "my-project"], input="my-project\nMy Project\n\n\n")
    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0][1]["project_slug"] == "my_project"
    assert calls[0][1]["class_prefix"] == "MyProject"


def test_new_command_handles_existing_dir(monkeypatch):
    def raises(target_dir, context):
        raise FileExistsError("Directory already exists: my-project")

    monkeypatch.setattr("remote_mcp.cli.scaffold_project", raises)
    result = runner.invoke(app, ["new", "my-project"], input="my-project\nMy Project\n\n\n")
    assert result.exit_code == 1


def testderive_context_new_keys_defaults():
    ctx = derive_context("my-project", "My Project")
    assert ctx["auth_mode"] == "passthrough"
    assert ctx["github_owner"] == "YOUR-GITHUB-USERNAME"
    assert ctx["legacy_sse"] is False


def testderive_context_new_keys_explicit():
    ctx = derive_context(
        "my-project",
        "My Project",
        auth_mode="jwt",
        github_owner="octocat",
        legacy_sse=True,
    )
    assert ctx["auth_mode"] == "jwt"
    assert ctx["github_owner"] == "octocat"
    assert ctx["legacy_sse"] is True


def test_new_command_auth_mode_flag(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "remote_mcp.cli.scaffold_project", lambda target_dir, context: calls.append(context)
    )
    result = runner.invoke(
        app,
        ["new", "my-project", "-y", "--auth-mode", "none", "--into", str(tmp_path / "o")],
    )
    assert result.exit_code == 0, result.output
    assert calls[0]["auth_mode"] == "none"


def test_new_command_rejects_bad_auth_mode(tmp_path):
    result = runner.invoke(
        app,
        ["new", "my-project", "-y", "--auth-mode", "oauth", "--into", str(tmp_path / "o")],
    )
    assert result.exit_code != 0


def test_new_command_github_owner_flag(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "remote_mcp.cli.scaffold_project", lambda target_dir, context: calls.append(context)
    )
    result = runner.invoke(
        app,
        ["new", "my-project", "-y", "--github-owner", "octocat", "--into", str(tmp_path / "o")],
    )
    assert result.exit_code == 0, result.output
    assert calls[0]["github_owner"] == "octocat"


def test_new_command_legacy_sse_flag(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        "remote_mcp.cli.scaffold_project", lambda target_dir, context: calls.append(context)
    )
    result = runner.invoke(
        app,
        ["new", "my-project", "-y", "--legacy-sse", "--into", str(tmp_path / "o")],
    )
    assert result.exit_code == 0, result.output
    assert calls[0]["legacy_sse"] is True
