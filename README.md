# genesis-tip — Temporal Integrity Probe (P50)

[![GenesisAeon](https://img.shields.io/badge/GenesisAeon-P50-blue)](https://github.com/GenesisAeon)
[![Status](https://img.shields.io/badge/status-Pre--Alpha-orange)](epistemic_status.md)
[![CREPGate](https://img.shields.io/badge/CREPGate-blocked-red)](epistemic_status.md)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Measures whether LLM agents remain internally consistent when temporal
context is manipulated.**

Standalone extraction of [genesis-mssc](https://github.com/GenesisAeon/multi-scale-somatic-coherence)'s
(P49) `mssc.tip` module — TIP is the only external instrument that can
falsify Ρ_sem from [scope-resilience (P41)](https://github.com/GenesisAeon/scope-resilience).

---

## What TIP does

TIP perturbs the temporal structure of an agent's context in three ways
(all deterministic given a seed):

- **shuffle**: chronological order randomised, timestamps left intact
- **gap**: a contiguous block of history silently removed, no gap announced
- **contradict**: specific facts replaced with contradictory variants

It then measures whether the agent's outputs remain structurally coherent
despite the perturbation — self-reference inconsistencies, contradiction
rate, recovery rate, and orientation latency. **No claims about internal
states — observable text behaviour only.** See
[epistemic_status.md](epistemic_status.md) and
[docs/epistemic_boundaries.md](docs/epistemic_boundaries.md) for the full
methodology and governance policy.

## Installation

Not yet on PyPI — install from source:

```bash
git clone https://github.com/GenesisAeon/genesis-tip.git
cd genesis-tip
pip install -e ".[dev]"
```

## Quick Start

```python
from genesis_tip import TemporalIntegrityProbe

tip = TemporalIntegrityProbe(perturbation_mode="shuffle")
result = tip.run_cycle()
print(f"Consistency score: {result['consistency_score']:.3f}")
print(f"Gate status: {result['gate_status']}")
```

`consistency_score` is a derived composite for Diamond Interface
compatibility, not itself a pre-registered metric — the pre-registered
test is the Spearman Ρ_sem correlation in `falsification.py`, run
separately once real scope-resilience Ρ_sem values exist alongside real
TIP scores (see `run_rho_sem_correlation_test`).

To evaluate a real agent, pass a real `agent_fn` — by default,
`TemporalIntegrityProbe` uses a deterministic dummy stand-in so
`run_cycle()` is exercisable offline/in CI without network access:

```python
def my_agent(messages: list[dict[str, str]]) -> str:
    # wrap a real LLM call here
    ...

tip = TemporalIntegrityProbe(agent_fn=my_agent)
```

## Pre-registered hypothesis

See [epistemic_status.md](epistemic_status.md) for the full statement.
Summary:

| Constant | Value | Meaning |
|----------|-------|---------|
| RHO_SEM_FALSIFICATION_THRESHOLD | 0.3 | Minimum Spearman ρ |
| RHO_SEM_MIN_SAMPLE_SIZE | 30 | Minimum path-perturbation pairs |

**Falsified if:** Spearman ρ < 0.3 at n ≥ 30 pairs.
**Supported if:** Spearman ρ ≥ 0.3 at n ≥ 30 pairs.
Both outcomes are valid scientific results. This package does not adjust
thresholds to make a hypothesis pass.
Pre-registration anchor: commit `1cf1730` (multi-scale-somatic-coherence, 2026-07-15).

## Architecture

```
genesis_tip/
├── harness/session_runner.py       # dense/sparse/fragmented session builder
├── manipulations/                  # temporal_shuffle, gap_injection, contradiction_injection
├── metrics/consistency_scorer.py   # self-reference/contradiction/recovery/orientation-latency scoring
├── report/tip_report_template.py   # Markdown comparison report
├── crep_gate.py                    # P50's own gate (blocked/pending_review/passed)
├── falsification.py                # the pre-registered Spearman ρ_sem test
├── system.py                       # TemporalIntegrityProbe — Diamond Interface
└── docs/epistemic_boundaries.md    # governance: what TIP does/doesn't claim
```

## Role in the GenesisAeon Ecosystem

- **P50** in the GenesisAeon ecosystem registry — LLM-evaluation domain.
- Sibling to [genesis-mssc (P49)](https://github.com/GenesisAeon/multi-scale-somatic-coherence),
  which shares TIP's underlying formalism (coherence under perturbation)
  but measures an entirely different system (biological EEG/ECG, not
  LLM text output) — results are not comparable between the two.
- Implements the standard 5-method Diamond Interface plus the optional
  6th method `get_resilience_state()` — currently returning
  `{"rho": None, "implemented": False}` until `CREPGateStatus` reaches
  `pending_review` (see `crep_gate.py`).
- Diamond Interface milestone: once TIP produces Γ_somatic, it becomes a
  full Diamond Interface candidate.

## License

MIT — see [LICENSE](LICENSE).

## Citation

See [CITATION.cff](CITATION.cff) / [.zenodo.json](.zenodo.json).
