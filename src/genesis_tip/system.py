"""TemporalIntegrityProbe — Diamond Interface main class (P50).

Status: CREPGateStatus.BLOCKED
Reason: Gamma_somatic not yet implemented. run_cycle() produces a derived
        consistency score from real session/manipulation/scoring
        machinery (ported from genesis-mssc's mssc.tip, see
        harness/session_runner.py, manipulations/, metrics/), but that
        score is a convenience composite for the Diamond Interface's
        H/UTAC framing — NOT the pre-registered metric itself. The
        pre-registered test is the Spearman rho_sem correlation in
        falsification.py, run separately once real scope-resilience
        (P41) Ρ_sem values exist alongside real TIP scores.

Connection to P41 (scope-resilience):
  TIP consistency scores are hypothesised to rank-correlate
  (Spearman rho >= 0.3, n >= 30) with Rho_sem from scope-resilience.
  Pre-registration: commit 1cf1730 (multi-scale-somatic-coherence).
"""

from __future__ import annotations

import datetime
from typing import Any

from genesis_tip.crep_gate import (
    RHO_SEM_FALSIFICATION_THRESHOLD,
    CREPGateStatus,
    current_gate_status,
)
from genesis_tip.harness.session_runner import (
    AgentCallable,
    ContextEntry,
    SessionMode,
    SessionRunner,
)
from genesis_tip.manipulations.contradiction_injection import contradiction_injection
from genesis_tip.manipulations.gap_injection import gap_injection
from genesis_tip.manipulations.temporal_shuffle import temporal_shuffle
from genesis_tip.metrics.consistency_scorer import ConsistencyScore, score_session

_MANIPULATORS = {
    "shuffle": lambda entries: temporal_shuffle(entries),
    "gap": lambda entries: gap_injection(entries),
}


def _dummy_agent(messages: list[dict[str, str]]) -> str:
    """Deterministic stand-in agent for offline/CI-safe testing.

    Not a real LLM call and not a claim about any real agent's
    behaviour — it exists only so run_cycle() is exercisable without
    network access or an API key. Real TIP evaluations must pass a real
    ``agent_fn`` (e.g. wrapping the Inter-AI-Bridge adapter).
    """
    last_user = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    return f"Acknowledged: {last_user}"


class TemporalIntegrityProbe:
    """Temporal Integrity Probe — P50.

    Probes whether an agent's text outputs remain internally consistent
    when the temporal context it receives is manipulated:
      - shuffle: chronological order randomised
      - gap: time intervals silently removed
      - contradict: conflicting facts injected

    "Temporal": specifically perturbs chronological structure.
    "Integrity": behavioural, not mental — checks structural consistency.
    "Probe": observable text behaviour only, no internal-state claims.
    See docs/epistemic_boundaries.md for the full governance policy this
    package inherits from genesis-mssc's TIP module.

    Current output: a derived consistency_score in [0, 1] plus the full
    ConsistencyScore breakdown (self-reference inconsistencies,
    contradictions, recovery rate, orientation latency).
    Future output (gate condition b): Gamma_somatic via Diamond Interface.
    """

    def __init__(
        self,
        agent_fn: AgentCallable | None = None,
        perturbation_mode: str = "shuffle",
    ) -> None:
        if perturbation_mode not in (*_MANIPULATORS, "contradict"):
            raise ValueError(
                f"perturbation_mode must be one of "
                f"{(*_MANIPULATORS, 'contradict')}, got {perturbation_mode!r}"
            )
        self._agent_fn: AgentCallable = agent_fn or _dummy_agent
        self.perturbation_mode = perturbation_mode
        self._sessions: list[dict[str, Any]] = []
        self._consistency_scores: list[float] = []
        self._gate_status = current_gate_status()

    def run_cycle(
        self,
        context_entries: list[ContextEntry] | None = None,
        probes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run one TIP evaluation cycle.

        Parameters
        ----------
        context_entries:
            Chronological context for the agent. If None: a synthetic
            demo context is used (offline/CI-safe, not real session data
            — gate condition (a) stays unmet regardless of how many
            times this runs with synthetic data).
        probes:
            Probe prompts sent to the agent in sequence. If None: a
            synthetic demo set is used.

        Returns
        -------
        dict with:
          consistency_score: float in [0, 1] — derived composite, see
            module docstring; NOT the pre-registered metric itself.
          consistency_breakdown: ConsistencyScore.summary_dict()
          perturbation_mode: str
          n_turns: int
          gate_status: str
          note: explanation of current limitations
        """
        if context_entries is None:
            context_entries = self._synthetic_demo_context()
        if probes is None:
            probes = self._synthetic_demo_probes()

        manipulator = self._build_manipulator(context_entries)
        runner = SessionRunner(
            agent_fn=self._agent_fn,
            mode=SessionMode.FRAGMENTED,
            agent_id="tip-run-cycle",
            manipulator=manipulator,
        )
        result = runner.run(context_entries, probes)
        score = score_session(result)
        derived_score = self._derive_scalar_score(score)

        self._sessions.append({"result": result, "score": score})
        self._consistency_scores.append(derived_score)

        return {
            "consistency_score": derived_score,
            "consistency_breakdown": score.summary_dict(),
            "perturbation_mode": self.perturbation_mode,
            "n_turns": len(result.turns),
            "n_sessions": len(self._sessions),
            "gate_status": str(self._gate_status),
            "note": (
                "Gamma_somatic not yet implemented. consistency_score is a "
                "derived composite for Diamond Interface compatibility, not "
                "the pre-registered metric — see falsification.py for the "
                "actual Spearman rho_sem test (gate condition e). "
                f"Diamond Interface fully available when "
                f"gate_status={CREPGateStatus.PENDING_REVIEW}."
            ),
        }

    def get_crep_state(self) -> dict[str, Any]:
        """CREP state — Gamma is None until gate condition (b) is met.

        Returning None is correct: Gamma is a trajectory property, not
        an initial value. Even after run_cycle(), Gamma_somatic requires
        gate_status != blocked.
        """
        if self._gate_status == CREPGateStatus.BLOCKED:
            return {
                "C": None, "R": None, "E": None, "P": None,
                "Gamma": None,
                "note": "CREPGateStatus=BLOCKED: Gamma_somatic not yet implemented",
            }
        raise NotImplementedError(
            "Gamma_somatic will be implemented when gate condition (b) is "
            "met: real session data + Rho_sem values available."
        )

    def get_utac_state(self) -> dict[str, Any]:
        """UTAC state — H is the mean derived consistency score.

        H_star reuses RHO_SEM_FALSIFICATION_THRESHOLD as a threshold
        analogy (both represent "the minimum value for TIP's signal to
        be considered meaningful") — this is a metaphorical reuse across
        two different measurement scales (a rank-correlation coefficient
        vs. a mean consistency score), not a claim that they are the
        same quantity.
        """
        if not self._consistency_scores:
            return {"H": None, "H_star": None, "K_eff": None}
        h = sum(self._consistency_scores) / len(self._consistency_scores)
        return {
            "H": h,
            "H_star": RHO_SEM_FALSIFICATION_THRESHOLD,
            "K_eff": 1.0,
        }

    def get_phase_events(self) -> list[dict[str, Any]]:
        """Sessions where the derived consistency score dropped below
        the pre-registered falsification threshold."""
        return [
            {
                "type": "consistency_below_threshold",
                "session_idx": i,
                "score": s,
                "threshold": RHO_SEM_FALSIFICATION_THRESHOLD,
            }
            for i, s in enumerate(self._consistency_scores)
            if s < RHO_SEM_FALSIFICATION_THRESHOLD
        ]

    def get_resilience_state(self) -> dict[str, Any]:
        """6th Diamond method — not yet meaningful without Gamma_somatic."""
        return {
            "rho": None,
            "implemented": False,
            "note": "Available after gate_status=pending_review",
        }

    def to_zenodo_record(self) -> dict[str, Any]:
        return {
            "title": (
                "genesis-tip — P50: Temporal Integrity Probe for "
                "LLM behavioural consistency under context manipulation"
            ),
            "description": (
                "Measures whether LLM agents' text outputs remain "
                "internally consistent when temporal context is "
                "manipulated (shuffled, gapped, contradicted). "
                "Outputs consistency scores hypothesised to "
                f"rank-correlate (Spearman rho >= "
                f"{RHO_SEM_FALSIFICATION_THRESHOLD}) with Rho_sem from "
                "scope-resilience (P41). "
                "Pre-registration: commit 1cf1730 "
                "(multi-scale-somatic-coherence). "
                "Behavioural language only — see docs/epistemic_boundaries.md. "
                "GenesisAeon P50."
            ),
            "creators": [
                {"name": "Römer, Johann",
                 "affiliation": "MOR Research Collective"}
            ],
            "communities": [{"identifier": "genesisaeon"}],
        }

    # -- internals --------------------------------------------------------

    def _build_manipulator(self, context_entries: list[ContextEntry]):
        if self.perturbation_mode in _MANIPULATORS:
            return _MANIPULATORS[self.perturbation_mode]

        # perturbation_mode == "contradict": build a spec against the
        # synthetic demo's known contradictable fact. A caller passing
        # custom context_entries with perturbation_mode="contradict"
        # must ensure at least one entry contains "42" (the demo's
        # placeholder claim) or override this via a subclass/spec.
        spec = [
            {
                "entry_index": 0,
                "find": "42",
                "replace": "99",
                "label": "demo_value_flip",
            }
        ]
        return lambda entries: contradiction_injection(entries, spec)

    def _derive_scalar_score(self, score: ConsistencyScore) -> float:
        """Derived composite consistency_score in [0, 1].

        NOT itself pre-registered — a convenience scalar for the Diamond
        Interface's H/UTAC framing. 1.0 = no detected inconsistencies or
        contradictions; decreases with more of either, relative to
        session length.
        """
        if score.n_turns == 0:
            return 0.0
        n_issues = score.self_reference_inconsistency_count + len(score.contradiction_pairs)
        return max(0.0, 1.0 - min(1.0, n_issues / score.n_turns))

    def _synthetic_demo_context(self) -> list[ContextEntry]:
        base = datetime.datetime(2026, 1, 1)
        return [
            ContextEntry(
                timestamp=(base + datetime.timedelta(hours=i)).isoformat(),
                content=f"Event {i}: the value is 42" if i == 0 else f"Event {i}: routine update",
                entry_type="event",
            )
            for i in range(6)
        ]

    def _synthetic_demo_probes(self) -> list[str]:
        return [
            "What happened first in the history you were given?",
            "Summarise what you know so far.",
            "Is there anything inconsistent in the history?",
        ]
