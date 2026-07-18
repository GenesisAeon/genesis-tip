"""Tests for the preset engine."""

import pytest

from diamond_setup.preset import _build_context, _to_snake, scaffold
from diamond_setup.templates import REGISTRY


def test_to_snake_kebab():
    assert _to_snake("my-project") == "my_project"


def test_to_snake_spaces():
    assert _to_snake("My Cool Project") == "my_cool_project"


def test_to_snake_noop():
    assert _to_snake("myproject") == "myproject"


def test_build_context_defaults():
    tmpl = REGISTRY["minimal"]
    ctx = _build_context("my-project", tmpl, {})
    assert ctx["name"] == "my-project"
    assert ctx["name_snake"] == "my_project"
    assert "python_version_nodot" in ctx


def test_build_context_override():
    tmpl = REGISTRY["minimal"]
    ctx = _build_context("my-project", tmpl, {"author": "Ada"})
    assert ctx["author"] == "Ada"


def test_build_context_none_values_ignored():
    """None overrides (CLI defaults) must not overwrite template defaults."""
    tmpl = REGISTRY["minimal"]
    ctx = _build_context("x", tmpl, {"author": None})
    assert ctx["author"] == tmpl["defaults"]["author"]


@pytest.mark.parametrize("template_name", list(REGISTRY.keys()))
def test_scaffold_dry_run_returns_paths(tmp_path, template_name):
    """Dry-run must return all planned paths without creating anything."""
    tmpl = REGISTRY[template_name]
    paths = scaffold("test-project", tmpl, tmp_path, dry_run=True)
    assert len(paths) > 0
    # Nothing should have been written
    assert not (tmp_path / "test-project").exists()


@pytest.mark.parametrize("template_name", list(REGISTRY.keys()))
def test_scaffold_writes_files(tmp_path, template_name):
    """scaffold() must create all declared files on disk."""
    tmpl = REGISTRY[template_name]
    paths = scaffold("test-project", tmpl, tmp_path)
    for path in paths:
        assert path.exists(), f"Expected {path} to exist"


def test_scaffold_minimal_pyproject_content(tmp_path):
    """The rendered pyproject.toml must contain the project name."""
    tmpl = REGISTRY["minimal"]
    scaffold("my-lib", tmpl, tmp_path)
    pyproject = (tmp_path / "my-lib" / "pyproject.toml").read_text()
    assert 'name = "my-lib"' in pyproject


def test_scaffold_snake_case_in_paths(tmp_path):
    """Kebab project names must produce snake_case module directories."""
    tmpl = REGISTRY["minimal"]
    scaffold("cool-tool", tmpl, tmp_path)
    assert (tmp_path / "cool-tool" / "src" / "cool_tool").is_dir()


def test_scaffold_genesis_has_domains_yaml(tmp_path):
    """Genesis template must include domains.yaml."""
    tmpl = REGISTRY["genesis"]
    scaffold("gen-proj", tmpl, tmp_path)
    assert (tmp_path / "gen-proj" / "domains.yaml").exists()


def test_scaffold_no_overwrite(tmp_path):
    """scaffold() must not be called twice on the same path at CLI level (guard in CLI)."""
    # The engine itself is neutral — test that CLI guards this.
    # Here we just verify the file is correctly rendered twice (idempotent content-wise).
    tmpl = REGISTRY["minimal"]
    scaffold("dup-project", tmpl, tmp_path)
    scaffold("dup-project", tmpl, tmp_path)  # second call overwrites — fine at engine level
    assert (tmp_path / "dup-project" / "README.md").exists()
