# Diamond Setup

**Universal Python project scaffold** — generate professional, CI-ready project skeletons in seconds.

No cookiecutter, no Jinja2, no magic. Just a clean CLI, sensible templates, and a validator that keeps your projects healthy.

## Quickstart

```bash
pip install diamond-setup
# or with uv:
uv tool install diamond-setup
```

```bash
diamond scaffold my-new-tool
cd my-new-tool && uv sync --dev && uv run pytest
```

## Why Diamond Setup?

| Feature | diamond-setup | cookiecutter | copier |
|---------|:---:|:---:|:---:|
| Zero config needed | ✅ | ❌ | ❌ |
| Built-in validator | ✅ | ❌ | ❌ |
| Pure Python templates | ✅ | ❌ | ❌ |
| `--dry-run` support | ✅ | ❌ | ✅ |
| Extensible presets | ✅ | ✅ | ✅ |

## Commands

| Command | Description |
|---------|-------------|
| `diamond scaffold <name>` | Create a new project |
| `diamond list-templates` | Show available templates |
| `diamond validate [path]` | Check a project's health |
| `diamond version` | Show version |
