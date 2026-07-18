"""CREPGate for genesis-tip (P50).

Pre-registration anchor: commit 1cf1730 in multi-scale-somatic-coherence
  RHO_SEM_FALSIFICATION_THRESHOLD = 0.3
  RHO_SEM_MIN_SAMPLE_SIZE = 30

This is genesis-tip's OWN gate, not a copy of genesis-mssc's (P49)
domain-18 gate (mssc/crep_gate.py) — that gate's conditions
(coupling_significant, null_excluded, beta_fit_stable, replicated_shhs)
concern MSSC's own somatic-coherence domain claim, not TIP's role as an
external falsification instrument for Ρ_sem (scope-resilience, P41).
Only the underlying Spearman threshold/sample-size constants and the
`rho_sem_correlation_tested` condition are shared across both gates,
because both ultimately test the same P41 hypothesis.

The gate to P50 "passed" status: TIP produces Γ_somatic via a full
Diamond Interface (mssc/README.md, 2026-07-15: "TIP is a future P50
candidate ... once it produces Γ_somatic via a full Diamond Interface")
AND the Spearman correlation test runs with n >= 30 pairs.
"""

from __future__ import annotations

from enum import StrEnum

# PRE-REGISTERED CONSTANTS — do not change without a CHANGELOG entry
# "Pre-registration amendment: [old] -> [new], justification: ..."
RHO_SEM_FALSIFICATION_THRESHOLD: float = 0.3
RHO_SEM_MIN_SAMPLE_SIZE: int = 30


class CREPGateStatus(StrEnum):
    BLOCKED = "blocked"
    PENDING_REVIEW = "pending_review"
    PASSED = "passed"


GATE_CONDITIONS: dict[str, bool] = {
    # (a) TIP runs on >=1 real session (not synthetic-only)
    "real_session_data_available": False,
    # (b) Gamma_somatic produced via Diamond Interface
    "gamma_somatic_implemented": False,
    # (c) scope-resilience (P41) provides Rho_sem values
    "rho_sem_values_available": False,
    # (d) n >= RHO_SEM_MIN_SAMPLE_SIZE path-perturbation pairs
    "minimum_sample_size_reached": False,
    # (e) Spearman test run with the pre-registered threshold
    "rho_sem_correlation_tested": False,
}


def current_gate_status() -> CREPGateStatus:
    """Derive gate status from GATE_CONDITIONS.

    blocked        -> not all conditions met
    pending_review -> all 5 conditions met, awaiting independent review
    passed          -> explicitly confirmed after independent review
                       (this function never returns PASSED itself —
                       that transition is a human/maintainer action,
                       not something the gate infers on its own)
    """
    if all(GATE_CONDITIONS.values()):
        return CREPGateStatus.PENDING_REVIEW
    return CREPGateStatus.BLOCKED
