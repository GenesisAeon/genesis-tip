"""Pre-registered falsification test for genesis-tip (P50).

Gate condition (e) in crep_gate.py: the Spearman rank correlation between
TIP consistency scores and Ρ_sem values (scope-resilience, P41) across
n >= RHO_SEM_MIN_SAMPLE_SIZE path-perturbation pairs.

Pre-registration anchor: commit 1cf1730 (multi-scale-somatic-coherence,
2026-07-15). The threshold and minimum sample size are fixed in
crep_gate.py and must not be changed here or anywhere else without a
CHANGELOG "Pre-registration amendment" entry.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy import stats

from genesis_tip.crep_gate import (
    RHO_SEM_FALSIFICATION_THRESHOLD,
    RHO_SEM_MIN_SAMPLE_SIZE,
)


@dataclass
class RhoSemCorrelationResult:
    """Result of the pre-registered Spearman correlation test.

    verdict is one of "supported", "falsified", or "insufficient_sample"
    (n < RHO_SEM_MIN_SAMPLE_SIZE — the test did not run against the
    pre-registered criteria at all, this is not the same as "falsified").
    """

    n: int
    spearman_rho: float | None
    p_value: float | None
    threshold: float
    min_sample_size: int
    verdict: str

    def summary_dict(self) -> dict[str, float | int | str | None]:
        return {
            "n": self.n,
            "spearman_rho": self.spearman_rho,
            "p_value": self.p_value,
            "threshold": self.threshold,
            "min_sample_size": self.min_sample_size,
            "verdict": self.verdict,
        }


def run_rho_sem_correlation_test(
    tip_scores: list[float],
    rho_sem_values: list[float],
) -> RhoSemCorrelationResult:
    """Run the pre-registered Spearman correlation test.

    Parameters
    ----------
    tip_scores:
        TIP consistency scores, one per path-perturbation pair.
    rho_sem_values:
        Corresponding Ρ_sem values from scope-resilience (P41), same
        pairing/order as ``tip_scores``.

    Returns
    -------
    RhoSemCorrelationResult

    Raises
    ------
    ValueError
        If the two sequences have different lengths.

    Notes
    -----
    Both "supported" (rho >= threshold) and "falsified" (rho < threshold)
    are valid scientific outcomes at n >= min_sample_size. Neither this
    function nor any caller should adjust ``threshold``/``min_sample_size``
    after seeing the result — see crep_gate.py's pre-registration note.
    """
    if len(tip_scores) != len(rho_sem_values):
        raise ValueError(
            f"tip_scores (n={len(tip_scores)}) and rho_sem_values "
            f"(n={len(rho_sem_values)}) must have the same length."
        )

    n = len(tip_scores)

    if n < RHO_SEM_MIN_SAMPLE_SIZE:
        return RhoSemCorrelationResult(
            n=n,
            spearman_rho=None,
            p_value=None,
            threshold=RHO_SEM_FALSIFICATION_THRESHOLD,
            min_sample_size=RHO_SEM_MIN_SAMPLE_SIZE,
            verdict="insufficient_sample",
        )

    result = stats.spearmanr(tip_scores, rho_sem_values)
    rho = float(result.statistic)
    p_value = float(result.pvalue)

    verdict = "supported" if rho >= RHO_SEM_FALSIFICATION_THRESHOLD else "falsified"

    return RhoSemCorrelationResult(
        n=n,
        spearman_rho=rho,
        p_value=p_value,
        threshold=RHO_SEM_FALSIFICATION_THRESHOLD,
        min_sample_size=RHO_SEM_MIN_SAMPLE_SIZE,
        verdict=verdict,
    )
