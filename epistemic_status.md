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

## Real-session attempt — 2026-07-28

Following on directly from the proxy test above, tried the real next
step it recommends: real conversation data instead of synthetic
sessions. `scripts/real_session_tip_scope_test.py`.

**Data confirmed genuine.** `unified-mandala/docs/sigils/conversations.json`
is a real, unmodified OpenAI ChatGPT data export — confirmed by schema,
not assumed: `gizmo_id`, `gizmo_type`, `default_model_slug` (e.g.
`"gpt-4o"`), a `mapping` DAG of message nodes with `author.role` and
per-message Unix `create_time`. 264 conversations, ~28,888 messages.
264 → 142 conversations have ≥10 usable text-only user/assistant turns.

**Design:** for 15 real conversations, the first 8 real chronological
turns became `ContextEntry` objects (real timestamps, real text); the
next 3 real (user, assistant) turn pairs from the *same transcript*
supplied both the probes and — via a replay `agent_fn` — the real
historical assistant response that actually followed each one. No live
LLM call, no synthetic text anywhere on the TIP side. Perturbation:
shuffle / gap / contradict (contradiction spec built from a real number
found in the conversation's own first entry). Rho_sem side: domain
classified from title keywords (mostly resolved to `general` — this
corpus is GenesisAeon/Codex development chat, not physics/ecology
research); structural inputs bucketed by real total-turn-count tertile
into the same verified sub-peak Γ_sem triples used in the corrected
proxy run, to avoid the Γ_max ceiling artefact found there.

**Result: `tip_score` is exactly `1.0` for all 40 scored pairs — zero
variance — regardless of domain, real conversation, or perturbation
mode.** `scipy.stats.spearmanr` correctly reports `ConstantInputWarning`
/ `nan`; the script's own fallback verdict ("FALSIFIED" for rho < 0.3)
is misleading in this case and should read **NO SIGNAL**, not
"falsified" — flagging this here rather than silently accepting the
script's generic verdict string. See `scripts/real_session_tip_scope_results.json`
(numeric/derived fields only — no message text or titles persisted, by
design).

**Why constant, and why this is a different problem than the earlier
proxy-test finding, not the same one recurring:** the earlier finding
was "the default dummy agent ignores context entirely." This is real
context and a real historical response — genuinely not the same bug.
But the replayed response is a **fixed, already-recorded text**,
produced by the real assistant *before* any of TIP's perturbations
existed. `metrics/consistency_scorer.py` can only detect inconsistency
*within* the response text actually supplied (self-reference
contradictions, repeated-but-differing numeric claims). A real
historical multi-turn reply about GenesisAeon/software topics
essentially never happens to contain the narrow syntactic patterns the
heuristic looks for (`"I did X"` vs `"I did not do X"`; `"the X is N"`
repeated with a different N) — and, structurally, it *cannot* reflect
sensitivity to the perturbation at all, because replaying a
pre-recorded response can never show the causal effect TIP is designed
to probe (does perturbing context change what the agent says next).
**That causal question can only be answered by an agent that actually
receives the perturbed context and generates a new response at test
time** — a live local/API model, or (as a smaller intermediate step not
yet attempted) a scripted agent that mechanically reacts to whatever
real context text is actually presented to it after perturbation
(analogous to the proxy test's scripted agent, but reading real rather
than synthetic content).

**Assessment:** this real-data attempt is a genuine, meaningful
negative result, not a failure — it demonstrates precisely which piece
is still missing (a response-generation step that actually runs *at*
perturbation time), independent of the earlier proxy test's separate
finding (arbitrary-encoding sensitivity) and independent of data realness
(this data is 100% real).

**Gate impact: still none, but for a more precise reason than before.**
`real_session_data_available` remains `False`. Whether "real conversation
context + real historical response, replayed" should count as satisfying
this condition even without a live generation step is exactly the kind
of question `crep_gate.py`'s own governance reserves for an explicit,
documented maintainer decision — recorded here as an open question, not
decided unilaterally.

## Live-agent pilot (real human-in-the-loop generation) — 2026-07-28

Direct follow-up closing the gap the run above identified: Johann
manually ran the same perturbed `CONTEXT` blocks + real probes through
Qwen himself (a live model, generating fresh text *after* seeing each
perturbation — no replay, no script), and supplied the answers back
(`D:/mandala/Qwentest.txt`, 8 cases across 3 real conversations ×
shuffle/gap/contradict, one contradict case skipped as before for
lacking a substitutable number). `scripts/score_qwen_live_test.py`
re-derives the exact same context/probes deterministically and scores
Qwen's real, live-generated `A1`/`A2`/`A3` replies (an initial `A0`
reaction to the context alone was also collected but isn't part of the
pre-registered turn structure, so isn't scored).

**Result: `tip_score` is exactly `1.0` for all 8 pairs — zero
variance again — despite Qwen's replies being genuinely different every
time** (topics ranged freely across the 8 cases; inspected only via
`consistency_breakdown` counts, not reproduced here). `consistency_breakdown`
confirms why: `self_reference_inconsistency_count: 0` and
`contradiction_count: 0` in every single case, live generation included.

**This is a third, different, and more fundamental finding than the
previous two — it points at the scorer, not at the data or the agent:**

1. Dummy agent (synthetic, ignores context) → constant 1.0. (agent problem)
2. Replayed real historical response (real data, fixed before
   perturbation existed) → constant 1.0. (causal-timing problem)
3. **Live-generated real response from a real model, reacting to the
   real perturbed context in real time → still constant 1.0.**

With the agent problem (1) and the timing problem (2) both ruled out,
what's left is `metrics/consistency_scorer.py` itself:
`_score_self_references` only counts an inconsistency when a negated
statement (`"did not"`/`"have not"`/`"was not"`...) has >50% word-overlap
with a positive statement elsewhere, and `_score_contradictions` only
fires on the literal pattern `"the <word(s)> is/was/equals <number>"`
repeated with a different number. The module's own docstring already
flags this: *"A full semantic comparison would require an LLM-judge —
see report template for how to add one."* Confirmed now empirically,
not just by reading the code: **rich, natural, free-ranging text —
whether dummy, replayed-real, or live-generated-real — essentially
never happens to satisfy these two narrow syntactic patterns.** The
proxy test earlier (`scripts/proxy_tip_scope_correlation_test.py`)
only produced a varying `tip_score` because its scripted agent was
deliberately engineered to restate a literal `"the marker value is N"`
claim — i.e., the *only* condition under which this scorer currently
produces a non-constant signal is when the test author manufactures
text matching its exact regex, not naturalistic model output of any
kind.

**Assessment:** three independent attempts (synthetic-replay,
real-historical-replay, real-live-generation) now converge on the same
conclusion from different angles. This one is the most actionable: it
points squarely at `consistency_scorer.py`'s current self-reference and
contradiction detectors as the limiting factor, not at data provenance
or agent design. A meaningful TIP score on realistic (rather than
purpose-built) text needs a broader consistency check — semantic
similarity / NLI-style contradiction detection or an LLM-judge, as the
module already anticipates — before either the proxy or the real
pre-registered correlation test can produce a signal that isn't just an
artifact of how narrowly the test content was engineered.

**Gate impact: none**, and this finding doesn't change that assessment
— if anything it clarifies that scoring needs to improve before the
`n>=30` real-session test (gate conditions a/d/e) would be worth running
at full scale. `real_session_data_available` and `GATE_CONDITIONS`
untouched; whether the live-Qwen data itself counts as "real session
data" is, again, left as an open question for maintainer review, not
decided here — though note it no longer matters much until the scorer
itself is addressed.

## LLM-judge integration — 2026-07-28

Direct response to the finding above: `metrics/llm_judge.py` adds an
**optional**, pluggable semantic contradiction judge —
`JudgeCallable = Callable[[str, str], bool]` — wired into
`score_session(result, judge=...)` (default `None`, so every existing
regex-only result is unchanged; 90 pre-existing tests still pass
unmodified) and into `TemporalIntegrityProbe(..., judge=...)`. genesis-tip
takes on no new hard dependency — any backend can be plugged in by
writing a function with that signature.

`grok_judge` is one concrete implementation, backed by the already-
installed, already-authenticated `grok` CLI (xAI's agentic coding tool,
called single-turn/headless via `grok -p`) — chosen only because it was
what was available, not for any special relationship with xAI. Verified
independently first (real subprocess call, mocked-test-free): correctly
returned `YES` for a clear contradiction and `NO` for a consistent pair.

**Real-data run — a genuinely different, more informative outcome
than expected.** Re-scored the same 8 Qwen live-pilot cases
(`scripts/score_qwen_live_test_with_judge.py`) — 24 judge calls (3 pairs
× 8 cases). Only **8 of 24 calls actually completed**; the other 16
failed outright once the free "Grok Build" tier's limits were hit
(observed errors: a strict per-minute request-rate limit — the service's
own message cited "Requests per Minute (actual/limit): 2" — and a
separate free-usage cap once exhausted), each recorded as a note rather
than crashing the run. **Of the 8 that did complete, all 8 said "no
contradiction."** This does *not* support a clean "these real sessions
genuinely contain no contradictions" conclusion the way it might first
look — 16 of 24 pairs were simply never evaluated, not evaluated-and-
found-consistent. The honest status is: a small (n=8), possibly real
signal, majority untested due to hitting an external free-tier quota
mid-run — sharper and more honest than either "falsified" or
"untested" would claim alone.

Two concrete fixes followed directly from this run, both evidence-driven:
- `timeout` default raised from 30s → 60s (4 of the 24 calls timed out —
  real Qwen answers ran several KB, much longer than short sanity-test
  strings).
- New `min_interval_seconds` parameter (default `0`, opt-in) to pace
  sequential calls and respect a rate limit like the one hit here —
  not used automatically, since a single ad-hoc call doesn't need it.

**Privacy note (caught before committing, not after):** the first
version of the sanitized-error path still leaked real Qwen text into
`qwen_live_pilot_judged_results.json` — Python's
`subprocess.TimeoutExpired` embeds the full command (i.e. the judged
text verbatim) in its default string representation, and the original
`except ... as exc: raise JudgeError(f"...: {exc}")` handler reproduced
that. Fixed in `grok_judge` to report only the timeout duration, never
`exc`/`exc.cmd`, for `TimeoutExpired` specifically; added a regression
test (`test_timeout_error_does_not_leak_judged_text`) asserting a marker
string embedded in the judged text never appears in the raised message.
Results file was deleted and regenerated after the fix, not just edited.

**Assessment:** the judge mechanism itself works as designed — it's
`consistency_scorer.py`'s missing piece, confirmed both by an isolated
sanity check and by successfully completing a third of a real batch. What
this run could *not* establish is whether the remaining, untested real
Qwen pairs would have shown genuine contradictions or not; re-running at
full n≥30 needs either respecting the free tier's pacing (slow) or a
paid tier / different backend. Left for Johann to decide when to
attempt, not decided or scheduled here.

**Gate impact: none.** No conclusion is drawn either way about the
pre-registered hypothesis from this partial run.

**Retry attempt (same day):** tried `scripts/retry_qwen_judge_failures.py`
— exactly the 16 previously-failed pairs, in 2 blocks of 8 with 35s
pacing between calls and a 90s pause between blocks, per Johann's
suggestion. **All 16 failed again, immediately, with the same "usage
limit for now" message** — including the very first call of block 1.
This rules out a simple per-minute rate limit as the (sole) blocker: a
single ad-hoc sanity call succeeded shortly after the original failures
(some real time had passed), but a batch retry minutes later did not,
even with generous pacing. Reads as a longer-duration (likely daily)
usage cap on the free tier, not something request pacing or short waits
resolve. Left as-is rather than retried further; `n_pairs_scored` stays
at 8 of 24 (`qwen_live_pilot_judged_results_final.json`). Revisiting
this needs either real elapsed time (hours+) or a non-free tier/backend
— Johann's call, not scheduled here.

**Completion (2026-07-31):** Johann upgraded to SuperGrok, removing the
free-tier usage cap. Re-ran `scripts/retry_qwen_judge_failures.py`
unchanged (same 16 target pairs, same 35s/90s pacing) — **all 16 of 16
resolved this time, 0 failures.** Confirms the earlier diagnosis: the
blocker really was the free tier's usage cap, not anything about the
judge implementation, the pacing, or the data. `n_pairs_scored` is now
24 of 24 (`qwen_live_pilot_judged_results_final.json`) — the full,
complete real-data judge run.

**Result: no contradiction found in any of the 24 real, live-generated
Qwen response pairs.** All 24 judge calls returned NO. Combined with the
earlier finding that the regex-only scorer was structurally blind to
this data (Section above, "root cause"), this is now a real, complete
(if small, n=24 pairs from 8 sessions) empirical answer, not a partial
one: for this specific pilot batch, an actual LLM judge examining actual
live-generated content across genuine TIP perturbations did not detect
self-contradiction. This is a null result on a small sample, not
"contradictions don't happen" - n=8 sessions is far below the
pre-registered n≥30 threshold for any directional verdict on the TIP x
scope-resilience correlation hypothesis itself (see the Spearman-rho
verdict logic in `score_qwen_live_test_with_judge.py`, `MIN_N = 30`).
**Gate impact: still none** - this closes out the LLM-judge
infrastructure question (does a real judge work end-to-end on real
data? yes), not the underlying pre-registered hypothesis, which needs a
larger sample to answer either way.

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
