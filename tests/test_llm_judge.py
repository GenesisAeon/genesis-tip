"""Tests for the optional LLM-judge contradiction detector.

No real subprocess/network calls here - grok_judge's plumbing is tested
against a mocked subprocess.run, and score_session's judge integration is
tested against fake in-process JudgeCallable functions. Real end-to-end
grok CLI calls were verified manually (see epistemic_status.md,
"Live-agent pilot" and the LLM-judge follow-up entries) and are
deliberately not part of the automated suite, since CI has neither the
grok CLI installed nor an authenticated account.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from genesis_tip.harness.session_runner import ContextEntry, SessionMode, SessionResult, Turn
from genesis_tip.metrics.consistency_scorer import score_session
from genesis_tip.metrics.llm_judge import JudgeError, _parse_boolean_answer, grok_judge


def _make_result(responses: list[str]) -> SessionResult:
    turns = [
        Turn(turn_index=i, prompt=f"probe {i}", response=r, mode=SessionMode.DENSE)
        for i, r in enumerate(responses)
    ]
    entries = [ContextEntry(timestamp="2026-01-01T00:00:00Z", content="Init", entry_type="event")]
    return SessionResult(
        agent_id="test_agent",
        mode=SessionMode.DENSE,
        turns=turns,
        context_entries_original=entries,
        context_entries_presented=entries,
        manipulation_logs=[],
        raw_history=[],
    )


class TestParseBooleanAnswer:
    def test_yes(self) -> None:
        assert _parse_boolean_answer("YES") is True

    def test_no(self) -> None:
        assert _parse_boolean_answer("NO") is False

    def test_lowercase(self) -> None:
        assert _parse_boolean_answer("yes\n") is True

    def test_embedded_in_sentence(self) -> None:
        assert _parse_boolean_answer("The answer is NO, they do not conflict.") is False

    def test_unparseable_raises(self) -> None:
        with pytest.raises(JudgeError):
            _parse_boolean_answer("I'm not sure how to answer that.")


class TestGrokJudgeSubprocessPlumbing:
    @patch("genesis_tip.metrics.llm_judge.subprocess.run")
    def test_successful_call(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="YES\n", stderr="")
        result = grok_judge("The meeting was Monday.", "The meeting was Tuesday.")
        assert result is True
        args = mock_run.call_args[0][0]
        assert args[0] == "grok"
        assert args[1] == "-p"

    @patch("genesis_tip.metrics.llm_judge.subprocess.run")
    def test_nonzero_exit_raises(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not logged in")
        with pytest.raises(JudgeError):
            grok_judge("a", "b")

    @patch("genesis_tip.metrics.llm_judge.time.sleep")
    @patch("genesis_tip.metrics.llm_judge.subprocess.run")
    def test_min_interval_throttles_second_call(
        self, mock_run: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Rate-limit finding from the Qwen batch (16/24 calls failed once the
        free tier's per-minute limit was hit) - min_interval_seconds paces
        sequential calls instead of firing them back-to-back."""
        import genesis_tip.metrics.llm_judge as llm_judge_module

        llm_judge_module._last_grok_call_at = None
        mock_run.return_value = MagicMock(returncode=0, stdout="NO\n", stderr="")

        grok_judge("a", "b", min_interval_seconds=30.0)
        mock_sleep.assert_not_called()  # first call: nothing to wait for

        grok_judge("c", "d", min_interval_seconds=30.0)
        mock_sleep.assert_called_once()
        waited = mock_sleep.call_args[0][0]
        assert 0 < waited <= 30.0

    @patch("genesis_tip.metrics.llm_judge.subprocess.run")
    def test_missing_binary_raises_judge_error(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = FileNotFoundError("grok not found")
        with pytest.raises(JudgeError):
            grok_judge("a", "b")

    @patch("genesis_tip.metrics.llm_judge.subprocess.run")
    def test_timeout_error_does_not_leak_judged_text(self, mock_run: MagicMock) -> None:
        """TimeoutExpired's default repr embeds the full argv (i.e. the judged
        text verbatim) - the raised JudgeError must not reproduce it."""
        secret_text = "SENSITIVE_MARKER_e8f3a1 should never appear in the error"
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["grok", "-p", secret_text], timeout=60.0
        )
        with pytest.raises(JudgeError) as excinfo:
            grok_judge(secret_text, "b")
        assert "SENSITIVE_MARKER_e8f3a1" not in str(excinfo.value)


class TestScoreSessionJudgeIntegration:
    def test_no_judge_preserves_existing_behaviour(self) -> None:
        """judge=None (default) must not change any existing regex-only result."""
        responses = ["The temperature is 22.", "Something else.", "The temperature is 35."]
        result = _make_result(responses)
        score_without = score_session(result)
        score_with_none = score_session(result, judge=None)
        assert score_without.contradiction_pairs == score_with_none.contradiction_pairs

    def test_judge_flags_additional_contradiction(self) -> None:
        """Text with no regex-detectable contradiction, but judge says YES."""
        responses = ["The launch went smoothly.", "Actually the launch failed entirely."]

        def always_contradicts(_a: str, _b: str) -> bool:
            return True

        result = _make_result(responses)
        score = score_session(result, judge=always_contradicts)
        assert len(score.contradiction_pairs) == 1
        assert "llm-judge" in score.contradiction_pairs[0][2]

    def test_judge_returning_false_adds_nothing(self) -> None:
        responses = ["All good.", "Still all good."]

        def never_contradicts(_a: str, _b: str) -> bool:
            return False

        result = _make_result(responses)
        score = score_session(result, judge=never_contradicts)
        assert score.contradiction_pairs == []

    def test_judge_does_not_duplicate_regex_detected_pair(self) -> None:
        responses = ["The temperature is 22.", "The temperature is 35."]

        def always_contradicts(_a: str, _b: str) -> bool:
            return True

        result = _make_result(responses)
        score = score_session(result, judge=always_contradicts)
        # regex already flags (0, 1) - judge must not add a second entry for the same pair
        assert len(score.contradiction_pairs) == 1

    def test_judge_error_recorded_as_note_not_raised(self) -> None:
        def failing_judge(_a: str, _b: str) -> bool:
            raise JudgeError("simulated backend failure")

        result = _make_result(["First.", "Second."])
        score = score_session(result, judge=failing_judge)
        assert score.contradiction_pairs == []
        assert any("llm_judge" in n for n in score.notes)
