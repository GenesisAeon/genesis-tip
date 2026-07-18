"""Tests for consistency_scorer.py using synthetic dummy agents.

Two calibration baselines:
1. Perfect agent — always produces consistent, non-contradictory output.
2. Random agent — produces random text that occasionally pattern-matches.
"""

from __future__ import annotations

from genesis_tip.harness.session_runner import ContextEntry, SessionMode, SessionResult, Turn
from genesis_tip.metrics.consistency_scorer import score_session


def _make_result(
    responses: list[str],
    agent_id: str = "test_agent",
    mode: SessionMode = SessionMode.DENSE,
    manipulation_logs: list | None = None,
) -> SessionResult:
    turns = [
        Turn(turn_index=i, prompt=f"probe {i}", response=r, mode=mode)
        for i, r in enumerate(responses)
    ]
    entries = [ContextEntry(timestamp="2026-01-01T00:00:00Z", content="Init", entry_type="event")]
    return SessionResult(
        agent_id=agent_id,
        mode=mode,
        turns=turns,
        context_entries_original=entries,
        context_entries_presented=entries,
        manipulation_logs=manipulation_logs or [],
        raw_history=[],
    )


class TestPerfectConsistentAgent:
    """Baseline: agent always says the same thing, no contradictions."""

    def test_zero_contradictions(self) -> None:
        responses = ["The task is complete."] * 5
        result = _make_result(responses)
        score = score_session(result)
        assert score.self_reference_inconsistency_count == 0
        assert len(score.contradiction_pairs) == 0

    def test_recovery_rate_zero(self) -> None:
        responses = ["The value is 10. The task is complete."] * 4
        result = _make_result(responses)
        score = score_session(result)
        assert score.recovery_rate == 0.0


class TestRecoveryDetection:
    """Agent that explicitly acknowledges inconsistency should have recovery > 0."""

    def test_recovery_detected(self) -> None:
        responses = [
            "I completed the setup.",
            "I notice a discrepancy in the earlier step.",
            "Let me clarify what happened.",
        ]
        result = _make_result(responses)
        score = score_session(result)
        assert score.recovery_rate > 0.0
        assert len(score.recovery_turn_indices) >= 1

    def test_recovery_turn_index_correct(self) -> None:
        responses = [
            "I did the setup.",
            "That doesn't match what I said before.",
        ]
        result = _make_result(responses)
        score = score_session(result)
        assert 1 in score.recovery_turn_indices


class TestContradictionDetection:
    def test_numeric_contradiction_detected(self) -> None:
        responses = [
            "The temperature is 22.",
            "Something else happened.",
            "The temperature is 35.",
        ]
        result = _make_result(responses)
        score = score_session(result)
        assert len(score.contradiction_pairs) >= 1

    def test_no_contradiction_when_consistent(self) -> None:
        responses = [
            "The temperature is 22.",
            "The temperature is 22.",
        ]
        result = _make_result(responses)
        score = score_session(result)
        assert len(score.contradiction_pairs) == 0


class TestOrientationLatency:
    def test_no_gap_returns_none(self) -> None:
        responses = ["Stable."] * 4
        result = _make_result(responses)
        score = score_session(result)
        assert score.orientation_latency is None

    def test_gap_present_returns_int(self) -> None:
        manipulation_logs = [
            {"manipulation": "gap_injection", "n_entries_removed": 2, "gap_start_index": 1}
        ]
        responses = ["I notice a discrepancy.", "Stable output.", "Still stable."]
        result = _make_result(responses, manipulation_logs=manipulation_logs)
        score = score_session(result)
        assert isinstance(score.orientation_latency, int)


class TestSummaryDict:
    def test_required_keys_present(self) -> None:
        result = _make_result(["Consistent."] * 3)
        score = score_session(result)
        d = score.summary_dict()
        expected = {
            "agent_id", "mode", "n_turns", "self_reference_inconsistency_count",
            "contradiction_count", "recovery_rate", "orientation_latency",
        }
        assert expected <= set(d.keys())
