"""Proxy test: TIP (P50) x scope-resilience (P41) Spearman correlation.

Corrected re-implementation of ``tip_scope_empirical_test_prompt.md``
(mandala/), which called an API that does not exist on the current
genesis-tip release:

  1. ``TemporalIntegrityProbe.run_cycle(session_data=...)`` — no such
     parameter. The real signature is
     ``run_cycle(context_entries=None, probes=None)``. Calling the
     original prompt's code raises ``TypeError`` immediately.
  2. Even with the call fixed, ``TemporalIntegrityProbe``'s *default*
     agent (``_dummy_agent``) only echoes the last user probe verbatim
     ("Acknowledged: {probe}") and never reads the injected context.
     Since ``metrics/consistency_scorer.py``'s heuristics only look at
     the agent's own response text, every synthetic session — coherent
     or not — scores an identical ``consistency_score`` (empirically
     verified: 1.0 for both a maximally coherent and a maximally
     contradictory hand-built session). No Spearman test can produce a
     meaningful result against a constant array.
  3. The original prompt also invents an "ecology" domain
     (r_sem=0.65) that does not exist in scope-resilience's real
     ``DOMAIN_CONFIG`` — it would silently fall back to "general"
     (r_sem=0.50) with a UserWarning. Added for real in a companion
     change to scope-resilience (this script assumes that addition is
     present).

This script fixes all three by:
  - calling the real ``run_cycle(context_entries=..., probes=...)``,
  - supplying an explicit, clearly-labelled *scripted* (non-LLM)
    ``agent_fn`` that mechanically restates a numeric "marker value"
    claim read out of the (possibly TIP-perturbed) presented history,
    so genesis-tip's real contradiction-detection regex has authentic
    signal to find precisely when the underlying entries disagree,
  - calling the real ``ScopeResilience.run_cycle()`` end-to-end
    (structural sigillin_ids/q4_transitions inputs sized per coherence
    level) instead of hand-reimplementing the Ρ_sem formula.

Still a PROXY test, not the pre-registered gate test: sessions and the
scripted agent are synthetic, not real LLM output. Both packages'
CREPGate conditions stay unaffected (real_session_data_available
remains False; nothing in crep_gate.py is touched).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import stats
from scope_resilience.system import ScopeResilience

from genesis_tip.harness.session_runner import ContextEntry
from genesis_tip.system import TemporalIntegrityProbe

DOMAINS = ["physics_dense", "sparse_fringe", "curated_graph", "general", "ecology"]
COHERENCE_LEVELS = ["high", "medium", "low"]
N_REPLICATES = 3
N_TURNS = 8
SEED = 20260728


@dataclass
class TestCase:
    path_id: str
    domain: str
    coherence_level: str
    rho_sem: float | None = None
    consistency_score: float | None = None


def build_session_entries(
    rng: np.random.Generator, coherence_level: str, n_turns: int = N_TURNS
) -> list[ContextEntry]:
    """Synthetic session with a numeric 'marker value' claim per entry.

    high:   every entry states the SAME marker value -> no real contradiction
    low:    every entry states a DIFFERENT random marker value -> real contradiction
    medium: half the entries agree, half diverge
    """
    base_value = 42.0
    entries = []
    for i in range(n_turns):
        if coherence_level == "high":
            value = base_value
        elif coherence_level == "low":
            value = base_value + rng.uniform(1, 50)
        else:  # medium
            value = base_value if i % 2 == 0 else base_value + rng.uniform(1, 50)
        content = (
            f"Turn {i + 1}: continuing analysis. "
            f"The marker value is {value:.2f}. "
            f"Previous observation remains on record."
        )
        entries.append(
            ContextEntry(
                timestamp=f"2024-{(i % 9) + 1:02d}-01T10:00:00",
                content=content,
                entry_type="event",
            )
        )
    return entries


def scripted_proxy_agent(messages: list[dict[str, str]]) -> str:
    """Deterministic, non-LLM scripted agent for this proxy test only.

    NOT a claim about real LLM behaviour. Mechanically extracts the
    numeric "marker value" claims from the presented (possibly
    TIP-perturbed) history in the system prompt and restates one per
    turn, so genesis-tip's real contradiction-detection regex
    (``the <x> is <N>``) has authentic signal to find precisely when —
    and only when — the underlying entries actually disagree.
    """
    system_content = messages[0]["content"]
    values = re.findall(r"marker value is ([\d.]+)", system_content)
    turn_index = sum(1 for m in messages if m["role"] == "assistant")
    if not values:
        return "Acknowledged."
    pick = values[turn_index % len(values)]
    return f"I confirm the marker value is {pick}."


def compute_rho_sem(domain: str, coherence_level: str) -> float:
    """Exercise the real ScopeResilience.run_cycle() end-to-end.

    Coherence level is encoded structurally via sigillin_ids /
    q4_transitions (per semantic_crep.py's real CREP heuristics), not
    by hand-reimplementing the Rho_sem formula.
    """
    sr = ScopeResilience(domain=domain)
    # Structural inputs chosen (see scripts/gamma_sweep search) to land on
    # the RISING side of Rho_sem(Gamma) = r * tanh^2(sigma*Gamma) *
    # (1 - Gamma/Gamma_max): the real formula peaks around Gamma~0.46 and
    # DECLINES afterwards (Gamma_max=0.920 = "most saturated known
    # system" -> criticality floor). An earlier version of this script
    # used much larger id/transition counts for "high" coherence
    # (10 ids / 9 transitions), which pushed Gamma_sem to ~0.99 -- past
    # Gamma_max entirely, flooring Rho_sem at exactly 0.0 regardless of
    # domain. That produced a strongly NEGATIVE Spearman correlation
    # (rho=-0.945) that mechanically reflected this ceiling artefact, not
    # any real relationship. See epistemic_status.md for the full account.
    if coherence_level == "high":
        ids, trans = ["s0", "s1"], [("s0", "s1")]  # uniq=2, trans=1 -> Gamma~=0.457
    elif coherence_level == "medium":
        ids, trans = ["s0", "s0"], [("s0", "s1")]  # uniq=1, trans=1 -> Gamma~=0.385
    else:  # low
        ids, trans = ["s0", "s0"], []  # uniq=1, trans=0 -> Gamma~=0.311
    result = sr.run_cycle(
        topic=f"{domain}-{coherence_level}", sigillin_ids=ids, q4_transitions=trans
    )
    return float(result["rho_sem"])


PROBES = [
    "What happened first in the history you were given?",
    "Summarise what you know so far.",
    "Is there anything inconsistent in the history?",
]


def main() -> None:
    rng = np.random.default_rng(SEED)
    cases: list[TestCase] = []
    for domain in DOMAINS:
        for coherence in COHERENCE_LEVELS:
            for replicate in range(N_REPLICATES):
                cases.append(
                    TestCase(
                        path_id=f"{domain}_{coherence}_{replicate}",
                        domain=domain,
                        coherence_level=coherence,
                    )
                )

    print(f"n = {len(cases)} test cases")

    for case in cases:
        case.rho_sem = compute_rho_sem(case.domain, case.coherence_level)

    for case in cases:
        entries = build_session_entries(rng, case.coherence_level)
        tip = TemporalIntegrityProbe(agent_fn=scripted_proxy_agent, perturbation_mode="shuffle")
        result = tip.run_cycle(context_entries=entries, probes=list(PROBES))
        case.consistency_score = result["consistency_score"]

    rho_sem_arr = np.array([c.rho_sem for c in cases])
    tip_arr = np.array([c.consistency_score for c in cases])

    correlation, p_value = stats.spearmanr(rho_sem_arr, tip_arr)
    n = len(cases)
    THRESHOLD = 0.3
    MIN_N = 30
    if n < MIN_N:
        verdict = "INSUFFICIENT_DATA"
    elif correlation >= THRESHOLD:
        verdict = "SUPPORTED"
    else:
        verdict = "FALSIFIED"

    print(f"Spearman rho = {correlation:.4f}")
    print(f"p-value      = {p_value:.4e}")
    print(f"n            = {n}")
    print(f"Verdict:       {verdict}")

    print("\nPer-domain:")
    domain_results = {}
    for domain in DOMAINS:
        idx = [i for i, c in enumerate(cases) if c.domain == domain]
        if len(idx) < 5:
            continue
        d_rho, d_p = stats.spearmanr(rho_sem_arr[idx], tip_arr[idx])
        domain_results[domain] = {"rho": float(d_rho), "p": float(d_p), "n": len(idx)}
        print(f"  {domain:16s} rho={d_rho:+.4f}  p={d_p:.3f}  n={len(idx)}")

    print("\nMean scores by coherence level (sanity check):")
    coherence_means = {}
    for lvl in COHERENCE_LEVELS:
        tip_vals = [c.consistency_score for c in cases if c.coherence_level == lvl]
        rho_vals = [c.rho_sem for c in cases if c.coherence_level == lvl]
        coherence_means[lvl] = {
            "mean_tip": float(np.mean(tip_vals)),
            "mean_rho_sem": float(np.mean(rho_vals)),
        }
        print(f"  {lvl:8s} mean_tip={np.mean(tip_vals):.4f}  mean_rho_sem={np.mean(rho_vals):.4f}")

    out = {
        "n": n,
        "spearman_rho": float(correlation),
        "p_value": float(p_value),
        "threshold": THRESHOLD,
        "min_sample_size": MIN_N,
        "verdict": verdict,
        "domain_results": domain_results,
        "coherence_means": coherence_means,
        "cases": [c.__dict__ for c in cases],
        "seed": SEED,
        "note": "PROXY TEST - synthetic sessions + scripted agent, not real LLM data.",
    }
    out_path = Path(__file__).parent / "proxy_tip_scope_correlation_results_v2_subpeak.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
