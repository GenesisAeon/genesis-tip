"""Tests for the CLI commands."""

from pathlib import Path

from typer.testing import CliRunner

from diamond_setup import __version__
from diamond_setup.cli import app
from diamond_setup.templates import REGISTRY

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_list_templates():
    result = runner.invoke(app, ["list-templates"])
    assert result.exit_code == 0
    for name in REGISTRY:
        assert name in result.output


def test_scaffold_minimal(tmp_path):
    result = runner.invoke(app, ["scaffold", "hello-world", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "hello-world" / "pyproject.toml").exists()


def test_scaffold_genesis(tmp_path):
    result = runner.invoke(
        app,
        ["scaffold", "my-genesis", "--template", "genesis", "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "my-genesis" / "domains.yaml").exists()


def test_scaffold_includes_agent_md_minimal(tmp_path):
    result = runner.invoke(app, ["scaffold", "agent-min", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    agent = tmp_path / "agent-min" / "AGENT.md"
    assert agent.exists()
    content = agent.read_text(encoding="utf-8")
    assert "GenesisAeon Release & Metadata Rules" in content
    assert "10.5281/zenodo.19645351" in content


def test_scaffold_includes_agent_md_genesis(tmp_path):
    result = runner.invoke(
        app,
        ["scaffold", "agent-gen", "--template", "genesis", "--output-dir", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "agent-gen" / "AGENT.md").exists()


def test_scaffold_unknown_template():
    result = runner.invoke(app, ["scaffold", "x", "--template", "nonexistent"])
    assert result.exit_code != 0
    assert "Unknown template" in result.output


def test_scaffold_existing_dir(tmp_path):
    (tmp_path / "existing-proj").mkdir()
    result = runner.invoke(app, ["scaffold", "existing-proj", "--output-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "already" in result.output and "exists" in result.output


def test_scaffold_dry_run_no_files(tmp_path):
    result = runner.invoke(
        app, ["scaffold", "dry-proj", "--output-dir", str(tmp_path), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Dry run" in result.output
    assert not (tmp_path / "dry-proj").exists()


def test_scaffold_with_overrides(tmp_path):
    result = runner.invoke(
        app,
        [
            "scaffold",
            "custom-proj",
            "--output-dir",
            str(tmp_path),
            "--author",
            "Test Author",
            "--description",
            "A test project",
        ],
    )
    assert result.exit_code == 0, result.output
    pyproject = (tmp_path / "custom-proj" / "pyproject.toml").read_text()
    assert "Test Author" in pyproject
    assert "A test project" in pyproject


def test_validate_current_project():
    """Running validate on diamond-setup's own root should pass."""
    # Find the repo root (parent of tests/)
    repo_root = Path(__file__).parent.parent
    result = runner.invoke(app, ["validate", str(repo_root)])
    assert result.exit_code == 0, result.output
    assert "passed" in result.output.lower() or "✔" in result.output


def test_validate_missing_pyproject(tmp_path):
    """A directory without pyproject.toml should fail validation."""
    result = runner.invoke(app, ["validate", str(tmp_path)])
    assert result.exit_code != 0
    assert "error" in result.output.lower() or "✘" in result.output


def test_validate_nonexistent_path():
    result = runner.invoke(app, ["validate", "/nonexistent/path/xyz"])
    assert result.exit_code != 0
