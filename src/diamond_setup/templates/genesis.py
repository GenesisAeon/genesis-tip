"""Genesis template — superset of minimal, adds domain/metrics YAML and entropy-table bridge."""

import copy

from diamond_setup._types import TemplateDict

from .minimal import TEMPLATE as MINIMAL_TEMPLATE

_extra_files = {
    "domains.yaml": """\
# Domain configuration for ${name}
# Compatible with entropy-table bridge format
domains:
  primary:
    name: "${name}"
    metrics: ${metrics}
    description: "${description}"

relations: []

metadata:
  project: "${name}"
  author: "${author}"
  version: "0.1.0"
""",
    "config/entropy.yaml": """\
# entropy-table bridge configuration
bridge:
  source_project: "${name}"
  export_format: "entropy-table-v1"
  domains_file: "domains.yaml"
  output: "exports/entropy-table.yaml"

options:
  sort_keys: false
  allow_unicode: true
""",
    "src/${name_snake}/bridge.py": """\
\"\"\"entropy-table YAML bridge for ${name}.\"\"\"

from __future__ import annotations

from pathlib import Path

import yaml


def export_to_entropy_table(
    input_path: str | Path = "domains.yaml",
    output_path: str | Path = "exports/entropy-table.yaml",
) -> Path:
    \"\"\"Export domain YAML to entropy-table compatible format.\"\"\"
    input_path = Path(input_path)
    output_path = Path(output_path)

    with input_path.open() as f:
        data = yaml.safe_load(f)

    entropy_data = {
        "domains": data.get("domains", {}),
        "relations": data.get("relations", []),
        "metadata": {
            **data.get("metadata", {}),
            "generated_by": "${name} (diamond-setup v1.0.0)",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(entropy_data, sort_keys=False, allow_unicode=True))
    return output_path
""",
}

_genesis: TemplateDict = copy.deepcopy(MINIMAL_TEMPLATE)
_genesis["name"] = "genesis"
_genesis["description"] = "GenesisAeon project with domain/metrics YAML and entropy-table bridge"
_genesis["variables"] = MINIMAL_TEMPLATE["variables"] + ["metrics"]
_genesis["defaults"] = {
    **MINIMAL_TEMPLATE["defaults"],
    "metrics": "crep",
}
_genesis["files"] = {**MINIMAL_TEMPLATE["files"], **_extra_files}

TEMPLATE: TemplateDict = _genesis
