"""Tests für das Q4 Runtime Contract Schema und den Validator."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = REPO_ROOT / "contracts"
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "validate_runtime.py"

# Importiere validate_runtime direkt für Unit-Tests
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from validate_runtime import validate_runtime  # noqa: E402, I001


# ── Schema-Dateien vorhanden ─────────────────────────────────────────────────

def test_schema_file_exists():
    assert (CONTRACTS_DIR / "runtime.schema.yaml").exists()


def test_example_minimal_exists():
    assert (CONTRACTS_DIR / "example_minimal.yaml").exists()


def test_example_full_exists():
    assert (CONTRACTS_DIR / "example_full.yaml").exists()


# ── Unit-Tests: validate_runtime() ──────────────────────────────────────────

def _load(name: str) -> dict:
    with (CONTRACTS_DIR / name).open() as f:
        return yaml.safe_load(f)


def test_minimal_valid():
    assert validate_runtime(_load("example_minimal.yaml")) == []


def test_full_valid():
    assert validate_runtime(_load("example_full.yaml")) == []


def test_missing_runtime_key():
    errors = validate_runtime({"other": "value"})
    assert any("runtime" in e for e in errors)


def test_wrong_version():
    data = {"runtime": {"version": "2.0", "protocol": "q4"}}
    errors = validate_runtime(data)
    assert any("version" in e for e in errors)


def test_wrong_protocol():
    data = {"runtime": {"version": "1.0", "protocol": "grpc"}}
    errors = validate_runtime(data)
    assert any("protocol" in e for e in errors)


def test_state_bits_invariant():
    # 16 Zustände = 4 Bit — darf NICHT 16 sein
    data = {
        "runtime": {
            "version": "1.0",
            "protocol": "q4",
            "layers": {"state": {"enabled": True, "bits": 16, "states": 16}},
        }
    }
    errors = validate_runtime(data)
    assert any("bits" in e for e in errors)


def test_state_states_invariant():
    data = {
        "runtime": {
            "version": "1.0",
            "protocol": "q4",
            "layers": {"state": {"enabled": True, "bits": 4, "states": 32}},
        }
    }
    errors = validate_runtime(data)
    assert any("states" in e for e in errors)


def test_threshold_out_of_range():
    data = {
        "runtime": {
            "version": "1.0",
            "protocol": "q4",
            "layers": {
                "state": {
                    "enabled": True,
                    "bits": 4,
                    "states": 16,
                    "thresholds": {"C": 1.5},  # Ungültig
                }
            },
        }
    }
    errors = validate_runtime(data)
    assert any("thresholds.C" in e for e in errors)


def test_subject_must_start_with_ga():
    data = {
        "runtime": {
            "version": "1.0",
            "protocol": "q4",
            "layers": {
                "coupling": {
                    "enabled": True,
                    "transport": "nats",
                    "subjects": ["genesis.old.subject"],  # Ungültig
                }
            },
        }
    }
    errors = validate_runtime(data)
    assert any("ga." in e for e in errors)


def test_efc_coupling_blocked_in_production():
    data = {
        "runtime": {
            "version": "1.0",
            "protocol": "q4",
            "speculative": {"efc_coupling": True},
        }
    }
    errors = validate_runtime(data)
    assert any("efc_coupling" in e for e in errors)


def test_consciousness_model_blocked():
    data = {
        "runtime": {
            "version": "1.0",
            "protocol": "q4",
            "speculative": {"consciousness_model": True},
        }
    }
    errors = validate_runtime(data)
    assert any("consciousness_model" in e for e in errors)


# ── CLI Exit-Code Tests ──────────────────────────────────────────────────────

def test_cli_example_minimal_exits_0():
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--example-minimal"],
        capture_output=True,
    )
    assert result.returncode == 0


def test_cli_example_full_exits_0():
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--example-full"],
        capture_output=True,
    )
    assert result.returncode == 0


def test_cli_invalid_yaml_exits_1(tmp_path: Path):
    bad = tmp_path / "runtime.yaml"
    bad.write_text("runtime:\n  version: '99.9'\n  protocol: 'unknown'\n")
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), str(bad)],
        capture_output=True,
    )
    assert result.returncode == 1
