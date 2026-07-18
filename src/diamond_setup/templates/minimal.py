"""Minimal template — clean, modern Python project for anyone."""

from diamond_setup._types import TemplateDict

TEMPLATE: TemplateDict = {
    "name": "minimal",
    "description": "Clean, modern Python project with uv, ruff, pytest and CI",
    "variables": ["name", "description", "author", "python_version"],
    "defaults": {
        "description": "A Python project",
        "author": "Your Name",
        "python_version": "3.11",
    },
    "files": {
        "pyproject.toml": """\
[project]
name = "${name}"
version = "0.1.0"
description = "${description}"
readme = "README.md"
license = { text = "MIT" }
authors = [{ name = "${author}" }]
requires-python = ">=${python_version}"
dependencies = []

[project.optional-dependencies]
dev = ["ruff>=0.6.0", "pytest>=8.0.0", "pytest-cov>=5.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/${name_snake}"]

[tool.ruff]
line-length = 100
target-version = "py${python_version_nodot}"

[tool.ruff.lint]
select = ["E", "F", "B", "I", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=${name_snake} --cov-report=term-missing -v"
""",
        "README.md": """\
# ${name}

${description}

## Quickstart

```bash
uv sync
uv run pytest
```

## Development

```bash
uv sync --dev
pre-commit install
uv run ruff check .
uv run pytest
```
""",
        ".gitignore": """\
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
.venv/
.uv/

# Testing
.coverage
htmlcov/
.pytest_cache/

# Docs
site/

# Editors
.vscode/
.idea/
*.swp
""",
        ".pre-commit-config.yaml": """\
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
""",
        ".github/workflows/ci.yml": """\
name: CI

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: $${{ matrix.python-version }}
      - run: uv sync --dev
      - run: uv run ruff check .
      - run: uv run pytest
""",
        "AGENT.md": """\
# AGENT.md – GenesisAeon Release & Metadata Rules

## Bei jeder relevanten Änderung (Version Bump, Feature, Bugfix, Docs):

1. **.zenodo.json**
   - Aktualisiere `version`, `description`, `keywords`, `related_identifiers`
   - Beschreibung muss die aktuelle Funktion des Packages klar beschreiben
   - Immer den Whitepaper-DOI (10.5281/zenodo.19645351) als `isPartOf` oder
     `isDocumentedBy` eintragen

2. **README.md**
   - Aktualisiere Whitepaper-Badge auf aktuelle Version
   - Aktualisiere @software BibTeX-Eintrag (version, publisher=Zenodo, DOI)
   - Füge Package-Number-Badge ein (z.B. Package 17)

3. **Versionierung**
   - pyproject.toml und __init__.py müssen synchron auf dieselbe Version sein
   - Tags immer als annotated Tag (`git tag -a vX.Y.Z`)

4. **Commit-Message**
   - Beginne mit "release:", "feat:", "fix:", "docs:" oder "chore:"

5. **Nach jedem neuen Tag**
   - Release-Pipeline (PyPI + Zenodo) wird automatisch ausgelöst

Diese Regeln sind bindend für alle Claude-Code-Runs und zukünftige Agents in GenesisAeon-Repos.
""",
        "src/${name_snake}/__init__.py": ('"""${name}."""\n\n__version__ = "0.1.0"\n'),
        "tests/__init__.py": "",
        "tests/test_main.py": """\
\"\"\"Tests for ${name}.\"\"\"

from ${name_snake} import __version__


def test_version():
    assert __version__ == "0.1.0"
""",
    },
}
