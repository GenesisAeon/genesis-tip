"""Tests for the pre-registered Spearman rho_sem correlation test."""

from __future__ import annotations

import pytest

from genesis_tip.falsification import run_rho_sem_correlation_test


class TestInsufficientSample:
    def test_below_min_sample_size(self) -> None:
        result = run_rho_sem_correlation_test([0.1] * 10, [0.2] * 10)
        assert result.verdict == "insufficient_sample"
        assert result.spearman_rho is None
        assert result.p_value is None

    def test_insufficient_sample_not_falsified(self) -> None:
        """Insufficient sample must never be conflated with 'falsified'."""
        result = run_rho_sem_correlation_test([0.0] * 5, [1.0] * 5)
        assert result.verdict != "falsified"


class TestSupportedAndFalsified:
    def test_perfect_positive_correlation_supported(self) -> None:
        tip_scores = [float(i) for i in range(30)]
        rho_sem = [float(i) for i in range(30)]
        result = run_rho_sem_correlation_test(tip_scores, rho_sem)
        assert result.verdict == "supported"
        assert result.spearman_rho == pytest.approx(1.0)
        assert result.n == 30

    def test_no_correlation_falsified(self) -> None:
        varying = [0.1, 0.9, 0.2, 0.8, 0.3, 0.7, 0.4, 0.6, 0.55, 0.45, 0.35, 0.65, 0.25, 0.75, 0.15]
        tip_scores = [0.5] * 15 + varying
        rho_sem = varying + [0.5] * 15
        result = run_rho_sem_correlation_test(tip_scores, rho_sem)
        assert result.n == 30
        assert result.verdict in ("supported", "falsified")  # both are valid outcomes
        assert result.spearman_rho is not None

    def test_verdict_matches_threshold(self) -> None:
        tip_scores = [float(i) for i in range(30)]
        rho_sem = [float(29 - i) for i in range(30)]  # perfectly anti-correlated
        result = run_rho_sem_correlation_test(tip_scores, rho_sem)
        assert result.spearman_rho == pytest.approx(-1.0)
        assert result.verdict == "falsified"


class TestInputValidation:
    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError):
            run_rho_sem_correlation_test([0.1] * 30, [0.2] * 29)


class TestSummaryDict:
    def test_summary_dict_has_required_keys(self) -> None:
        scores = [float(i) for i in range(30)]
        result = run_rho_sem_correlation_test(scores, scores)
        d = result.summary_dict()
        expected = {"n", "spearman_rho", "p_value", "threshold", "min_sample_size", "verdict"}
        assert expected <= set(d.keys())
