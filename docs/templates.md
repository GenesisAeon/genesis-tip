# Templates

Diamond Setup ships two built-in templates. Adding your own is a single Python file.

---

## `minimal`

**The default.** A clean, modern Python project with everything you need and nothing you don't.

```bash
diamond scaffold my-lib
diamond scaffold my-lib --template minimal
```

### Files generated

```
my-lib/
├── src/
│   └── my_lib/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
├── README.md
├── .gitignore
└── .pre-commit-config.yaml
```

### Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `name` | *(required)* | Project name |
| `description` | `"A Python project"` | Short description |
| `author` | `"Your Name"` | Author name |
| `python_version` | `"3.11"` | Minimum Python version |

---

## `genesis`

A superset of `minimal` — adds a `domains.yaml` for domain/metric configuration and an `entropy-table` YAML bridge module.

```bash
diamond scaffold my-physics-tool --template genesis
```

### Extra files

```
my-physics-tool/
├── domains.yaml           ← domain/metric configuration
├── config/
│   └── entropy.yaml       ← entropy-table bridge config
└── src/
    └── my_physics_tool/
        ├── __init__.py
        └── bridge.py      ← entropy-table export function
```

### Extra variables

| Variable | Default | Description |
|----------|---------|-------------|
| `metrics` | `"crep"` | Default metrics identifier |

---

## Adding a Custom Template

1. Create `src/diamond_setup/templates/my_template.py`:

```python
TEMPLATE = {
    "name": "my_template",
    "description": "My custom template",
    "variables": ["name", "description", "author", "python_version"],
    "defaults": {
        "description": "My project",
        "author": "Your Name",
        "python_version": "3.11",
    },
    "files": {
        "README.md": "# ${name}\n\n${description}\n",
        "pyproject.toml": "...",
        # keys are relative paths, values are template strings
        # use ${variable} for substitution
        # use $$ for a literal dollar sign
    },
}
```

2. Register it in `src/diamond_setup/templates/__init__.py`:

```python
from .my_template import TEMPLATE as MY_TEMPLATE

REGISTRY: dict[str, dict] = {
    "minimal": MINIMAL_TEMPLATE,
    "genesis": GENESIS_TEMPLATE,
    "my_template": MY_TEMPLATE,  # ← add this
}
```

That's it. `diamond list-templates` will immediately show it.
