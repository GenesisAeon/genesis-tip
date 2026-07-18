"""Tests for the TIP Markdown report generator."""

from __future__ import annotations

from genesis_tip.metrics.consistency_scorer import ConsistencyScore
from genesis_tip.report.tip_report_template import generate_report


def _make_score(agent_id: str, mode: str) -> ConsistencyScore:
    return ConsistencyScore(agent_id=agent_id, mode=mode, n_turns=3)


class TestGenerateReport:
    def test_returns_markdown_string(self) -> None:
        scores = [_make_score("agent-a", "dense")]
        report = generate_report(scores)
        assert isinstance(report, str)
        assert "# TIP" in report

    def test_includes_behavioural_language_note(self) -> None:
        report = generate_report([_make_score("agent-a", "dense")])
        assert "observable" in report.lower()

    def test_comparison_table_lists_all_agents(self) -> None:
        scores = [
            _make_score("agent-a", "dense"),
            _make_score("agent-b", "fragmented"),
        ]
        report = generate_report(scores)
        assert "agent-a" in report
        assert "agent-b" in report

    def test_raw_data_path_included_when_given(self) -> None:
        report = generate_report([_make_score("agent-a", "dense")], raw_data_path="data/run1.json")
        assert "data/run1.json" in report

    def test_raw_scores_omitted_when_disabled(self) -> None:
        report = generate_report([_make_score("agent-a", "dense")], include_raw_scores=False)
        assert "Raw scores (JSON)" not in report
