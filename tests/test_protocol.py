"""Tests for DiamondPackage protocol and validation."""

from __future__ import annotations

from diamond_setup.protocol import (
    CREPState,
    DiamondPackage,
    NotConvergedError,
    UTACState,
    ZenodoCreator,
    ZenodoRecord,
)
from diamond_setup.validation import (
    check_diamond_class,
    validate_diamond_instance,
    validate_model_shapes,
)


class _DemoUTAC(DiamondPackage):
    def __init__(self) -> None:
        super().__init__()
        self._h = 0.3

    def _run_cycle(self) -> dict[str, float]:
        self._h = min(1.0, self._h + 0.1)
        return {"H": self._h, "step": float(self.cycles_completed + 1)}

    def _build_crep_state(self) -> CREPState:
        return CREPState(C=0.5, R=0.5, E=0.5, P=0.5)

    def _build_utac_state(self) -> UTACState:
        return UTACState(H=self._h, H_star=0.7, K_eff=1.0)

    def _build_phase_events(self) -> list[dict[str, str]]:
        return [{"phase": "activation", "cycle": str(self.cycles_completed)}]

    def _build_zenodo_record(self) -> ZenodoRecord:
        return ZenodoRecord(
            title="demo-utac",
            description="Diamond protocol test package",
            creators=[ZenodoCreator(name="Test")],
        )


def test_not_converged_before_run_cycle():
    pkg = _DemoUTAC()
    try:
        pkg.get_crep_state()
        raise AssertionError("expected NotConvergedError")
    except NotConvergedError as exc:
        assert exc.method == "get_crep_state"


def test_full_diamond_flow():
    pkg = _DemoUTAC()
    assert validate_diamond_instance(pkg) == []
    assert pkg.cycles_completed == 1
    crep = pkg.get_crep_state()
    assert crep["Gamma"] == 0.5
    assert pkg.run_cycle()["H"] == 0.5


def test_check_diamond_class():
    assert check_diamond_class(_DemoUTAC) == []
    assert len(check_diamond_class(object)) > 0  # type: ignore[arg-type]


def test_crep_gamma_geometric_mean():
    crep = CREPState(C=0.0, R=1.0, E=1.0, P=1.0)
    assert crep.Gamma == 0.0


def test_validate_model_shapes():
    assert validate_model_shapes() == []
