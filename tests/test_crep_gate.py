"""Tests for genesis-tip's own CREPGate (P50)."""

from __future__ import annotations

from genesis_tip.crep_gate import (
    GATE_CONDITIONS,
    RHO_SEM_FALSIFICATION_THRESHOLD,
    RHO_SEM_MIN_SAMPLE_SIZE,
    CREPGateStatus,
    current_gate_status,
)


class TestPreRegisteredConstants:
    def test_threshold_unchanged(self) -> None:
        """Pre-registration anchor (commit 1cf1730): threshold must be 0.3."""
        assert RHO_SEM_FALSIFICATION_THRESHOLD == 0.3

    def test_sample_size_unchanged(self) -> None:
        """Pre-registration anchor (commit 1cf1730): min sample size must be 30."""
        assert RHO_SEM_MIN_SAMPLE_SIZE == 30


class TestGateStatus:
    def test_gate_has_five_conditions(self) -> None:
        assert len(GATE_CONDITIONS) == 5

    def test_initial_status_blocked(self) -> None:
        assert all(not v for v in GATE_CONDITIONS.values())
        assert current_gate_status() == CREPGateStatus.BLOCKED

    def test_all_conditions_true_yields_pending_review(self) -> None:
        original = dict(GATE_CONDITIONS)
        try:
            for key in GATE_CONDITIONS:
                GATE_CONDITIONS[key] = True
            assert current_gate_status() == CREPGateStatus.PENDING_REVIEW
        finally:
            GATE_CONDITIONS.update(original)

    def test_current_gate_status_never_returns_passed(self) -> None:
        """PASSED requires an explicit human/maintainer action, not inference."""
        original = dict(GATE_CONDITIONS)
        try:
            for key in GATE_CONDITIONS:
                GATE_CONDITIONS[key] = True
            assert current_gate_status() != CREPGateStatus.PASSED
        finally:
            GATE_CONDITIONS.update(original)
