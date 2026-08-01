# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-08-01

### Added
- `scripts/proxy_tip_scope_correlation_test.py`: corrected re-implementation
  of `tip_scope_empirical_test_prompt.md`'s proxy Spearman-correlation test
  against scope-resilience (P41), calling the real
  `TemporalIntegrityProbe.run_cycle(context_entries=..., probes=...)` and
  `ScopeResilience(...).run_cycle(...)` APIs end-to-end with an explicit,
  clearly-labelled scripted (non-LLM) proxy `agent_fn`. See
  `epistemic_status.md` ("Proxy test attempt (synthetic data) — 2026-07-28")
  for the full account, including two real API mismatches found in the
  original prompt and a methodological finding that no synthetic-data
  encoding of this test is neutral (flipping one structural assumption
  flips the pre-registered verdict from FALSIFIED to barely SUPPORTED).
  Does not affect `GATE_CONDITIONS` — `real_session_data_available` stays
  `False`.
- `scripts/real_session_tip_scope_test.py`: follow-up using real data —
  `unified-mandala/docs/sigils/conversations.json`, a confirmed genuine
  OpenAI ChatGPT export (264 conversations, ~28,888 messages). Real
  context entries, real probes, and a replay `agent_fn` returning the
  real historical assistant response, run through shuffle/gap/contradict.
  Result: `tip_score` is exactly `1.0` for all 40 scored pairs (zero
  variance) — not because the pipeline is broken, but because a replayed
  pre-recorded response structurally cannot reflect sensitivity to a
  perturbation that didn't exist when it was generated. See
  `epistemic_status.md` ("Real-session attempt — 2026-07-28") for the
  full account. Does not affect `GATE_CONDITIONS`.
- `scripts/score_qwen_live_test.py`: closes the gap identified above with
  a genuine live-agent pilot — Johann manually ran the same perturbed
  real context + real probes through Qwen (a live model) and supplied
  the answers (`D:/mandala/Qwentest.txt`, 8 cases). Result: `tip_score`
  is still exactly `1.0` for all 8 pairs, live generation included. This
  is a third, more fundamental finding: with the agent-ignores-context
  problem and the replay-timing problem both ruled out, the remaining
  cause is `metrics/consistency_scorer.py`'s narrow regex-based
  self-reference/contradiction detectors, which essentially never fire
  on naturalistic text of any kind (dummy, replayed, or live) — only on
  text deliberately engineered to match their exact patterns (as the
  earlier proxy test's scripted agent did). See `epistemic_status.md`
  ("Live-agent pilot — 2026-07-28"). Does not affect `GATE_CONDITIONS`.
- `src/genesis_tip/metrics/llm_judge.py`: optional, pluggable semantic
  contradiction judge (`JudgeCallable`) closing the gap identified above.
  Wired into `score_session(result, judge=...)` and
  `TemporalIntegrityProbe(..., judge=...)`, both defaulting to `None` —
  no behaviour change for existing callers, no new hard dependency.
  `grok_judge` is a concrete implementation backed by the `grok` CLI.
  Real-data re-run of the 8-case Qwen batch: only 8 of 24 calls actually
  completed (the rest hit the free "Grok Build" tier's rate/usage
  limits, recorded as notes, not crashes) — of those 8, none found a
  contradiction; the other 16 pairs are untested, not "tested and
  found consistent." `timeout` default raised 30s→60s (real answers
  are much longer than sanity-test strings); new opt-in
  `min_interval_seconds` param to pace future batches against a rate
  limit like the one hit here. A privacy issue was caught and fixed
  before commit: `subprocess.TimeoutExpired`'s default string embeds
  the full command (i.e. judged text) — `grok_judge` no longer
  reproduces it in `JudgeError` messages; regression test added. See
  `epistemic_status.md` ("LLM-judge integration — 2026-07-28"). Does
  not affect `GATE_CONDITIONS`.

## [0.1.1] - 2026-07-18

### Fixed
- CI: added the missing `docs` optional-dependency extra
  (`mkdocs`/`mkdocs-material`) to `pyproject.toml` — the `Docs (mkdocs
  --strict)` CI job installed `.[dev,docs]`, but the `docs` extra didn't
  exist, so `mkdocs` was silently never installed (`pip` doesn't error
  on an unknown extra name) and the build step failed with "command not
  found". Found by checking the real CI run for `v0.1.0`, not assuming
  local `pytest`+`ruff` success meant the whole pipeline was clean.
- `mypy src` (part of the same CI run's `Lint` job, also red): fixed 2
  real type errors — a bare `dict` return-type annotation missing its
  type parameters in `falsification.py`, and a missing return-type
  annotation on `system.py`'s `_build_manipulator` helper.
- Supersedes `v0.1.0` (CI red on both the `Lint` and `Docs` jobs; not
  removed/force-moved, left in history — no code/API change relative to
  it besides these two CI-only fixes).

## [0.1.0] - 2026-07-18

### Added
- Initial release as a standalone package (extracted from
  `genesis-mssc`/`mssc.tip`, P49 → P50).
- Real TIP implementation ported from `mssc.tip`, not reimplemented as a
  placeholder: `harness/session_runner.py` (dense/sparse/fragmented
  session builder), `manipulations/` (`temporal_shuffle`, `gap_injection`,
  `contradiction_injection`, all deterministic given a seed),
  `metrics/consistency_scorer.py` (self-reference inconsistency,
  contradiction rate, recovery rate, orientation latency),
  `report/tip_report_template.py` (Markdown comparison report), and
  `docs/epistemic_boundaries.md` (governance policy, carried over
  unchanged).
- `TemporalIntegrityProbe`: Diamond Interface main class
  (`run_cycle`, `get_crep_state`, `get_utac_state`, `get_phase_events`,
  `to_zenodo_record`, plus the optional 6th method
  `get_resilience_state()`) wired to the real harness/manipulation/
  scoring modules above, with a deterministic dummy agent as the default
  for offline/CI-safe testing.
- `crep_gate.py`: P50's own `CREPGateStatus` gate (blocked /
  pending_review / passed) with the 5 pre-registered gate conditions —
  distinct from `genesis-mssc`'s own domain-18 gate (different
  conditions; both share only the Ρ_sem threshold/sample-size constants
  and the `rho_sem_correlation_tested` condition).
- `falsification.py`: `run_rho_sem_correlation_test()` — the actual
  pre-registered Spearman rank-correlation implementation (using
  `scipy.stats.spearmanr`), distinguishing `supported` / `falsified` /
  `insufficient_sample` verdicts. Not present in `mssc.tip` itself; the
  pre-registration anchor (commit `1cf1730`) fixed the threshold and
  sample size but the correlation test itself had not yet been
  implemented anywhere.
- `epistemic_status.md`: full pre-registered hypothesis, gate-condition
  table, and epistemic-boundaries summary.
- 77 tests (including the ported real `mssc.tip` test suites for
  manipulations and consistency scoring), all passing; `ruff` clean.

### Fixed (relative to the diamond-setup scaffold this repo started from)
- Removed the vendored `diamond_setup` copy from `src/` — declares
  `diamond-setup>=2.2.0` as a real dependency instead.
- Removed dead scaffold tests (`test_cli.py`, `test_preset.py`,
  `test_protocol.py`, `test_validator.py`) referencing `diamond_setup`
  directly; kept `test_runtime_contract.py` (tests this repo's own
  `contracts/runtime.schema.yaml`, a legitimate scaffold feature).
- Rewrote `README.md`, `README_QUICKSTART.md`, `RELEASE_GUIDE.md`,
  `mkdocs.yml`, `docs/index.md`; removed `docs/cli.md`/`docs/templates.md`
  (about the `diamond` CLI itself, irrelevant here — this package has no
  CLI).

### Status
- `CREPGateStatus`: BLOCKED (Γ_somatic not yet implemented; 0/5 gate
  conditions met).
- Diamond Interface: implemented but gated — `get_crep_state()` returns
  `Gamma: None` until gate condition (b); `get_resilience_state()`
  returns `{"rho": None, "implemented": False}`.
- PyPI: not yet published — pending real session data (gate condition a)
  and Γ_somatic implementation (gate condition b).
