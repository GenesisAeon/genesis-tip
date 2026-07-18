# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
