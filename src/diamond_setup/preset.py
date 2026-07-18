"""Preset engine — resolves templates and renders project files."""

from __future__ import annotations

import re
from pathlib import Path
from string import Template

from ._types import TemplateDict


class TemplateError(Exception):
    """Raised when template rendering fails."""


def _to_snake(name: str) -> str:
    """Convert a project name (kebab or space) to snake_case."""
    return re.sub(r"[-\s]+", "_", name).lower()


def _python_version_nodot(version: str) -> str:
    """Turn '3.11' into '311' for ruff target-version."""
    return version.replace(".", "")


def _build_context(
    project_name: str, template: TemplateDict, overrides: dict[str, str | None]
) -> dict[str, str]:
    """Merge defaults, user overrides and derived variables into a render context."""
    ctx: dict[str, str] = {
        "name": project_name,
        "name_snake": _to_snake(project_name),
        **template.get("defaults", {}),
        **{k: v for k, v in overrides.items() if v is not None},
    }
    ctx["python_version_nodot"] = _python_version_nodot(ctx.get("python_version", "3.11"))
    return ctx


def _render(content: str, ctx: dict[str, str]) -> str:
    """Render a template string using Python's string.Template (safe_substitute)."""
    # First pass: render path-embedded variables (e.g. ${name_snake} in file keys)
    return Template(content).safe_substitute(ctx)


def scaffold(
    project_name: str,
    template: TemplateDict,
    output_dir: Path,
    overrides: dict[str, str | None] | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """
    Render a template into a new project directory.

    Args:
        project_name: The name of the new project.
        template:     A template dict from the registry.
        output_dir:   Parent directory where the project folder will be created.
        overrides:    Optional variable overrides (e.g. author, description).
        dry_run:      If True, return planned paths without writing any files.

    Returns:
        List of paths that were (or would be) written.
    """
    overrides = overrides or {}
    ctx = _build_context(project_name, template, overrides)
    project_root = output_dir / project_name
    written: list[Path] = []

    for raw_path, raw_content in template["files"].items():
        # Render the path itself (e.g. src/${name_snake}/__init__.py)
        rel_path = Path(_render(raw_path, ctx))
        abs_path = project_root / rel_path

        rendered_content = _render(raw_content, ctx)

        if not dry_run:
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(rendered_content, encoding="utf-8")

        written.append(abs_path)

    return written
