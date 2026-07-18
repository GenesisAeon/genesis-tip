# CLI Reference

## `diamond scaffold`

Create a new project from a template.

```
Usage: diamond scaffold [OPTIONS] PROJECT_NAME

Arguments:
  PROJECT_NAME  Name of the new project (kebab-case recommended)

Options:
  -t, --template TEXT       Template to use [default: minimal]
  -o, --output-dir PATH     Parent directory for the new project
  --author TEXT             Author name
  --description TEXT        Short project description
  --python-version TEXT     Minimum Python version (e.g. 3.11)
  --dry-run                 Preview files without writing them
```

**Examples**

```bash
# Minimal project in the current directory
diamond scaffold my-lib

# Genesis preset with custom author
diamond scaffold my-physics-tool --template genesis --author "Ada Lovelace"

# Preview what would be created
diamond scaffold my-lib --dry-run

# Output to a specific directory
diamond scaffold my-lib --output-dir ~/projects
```

---

## `diamond list-templates`

List all available templates with their descriptions.

```bash
diamond list-templates
```

---

## `diamond validate`

Validate a project directory against diamond-setup best practices.

```
Usage: diamond validate [PATH]

Arguments:
  PATH  Project directory to validate [default: current directory]
```

Checks performed:

| Check | Level |
|-------|-------|
| `pyproject.toml` present | **Error** |
| `src/` layout present | Warning |
| `tests/` directory present | Warning |
| `.github/workflows/` present | Warning |
| `README.md` present | Warning |
| `.gitignore` present | Warning |

```bash
# Validate the current directory
diamond validate

# Validate a specific project
diamond validate path/to/my-project
```

---

## `diamond version`

Print the installed version.

```bash
diamond version
```
