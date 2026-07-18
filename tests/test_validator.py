"""Tests for the validator module."""

from pathlib import Path

from diamond_setup.validator import validate


def test_validate_nonexistent_path():
    result = validate(Path("/does/not/exist"))
    assert not result.ok
    assert any("does not exist" in e for e in result.errors)


def test_validate_file_not_dir(tmp_path):
    f = tmp_path / "somefile.txt"
    f.write_text("hello")
    result = validate(f)
    assert not result.ok
    assert any("not a directory" in e for e in result.errors)


def test_validate_empty_dir_fails(tmp_path):
    result = validate(tmp_path)
    assert not result.ok
    assert any("pyproject.toml" in e for e in result.errors)


def test_validate_pyproject_only_passes_with_warnings(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"')
    result = validate(tmp_path)
    assert result.ok  # no errors
    assert len(result.warnings) > 0  # warnings for missing src/, tests/, etc.


def test_validate_full_project(tmp_path):
    """A fully populated project should pass with no errors and fewer warnings."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"')
    (tmp_path / "README.md").write_text("# x")
    (tmp_path / ".gitignore").write_text("*.pyc")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True)

    result = validate(tmp_path)
    assert result.ok
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_validate_diamond_own_repo():
    """diamond-setup's own repository must pass validation."""
    repo_root = Path(__file__).parent.parent
    result = validate(repo_root)
    assert result.ok, f"Errors: {result.errors}"
