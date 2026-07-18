# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.2.0] - 2026-07-16
### Added
- `ResilienceState` Pydantic model — canonical Ρ snapshot (`rho`, `lambda_star`,
  `recovery_time`, `criticality_margin`, `coupling_load`, `near_collapse`).
- `DiamondPackage.get_resilience_state()` — optional sixth Diamond method.
  Default implementation returns `{"rho": None, "implemented": False}`;
  packages built on `resilience-core` override it (see `resilience-core`
  P40 and `scope-resilience` P41).
- `NotInitializedError` — alias for `NotConvergedError`, used in
  GenesisAeon P40/P41 documentation.
- `.github/workflows/diamond-validation.yml` — Diamond Protocol self-check
  CI job, running on every push/PR to validate protocol conformance.

## [2.1.0] - 2026-07-01
### Added
- `diamond_setup.protocol.DiamondPackage` — canonical ABC for the five-method
  Diamond interface (`run_cycle`, `get_crep_state`, `get_utac_state`,
  `get_phase_events`, `to_zenodo_record`).
- Pydantic models: `CREPState`, `UTACState`, `ZenodoRecord`.
- `NotConvergedError` — Γ/UTAC reads before first `run_cycle()` are rejected
  (Gamma is an attractor property, not an initial value).
- `diamond_setup.validation.validate_diamond_instance` for CI/schema checks.
- `contracts/diamond.interface.yaml` — machine-readable contract spec.

## [2.0.0] - 2026
### Changed
- Re-tagged ecosystem milestone release as v2.0.0 — the v1.0.0 tag in
  this repo's history predates the GenesisAeon ecosystem-wide milestone
  (a prior scaffold-template release) and was not available for reuse.
  v2.0.0 is the correct, free major version for this milestone and is
  functionally a continuation of the v1.0.0 release below.

## [1.0.0] - 2026
### Added
- Initial v1.0.0 release as part of the GenesisAeon ecosystem-wide 1.0.0
  milestone.
- `diamond` CLI: `scaffold`, `list-templates`, and `validate` commands.
- `minimal` and `genesis` project templates.
- Standardized release tooling: `.zenodo.json`, `RELEASE_GUIDE.md`,
  `CONTRIBUTING.md`, issue/PR templates.

### Changed
- Project metadata (`pyproject.toml`) normalized: description encoding
  fixed, license, authors, and `requires-python` confirmed present.
