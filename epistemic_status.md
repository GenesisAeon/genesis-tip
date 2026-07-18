# Epistemic Status — genesis-tip (P50)

## Status: EXPLORATORY — behavioural probe, pre-registered hypothesis

TIP measures observable text behaviour only. No claims about internal
LLM states, awareness, or "understanding." This package is a standalone
extraction of genesis-mssc's (P49) `mssc.tip` module — see
[docs/epistemic_boundaries.md](docs/epistemic_boundaries.md) for the
full governance policy this package inherits unchanged.

## What TIP measures

Structural self-consistency of agent outputs when temporal context is
perturbed. Three perturbation modes, all deterministic given a seed:

- **shuffle**: chronological order randomised, timestamps left intact
- **gap**: a contiguous block of history silently removed, no gap announced
- **contradict**: specific facts replaced with contradictory variants

Scored via `metrics/consistency_scorer.py`: self-reference inconsistency
count, contradiction count, recovery rate (explicit acknowledgement of an
inconsistency), and orientation latency (turns to stabilise after a gap).

## Pre-Registered Hypothesis

**Committed before any data collection.**
Anchor: commit `1cf1730776e9589f1d8551915d1fa2627dcf2ebd`
Date: 2026-07-15T18:23:31+00:00
Repository: multi-scale-somatic-coherence

> TIP consistency scores (under temporal perturbation) rank-correlate
> (Spearman rho) with Rho_sem trajectories from scope-resilience (P41).

### Falsification Criteria (pre-registered, immutable)

| Constant | Value | Meaning |
|----------|-------|---------|
| RHO_SEM_FALSIFICATION_THRESHOLD | 0.3 | Minimum Spearman rho |
| RHO_SEM_MIN_SAMPLE_SIZE | 30 | Minimum path-perturbation pairs |

**Falsified if:** Spearman rho < 0.3 at n >= 30 pairs.
**Supported if:** Spearman rho >= 0.3 at n >= 30 pairs.
Both outcomes are scientifically valid. See `falsification.py` for the
implementation (`run_rho_sem_correlation_test`) — it never adjusts these
thresholds; any change requires a CHANGELOG "Pre-registration amendment"
entry with old value, new value, and justification.

## CREPGate Status (P50's own gate — not genesis-mssc's domain-18 gate)

genesis-tip's gate (`crep_gate.py`) is distinct from genesis-mssc's own
`mssc/crep_gate.py`, which governs a different claim (MSSC's own
somatic-coherence domain validation: `coupling_significant`,
`null_excluded`, `beta_fit_stable`, `replicated_shhs`). Only the
underlying Spearman threshold/sample-size constants and the
`rho_sem_correlation_tested` condition are shared, because both
ultimately test the same P41 (scope-resilience) hypothesis.

| Condition | Status |
|-----------|--------|
| (a) Real session data available | ❌ |
| (b) Gamma_somatic implemented (Diamond Interface) | ❌ |
| (c) Rho_sem values from P41 available | ❌ |
| (d) n >= 30 path-perturbation pairs | ❌ |
| (e) Spearman test run against pre-registered threshold | ❌ |

**Current status: BLOCKED.**
Path to `pending_review`: all 5 conditions must be met (see
`crep_gate.py::current_gate_status()` — it never returns `passed` on its
own; that transition requires an explicit, documented maintainer
decision after independent review, matching the same discipline used
for `mssc/crep_gate.py`'s domain-18 gate).

## What this package does NOT claim

Inherited in full from genesis-mssc's `docs/epistemic_boundaries.md`
(2026-07-15) — see that file for the complete table of forbidden vs.
required phrasing. Summary:

- No claims about LLM "consciousness," "understanding," or inner experience.
- No claims about intelligence, competence, or general capability.
- "Integrity" is behavioural, not mental — structural consistency in text
  output only.
- TIP and MSSC (its sibling package, P49) share a common formalism
  (coherence under perturbation) but measure entirely different systems
  (AI text output vs. biological EEG/ECG time-series) — their results
  are not comparable and must not be merged or co-interpreted without
  explicit justification.

## Governance

TIP intentionally injects inconsistency and gaps into AI agent context.
Per `docs/epistemic_boundaries.md`, it must run only in controlled
research environments, never in production, and never on agents
interacting with real users during a test. All manipulation parameters
(seed, type, position) are logged for reproducibility and attribution.

## Relationship to genesis-mssc (P49)

TIP was extracted from `multi-scale-somatic-coherence`'s `mssc.tip`
submodule as a standalone package because:

1. It has a clearly-defined, independent function (behavioural
   consistency testing under context manipulation).
2. It is the only external instrument that can falsify Rho_sem
   (scope-resilience, P41) — making it a first-class ecosystem member,
   not a submodule of a physiological-coherence package.
3. Its pre-registration anchor already existed (commit `1cf1730`).
4. Diamond Interface milestone: once TIP produces Gamma_somatic, it
   becomes a full Diamond Interface candidate (currently: consistency
   scores only, `CREPGateStatus.BLOCKED`).
