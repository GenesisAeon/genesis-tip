"""Validator — checks whether a directory looks like a healthy diamond-setup project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    path: Path
    passed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def validate(project_path: Path) -> ValidationResult:
    """
    Run a series of checks on a project directory.

    Checks (errors stop a CI build, warnings are informational):
    - pyproject.toml present          → error if missing
    - src/ layout present             → warning if absent
    - tests/ directory present        → warning if absent
    - .github/workflows/ present      → warning if absent
    - README.md present               → warning if absent
    - .gitignore present              → warning if absent
    """
    result = ValidationResult(path=project_path)

    if not project_path.exists():
        result.errors.append(f"Path does not exist: {project_path}")
        return result

    if not project_path.is_dir():
        result.errors.append(f"Path is not a directory: {project_path}")
        return result

    # --- Errors (hard requirements) ---
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        result.passed.append("pyproject.toml found")
    else:
        result.errors.append("pyproject.toml is missing — project cannot be built")

    # --- Warnings (best-practice recommendations) ---
    _warn_if_missing(
        result, project_path / "src", "src/ layout not found (recommended for packages)"
    )
    _warn_if_missing(result, project_path / "tests", "tests/ directory not found")
    ci_path = project_path / ".github" / "workflows"
    _warn_if_missing(result, ci_path, ".github/workflows/ not found — no CI configured")
    _warn_if_missing(result, project_path / "README.md", "README.md is missing")
    _warn_if_missing(result, project_path / ".gitignore", ".gitignore is missing")

    return result


def _warn_if_missing(result: ValidationResult, path: Path, message: str) -> None:
    if path.exists():
        result.passed.append(f"{path.name} found")
    else:
        result.warnings.append(message)
