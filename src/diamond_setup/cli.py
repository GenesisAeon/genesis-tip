"""Diamond Setup CLI — scaffold, validate and inspect project templates."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .preset import scaffold as _scaffold
from .templates import REGISTRY
from .validator import validate as _validate

app = typer.Typer(
    name="diamond",
    help="Universal Python project scaffold — create professional skeletons in seconds.",
    add_completion=True,
    rich_markup_mode="rich",
)
console = Console()
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# scaffold
# ---------------------------------------------------------------------------


@app.command()
def scaffold(
    project_name: Annotated[
        str, typer.Argument(help="Name of the new project (kebab-case recommended)")
    ],
    template: Annotated[str, typer.Option("--template", "-t", help="Template to use")] = "minimal",
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", "-o", help="Parent directory for the new project")
    ] = None,
    author: Annotated[str | None, typer.Option(help="Author name")] = None,
    description: Annotated[str | None, typer.Option(help="Short project description")] = None,
    python_version: Annotated[
        str | None, typer.Option(help="Minimum Python version (e.g. 3.11)")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Preview files without writing them")
    ] = False,
) -> None:
    """[bold]Scaffold a new project[/bold] from a template.

    Examples:

      diamond scaffold my-tool

      diamond scaffold my-tool --template genesis --author "Ada Lovelace"

      diamond scaffold my-tool --dry-run
    """
    if template not in REGISTRY:
        err_console.print(
            f"[red]Unknown template '[bold]{template}[/bold]'. "
            f"Run [bold]diamond list-templates[/bold] to see available options.[/red]"
        )
        raise typer.Exit(code=1)

    dest = output_dir or Path.cwd()
    project_path = dest / project_name

    if project_path.exists() and not dry_run:
        err_console.print(
            f"[red]Directory [bold]{project_path}[/bold] already exists. "
            "Use a different name or [bold]--output-dir[/bold].[/red]"
        )
        raise typer.Exit(code=1)

    overrides = {
        "author": author,
        "description": description,
        "python_version": python_version,
    }

    tmpl = REGISTRY[template]
    mode = "[yellow]DRY RUN[/yellow] — " if dry_run else ""
    console.print(
        Panel(
            f"{mode}[bold green]Scaffolding[/bold green] [cyan]{project_name}[/cyan] "
            f"with template [magenta]{template}[/magenta]",
            expand=False,
        )
    )

    written = _scaffold(project_name, tmpl, dest, overrides=overrides, dry_run=dry_run)

    table = Table(show_header=False, box=None, padding=(0, 2))
    for path in written:
        rel = path.relative_to(dest)
        icon = "📄" if dry_run else "✅"
        table.add_row(icon, str(rel))
    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run — no files were written.[/yellow]")
    else:
        console.print(
            f"\n[bold green]Done![/bold green] Project created at [cyan]{project_path}[/cyan]\n"
            f"\nNext steps:\n"
            f"  [dim]cd[/dim] {project_name}\n"
            f"  [dim]uv sync --dev[/dim]\n"
            f"  [dim]pre-commit install[/dim]\n"
            f"  [dim]uv run pytest[/dim]"
        )


# ---------------------------------------------------------------------------
# list-templates
# ---------------------------------------------------------------------------


@app.command(name="list-templates")
def list_templates() -> None:
    """List all available templates."""
    table = Table(title="Available Templates", show_lines=True)
    table.add_column("Name", style="magenta bold", no_wrap=True)
    table.add_column("Description")
    table.add_column("Extra variables", style="dim")

    for name, tmpl in REGISTRY.items():
        base_vars = {"name", "description", "author", "python_version"}
        extras = sorted(set(tmpl.get("variables", [])) - base_vars)
        table.add_row(name, tmpl["description"], ", ".join(extras) or "—")

    console.print(table)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


@app.command()
def validate(
    path: Annotated[Path | None, typer.Argument(help="Project directory to validate")] = None,
) -> None:
    """Validate a project directory against diamond-setup best practices."""
    target = path or Path.cwd()
    result = _validate(target)

    console.print(f"\nValidating [cyan]{target}[/cyan]\n")

    for msg in result.passed:
        console.print(f"  [green]✔[/green]  {msg}")
    for msg in result.warnings:
        console.print(f"  [yellow]⚠[/yellow]  {msg}")
    for msg in result.errors:
        console.print(f"  [red]✘[/red]  {msg}")

    console.print()
    if result.ok:
        console.print("[bold green]All checks passed.[/bold green]")
    else:
        console.print(f"[bold red]{len(result.errors)} error(s) found.[/bold red]")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------


@app.command()
def version() -> None:
    """Show the diamond-setup version."""
    console.print(f"diamond-setup [bold]{__version__}[/bold]")


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
