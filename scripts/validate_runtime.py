#!/usr/bin/env python3
"""validate_runtime.py — validiert eine runtime.yaml gegen das Q4-Runtime-Contract-Schema.

Verwendung:
  python scripts/validate_runtime.py path/to/runtime.yaml
  python scripts/validate_runtime.py --example-full    # Validiert example_full.yaml
  python scripts/validate_runtime.py --example-minimal # Validiert example_minimal.yaml

Exit-Codes:
  0 — Valide
  1 — Validierungsfehler
  2 — Datei nicht gefunden / Parse-Fehler
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

# Windows consoles default to a non-UTF-8 codepage, which breaks the ✓/✗
# markers below with UnicodeEncodeError. Force UTF-8 stdout/stderr so the
# script behaves the same on Windows as it already does in Linux CI.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Pfad relativ zu diesem Skript
_REPO_ROOT = Path(__file__).parent.parent
_SCHEMA_PATH = _REPO_ROOT / "contracts" / "runtime.schema.yaml"
_CONTRACTS_DIR = _REPO_ROOT / "contracts"

# ── CREP-Dimensionen und ihre Standardwerte ──────────────────────────────────
_CREP_DIMS = ("C", "R", "E", "P")
_DEFAULT_THRESHOLDS: dict[str, float] = {"C": 0.5, "R": 0.6, "E": 0.7, "P": 0.8}

# Q4-Zustandsraum-Invarianten (mathematisch verifiziert)
_Q4_BITS = 4
_Q4_STATES = 16   # log₂(16) = 4 Bit — 16 Zustände, NICHT 16 Bit
_GRAY_ORDER = [0, 1, 3, 2, 6, 7, 5, 4, 12, 13, 15, 14, 10, 11, 9, 8]


# ── Validierungslogik ────────────────────────────────────────────────────────

class ValidationError(Exception):
    pass


def _err(msg: str) -> None:
    print(f"  ✗ ERROR   {msg}", file=sys.stderr)


def _warn(msg: str) -> None:
    print(f"  ⚠ WARNING {msg}")


def _ok(msg: str) -> None:
    print(f"  ✓ OK      {msg}")


def validate_runtime(data: Any) -> list[str]:
    """Validiert ein gepartes runtime.yaml-Dict. Gibt Liste von Fehlern zurück."""
    errors: list[str] = []

    if not isinstance(data, dict) or "runtime" not in data:
        errors.append("Toplevel-Key 'runtime' fehlt")
        return errors

    rt = data["runtime"]

    # version
    version = rt.get("version")
    if version != "1.0":
        errors.append(f"runtime.version muss '1.0' sein, nicht '{version}'")
    else:
        _ok("version = '1.0'")

    # protocol
    protocol = rt.get("protocol")
    if protocol not in ("q4", "standard"):
        errors.append(f"runtime.protocol muss 'q4' oder 'standard' sein, nicht '{protocol}'")
    else:
        _ok(f"protocol = '{protocol}'")

    layers = rt.get("layers", {})

    # state layer
    state = layers.get("state", {})
    if state.get("enabled"):
        bits = state.get("bits")
        states = state.get("states")
        if bits != _Q4_BITS:
            errors.append(
                f"state.bits muss {_Q4_BITS} sein (4-Bit Q4-Zustandsraum). "
                f"Erhalten: {bits}"
            )
        else:
            _ok(f"state.bits = {_Q4_BITS}")
        if states != _Q4_STATES:
            errors.append(
                f"state.states muss {_Q4_STATES} sein (log₂(16) = 4 Bit). "
                f"Erhalten: {states}. Hinweis: 16 Zustände = 4 Bit, NICHT 16 Bit."
            )
        else:
            _ok(f"state.states = {_Q4_STATES}")

        thresholds = state.get("thresholds", {})
        for dim in _CREP_DIMS:
            val = thresholds.get(dim)
            if val is not None:
                if not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
                    errors.append(
                        f"state.thresholds.{dim} muss float in [0.0, 1.0] sein. "
                        f"Erhalten: {val}"
                    )
                else:
                    _ok(f"threshold.{dim} = {val}")

    # coupling layer
    coupling = layers.get("coupling", {})
    if coupling.get("enabled"):
        transport = coupling.get("transport", "none")
        if transport not in ("nats", "none"):
            errors.append(f"coupling.transport muss 'nats' oder 'none' sein. Erhalten: '{transport}'")
        else:
            _ok(f"coupling.transport = '{transport}'")

        subjects = coupling.get("subjects", [])
        for subj in subjects:
            if not isinstance(subj, str) or not subj.startswith("ga."):
                errors.append(
                    f"coupling.subjects-Einträge müssen mit 'ga.' beginnen. "
                    f"Ungültig: '{subj}'"
                )
        if subjects:
            _ok(f"coupling.subjects = {subjects}")

        if coupling.get("gray_code") is True:
            _ok("gray_code Policy Gate aktiviert (Hamming-Distanz = 1 erzwungen)")

    # speculative layer — Produktions-Schutz
    speculative = rt.get("speculative", {})
    if speculative.get("efc_coupling") is True:
        errors.append(
            "speculative.efc_coupling = true ist in Produktion verboten. "
            "Nur im efc-research-module erlaubt."
        )
    if speculative.get("consciousness_model") is True:
        errors.append("speculative.consciousness_model = true ist niemals in Produktion erlaubt.")

    return errors


def load_yaml(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Datei nicht gefunden: {path}", file=sys.stderr)
        sys.exit(2)
    except yaml.YAMLError as exc:
        print(f"YAML-Parse-Fehler in {path}: {exc}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validiert eine runtime.yaml gegen das Q4-Runtime-Contract-Schema."
    )
    parser.add_argument(
        "runtime_yaml",
        nargs="?",
        help="Pfad zur runtime.yaml (optional wenn --example-* gesetzt)",
    )
    parser.add_argument(
        "--example-full",
        action="store_true",
        help="Validiert contracts/example_full.yaml",
    )
    parser.add_argument(
        "--example-minimal",
        action="store_true",
        help="Validiert contracts/example_minimal.yaml",
    )
    args = parser.parse_args()

    if args.example_full:
        target = _CONTRACTS_DIR / "example_full.yaml"
    elif args.example_minimal:
        target = _CONTRACTS_DIR / "example_minimal.yaml"
    elif args.runtime_yaml:
        target = Path(args.runtime_yaml)
    else:
        parser.print_help()
        sys.exit(2)

    print(f"\nValidiere: {target}\n")
    data = load_yaml(target)
    errors = validate_runtime(data)

    if errors:
        print()
        for err in errors:
            _err(err)
        print(f"\n✗ Validierung fehlgeschlagen — {len(errors)} Fehler\n")
        sys.exit(1)
    else:
        print(f"\n✓ Validierung erfolgreich — {target.name} ist konform\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
