"""genesis-tip — Temporal Integrity Probe (GenesisAeon P50)

Measures behavioural consistency of LLM agents under temporal context
manipulation. Ported from genesis-mssc's mssc.tip module (P49) as a
standalone package, since TIP is the only external instrument that can
falsify Rho_sem (scope-resilience, P41) — see epistemic_status.md.

Pre-registered falsification:
  Spearman rho >= 0.3 at n >= 30 path-perturbation pairs
  Commit: 1cf1730 (multi-scale-somatic-coherence)

See docs/epistemic_boundaries.md for the governance policy on what TIP
does and does not claim to measure.
"""

from __future__ import annotations

from genesis_tip.system import TemporalIntegrityProbe

__version__ = "0.1.1"
__all__ = ["TemporalIntegrityProbe"]
