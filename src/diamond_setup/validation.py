"""Runtime validation helpers for Diamond-interface compliance."""

from __future__ import annotations

import inspect
from typing import Any

from diamond_setup.protocol import (
    CREPState,
    DiamondPackage,
    NotConvergedError,
    UTACState,
    ZenodoCreator,
    ZenodoRecord,
)

REQUIRED_METHODS = (
    "run_cycle",
    "get_crep_state",
    "get_utac_state",
    "get_phase_events",
    "to_zenodo_record",
)

CREP_KEYS = frozenset({"C", "R", "E", "P", "Gamma"})
UTAC_KEYS = frozenset({"H", "H_star", "K_eff"})
ZENODO_KEYS = frozenset({"title", "description", "creators"})


def check_diamond_class(cls: type[Any]) -> list[str]:
    """Return a list of interface violations for *cls* (empty = OK)."""
    errors: list[str] = []
    if not inspect.isclass(cls):
        return [f"{cls!r} is not a class"]

    for name in REQUIRED_METHODS:
        if not callable(getattr(cls, name, None)):
            errors.append(f"missing callable: {name}")

    if not issubclass(cls, DiamondPackage):
        errors.append(f"{cls.__name__} should subclass diamond_setup.DiamondPackage")

    return errors


def validate_diamond_instance(
    instance: Any,
    *,
    run_cycle: bool = True,
    check_pre_cycle_guard: bool = True,
) -> list[str]:
    """Exercise the five Diamond methods and validate return schemas."""
    errors = check_diamond_class(type(instance))
    if errors:
        return errors

    if check_pre_cycle_guard:
        try:
            instance.get_crep_state()
            errors.append("get_crep_state should raise NotConvergedError before run_cycle")
        except NotConvergedError:
            pass
        except Exception as exc:
            errors.append(f"get_crep_state pre-cycle: {exc}")

    if run_cycle:
        try:
            result = instance.run_cycle()
            if not isinstance(result, dict):
                errors.append(f"run_cycle returned {type(result).__name__}, expected dict")
        except Exception as exc:
            errors.append(f"run_cycle failed: {exc}")
            return errors

    for method, expected_type, keys in (
        ("get_crep_state", dict, CREP_KEYS),
        ("get_utac_state", dict, UTAC_KEYS),
        ("to_zenodo_record", dict, ZENODO_KEYS),
    ):
        try:
            value = getattr(instance, method)()
            if not isinstance(value, expected_type):
                errors.append(f"{method} returned {type(value).__name__}")
                continue
            missing = keys - set(value.keys())
            if missing:
                errors.append(f"{method} missing keys: {sorted(missing)}")
        except Exception as exc:
            errors.append(f"{method} failed: {exc}")

    try:
        events = instance.get_phase_events()
        if not isinstance(events, list):
            errors.append(f"get_phase_events returned {type(events).__name__}")
    except Exception as exc:
        errors.append(f"get_phase_events failed: {exc}")

    return errors


def validate_model_shapes() -> list[str]:
    """Sanity-check Pydantic models (for CI without a domain package)."""
    errors: list[str] = []
    try:
        crep = CREPState(C=0.5, R=0.5, E=0.5, P=0.5)
        if crep.Gamma is None or crep.Gamma <= 0:
            errors.append("CREPState Gamma computation failed")
        utac = UTACState(H=0.4, H_star=0.6, K_eff=1.0)
        if set(utac.as_dict()) != UTAC_KEYS:
            errors.append("UTACState keys mismatch")
        zen = ZenodoRecord(
            title="t",
            description="d",
            creators=[ZenodoCreator(name="Test")],
        )
        if set(zen.as_dict()) >= ZENODO_KEYS:
            pass
        else:
            errors.append("ZenodoRecord keys mismatch")
    except Exception as exc:
        errors.append(f"model shapes: {exc}")
    return errors
