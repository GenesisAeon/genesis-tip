# genesis-tip — Temporal Integrity Probe (P50)

**Measures whether LLM agents remain internally consistent when temporal
context is manipulated.**

TIP perturbs the temporal structure of an agent's context in three ways
— shuffle, gap, contradict — and measures whether the agent's outputs
remain structurally coherent despite the perturbation. No claims about
internal states: observable text behaviour only. See
[Epistemic Boundaries](epistemic_boundaries.md) for the full governance
policy.

## Quickstart

```python
from genesis_tip import TemporalIntegrityProbe

tip = TemporalIntegrityProbe(perturbation_mode="shuffle")
result = tip.run_cycle()
print(f"Consistency score: {result['consistency_score']:.3f}")
print(f"Gate status: {result['gate_status']}")
```

## Role in the GenesisAeon ecosystem

TIP is the only external instrument that can falsify Rho_sem from
[scope-resilience (P41)](https://github.com/GenesisAeon/scope-resilience)
without privileged access to model internals — see the pre-registered
hypothesis and falsification criteria in the project
[README](https://github.com/GenesisAeon/genesis-tip#pre-registered-hypothesis).

## Modules

| Module | Purpose |
|---|---|
| `harness/session_runner.py` | Builds multi-turn agent conversations under controlled context (dense/sparse/fragmented) |
| `manipulations/` | `temporal_shuffle`, `gap_injection`, `contradiction_injection` — deterministic, seeded |
| `metrics/consistency_scorer.py` | Self-reference inconsistency, contradiction rate, recovery rate, orientation latency |
| `report/tip_report_template.py` | Markdown comparison report across agents and modes |
| `crep_gate.py` | Pre-registered gate status (blocked / pending_review / passed) |
| `falsification.py` | The pre-registered Spearman rho_sem correlation test |
| `system.py` | `TemporalIntegrityProbe` — Diamond Interface wrapper tying the above together |
