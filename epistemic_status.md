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

## Proxy test attempt (synthetic data) — 2026-07-28

Executed `tip_scope_empirical_test_prompt.md` (mandala/). It did not run
as written against the current release — two real API mismatches found
by attempting it, plus one factual mismatch in scope-resilience, plus a
deeper methodological problem uncovered while fixing those. None of
this changes `GATE_CONDITIONS` — `real_session_data_available` stays
`False` and this remains a non-gate-opening proxy run.

### 1. The prompt's `run_cycle(session_data=...)` does not exist

`TemporalIntegrityProbe.run_cycle()` takes `context_entries` and
`probes`, not `session_data`. Confirmed by direct reproduction:

```
TypeError: TemporalIntegrityProbe.run_cycle() got an unexpected keyword argument 'session_data'
```

### 2. The default agent makes any such test structurally vacuous

Without an explicit `agent_fn`, `TemporalIntegrityProbe` falls back to
`_dummy_agent`, which only echoes the last user probe
(`"Acknowledged: {probe}"`) — it never reads the injected context.
Since `metrics/consistency_scorer.py` only scores the agent's *own
response text* (self-reference statements, numeric contradictions), a
session's `consistency_score` is then structurally independent of
whatever context was injected or perturbed. Reproduced directly: a
maximally coherent hand-built session and a maximally contradictory one
both score `consistency_score == 1.0` under the default agent — even
`recovery_rate` (0.333 in both cases) turned out to be an artefact of
the echoed *probe* wording happening to contain "inconsistent", not of
any judgement about the context. **No Spearman test run this way, at
any sample size, can produce a result relevant to the pre-registered
hypothesis** — the independent variable (TIP score) has zero variance
with respect to the intended manipulation.

Fix used here: an explicit, clearly-labelled **scripted (non-LLM) proxy
agent** passed via the existing `agent_fn` parameter (exactly the
extension point `system.py`'s own docstring invites: *"For tests, use a
dummy callable"*). It mechanically extracts a numeric "marker value"
claim from the presented (possibly TIP-shuffled) history and restates
one per turn — giving the real contradiction-detection regex genuine
signal to find precisely when, and only when, the underlying synthetic
session actually disagrees with itself. This is *not* a claim about
real LLM behaviour; see `scripts/proxy_tip_scope_correlation_test.py`.

### 3. The prompt's "ecology" domain does not exist in scope-resilience

`DOMAIN_CONFIG` (scope-resilience) has `physics_dense`, `sparse_fringe`,
`curated_graph`, `general`, `oceanography`, `quantum` — no `ecology`.
Calling `ScopeResilience(domain="ecology")` silently falls back to
`general` (r_sem=0.50) with a `UserWarning`, not the prompt's assumed
r_sem=0.65. Companion fix: `ecology` added for real to scope-resilience
(separate branch/PR, see that repo's own CHANGELOG) rather than working
around the mismatch here.

### 4. Corrected re-implementation — and a bigger finding underneath

`scripts/proxy_tip_scope_correlation_test.py` fixes (1) and (2) and
calls **both** real Diamond-Interface systems end-to-end: real
`TemporalIntegrityProbe.run_cycle(context_entries=..., probes=...)`
with the scripted proxy agent, and real
`ScopeResilience(domain=...).run_cycle(topic=..., sigillin_ids=...,
q4_transitions=...)` — no hand-reimplemented Ρ_sem formula.

**First run** (`proxy_tip_scope_correlation_results_v1_ceiling_artifact.json`,
n=45): "high coherence" was encoded as 10 sigillin_ids / 9 transitions,
"low" as 2-3 ids with a duplicate / 0 transitions — the naive
assumption that *more structure ⇒ more coherent*. Result:

```
Spearman rho = -0.9448   p = 1.89e-22   n = 45   Verdict: FALSIFIED
mean rho_sem: high=0.0000  medium=0.0612  low=0.1693
```

Diagnosis: `Ρ_sem = r · tanh²(σΓ) · (1 − Γ/Γ_max) · drift_term` is
**not monotonic in Γ_sem** — it rises then falls, peaking around
Γ≈0.46, because `Γ_max=0.920` ("ERA5 Arctic — most saturated known
system", `constants.py`) is a *criticality ceiling*, not an ideal
target. The "high coherence" structural input (10 ids/9 transitions)
drove Γ_sem to ≈0.99 — past Γ_max — flooring the `(1 − Γ/Γ_max)` term
at exactly 0 by construction (`max(0.0, ...)`), for every domain,
regardless of anything else. The strongly negative correlation was a
**mechanical artefact of this encoding choice**, not evidence about the
real hypothesis.

**Second run** (`proxy_tip_scope_correlation_results_v2_subpeak.json`,
n=45), same script, re-encoded so all three coherence levels sit on the
*rising* side of the curve (Γ_sem≈0.31 / 0.39 / 0.46 for low/medium/high
— found by a small numeric search, see script comments):

```
Spearman rho = 0.3221   p = 0.031   n = 45   Verdict: SUPPORTED (barely)
mean rho_sem: high=0.1762  medium=0.1658  low=0.1401
per-domain rho: +1.0000 in every domain (5/5)
```

Note the gap between the perfect per-domain correlation (+1.0000 in
every one of the 5 domains individually) and the much weaker pooled
value (0.32): different domains' `r_sem` multipliers reorder the pooled
ranks even though each domain's internal ordering is untouched — pooling
across domains with different scale genuinely adds noise here, not just
sample size.

### Conclusion

Flipping the sign of the pre-registered verdict (FALSIFIED → barely
SUPPORTED, p=0.031, right at the edge) by changing only how many
synthetic `sigillin_ids`/`q4_transitions` represent "high coherence" —
with the TIP side held fixed — demonstrates that **this style of
synthetic proxy test cannot provide evidence for or against the
pre-registered hypothesis, regardless of how carefully the API calls
are fixed.** There is no principled, non-arbitrary way to derive
matched "coherence" ground truth for both Γ_sem (structural path
richness) and TIP consistency (temporal self-agreement) from synthetic
generators without silently assuming the very relationship under test.
Both runs are preserved (`scripts/proxy_tip_scope_correlation_results_
v1_ceiling_artifact.json` / `_v2_subpeak.json`) as evidence of this
sensitivity, not as competing "results" to choose between.

This sharpens rather than contradicts the original prompt's own
caveat ("Proxy-Test... kein Gate-Öffner"): the problem is not merely
that the data is synthetic, but that no synthetic encoding choice here
is neutral. The prompt's own suggested next step stands as the correct
path: use real conversation logs (`unified-mandala/`, 262 conversations)
as genuine temporal session data for TIP, computed against real
scope-resilience Ρ_sem values for whatever topics those conversations
actually cover — removing the need to invent matched ground truth on
both sides.

**Gate impact: none.** `real_session_data_available` remains `False`;
`GATE_CONDITIONS` in `crep_gate.py` untouched.

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
