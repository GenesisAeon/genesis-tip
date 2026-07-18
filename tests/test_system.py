"""Tests for TemporalIntegrityProbe (Diamond Interface, P50)."""

from __future__ import annotations

import pytest

from genesis_tip.crep_gate import RHO_SEM_FALSIFICATION_THRESHOLD
from genesis_tip.system import TemporalIntegrityProbe


class TestConstruction:
    def test_default_perturbation_mode(self) -> None:
        tip = TemporalIntegrityProbe()
        assert tip.perturbation_mode == "shuffle"

    def test_invalid_perturbation_mode_raises(self) -> None:
        with pytest.raises(ValueError):
            TemporalIntegrityProbe(perturbation_mode="not-a-real-mode")

    def test_gap_mode_accepted(self) -> None:
        tip = TemporalIntegrityProbe(perturbation_mode="gap")
        assert tip.perturbation_mode == "gap"

    def test_contradict_mode_accepted(self) -> None:
        tip = TemporalIntegrityProbe(perturbation_mode="contradict")
        assert tip.perturbation_mode == "contradict"


class TestRunCycle:
    def setup_method(self) -> None:
        self.tip = TemporalIntegrityProbe()

    def test_run_cycle_returns_dict(self) -> None:
        result = self.tip.run_cycle()
        assert isinstance(result, dict)

    def test_run_cycle_has_consistency_score(self) -> None:
        result = self.tip.run_cycle()
        assert "consistency_score" in result
        assert 0.0 <= result["consistency_score"] <= 1.0

    def test_run_cycle_has_breakdown(self) -> None:
        result = self.tip.run_cycle()
        breakdown = result["consistency_breakdown"]
        for key in (
            "agent_id", "mode", "n_turns",
            "self_reference_inconsistency_count",
            "contradiction_count", "recovery_rate", "orientation_latency",
        ):
            assert key in breakdown

    def test_synthetic_demo_has_three_turns(self) -> None:
        result = self.tip.run_cycle()
        assert result["n_turns"] == 3

    def test_multiple_cycles_accumulate_sessions(self) -> None:
        self.tip.run_cycle()
        self.tip.run_cycle()
        result = self.tip.run_cycle()
        assert result["n_sessions"] == 3

    def test_gap_mode_run_cycle(self) -> None:
        tip = TemporalIntegrityProbe(perturbation_mode="gap")
        result = tip.run_cycle()
        assert isinstance(result["consistency_score"], float)

    def test_contradict_mode_run_cycle(self) -> None:
        tip = TemporalIntegrityProbe(perturbation_mode="contradict")
        result = tip.run_cycle()
        assert isinstance(result["consistency_score"], float)


class TestDiamondInterface:
    def setup_method(self) -> None:
        self.tip = TemporalIntegrityProbe()

    def test_crep_state_gamma_none_when_blocked(self) -> None:
        """Gamma must be None before gate is open — not a random number."""
        crep = self.tip.get_crep_state()
        assert crep["Gamma"] is None

    def test_utac_state_none_before_run_cycle(self) -> None:
        utac = self.tip.get_utac_state()
        assert utac["H"] is None

    def test_utac_state_has_required_keys_after_run(self) -> None:
        self.tip.run_cycle()
        utac = self.tip.get_utac_state()
        assert all(k in utac for k in ["H", "H_star", "K_eff"])

    def test_utac_h_star_equals_threshold(self) -> None:
        self.tip.run_cycle()
        utac = self.tip.get_utac_state()
        assert utac["H_star"] == RHO_SEM_FALSIFICATION_THRESHOLD

    def test_phase_events_returns_list(self) -> None:
        self.tip.run_cycle()
        events = self.tip.get_phase_events()
        assert isinstance(events, list)

    def test_resilience_state_not_implemented(self) -> None:
        state = self.tip.get_resilience_state()
        assert state["implemented"] is False
        assert state["rho"] is None

    def test_zenodo_record_has_required_fields(self) -> None:
        zr = self.tip.to_zenodo_record()
        assert all(k in zr for k in ["title", "description", "creators"])
        assert "P50" in zr["title"]
        assert "1cf1730" in zr["description"]


class TestCustomAgent:
    def test_custom_agent_fn_used(self) -> None:
        calls: list[list[dict[str, str]]] = []

        def recording_agent(messages: list[dict[str, str]]) -> str:
            calls.append(messages)
            return "A fixed, consistent response."

        tip = TemporalIntegrityProbe(agent_fn=recording_agent)
        tip.run_cycle()
        assert len(calls) == 3  # 3 synthetic demo probes

    def test_perfectly_consistent_agent_scores_high(self) -> None:
        def consistent_agent(messages: list[dict[str, str]]) -> str:
            return "Everything is consistent."

        tip = TemporalIntegrityProbe(agent_fn=consistent_agent)
        result = tip.run_cycle()
        assert result["consistency_score"] == 1.0
