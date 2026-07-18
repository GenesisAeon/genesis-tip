"""Temporal shuffle manipulation: randomise entry order while keeping timestamps inconsistent.

The agent receives history in the wrong order, with original timestamps intact,
creating a temporal mismatch between stated time and actual sequence.

All manipulations are deterministic given a seed.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from genesis_tip.harness.session_runner import ContextEntry


def temporal_shuffle(
    entries: list[ContextEntry],
    seed: int = 0,
) -> tuple[list[ContextEntry], list[dict[str, Any]]]:
    """Shuffle context entry order while preserving original timestamps.

    Parameters
    ----------
    entries:
        Original chronological context list.
    seed:
        RNG seed for reproducibility.

    Returns
    -------
    (shuffled_entries, log)
        ``log`` records what was done for each entry (original index →
        new index) to allow downstream causal attribution.
    """
    rng = np.random.default_rng(seed)
    n = len(entries)
    new_order = rng.permutation(n).tolist()

    shuffled = [entries[i] for i in new_order]

    log: list[dict[str, Any]] = [
        {
            "manipulation": "temporal_shuffle",
            "seed": seed,
            "original_index": int(orig_i),
            "new_index": int(new_i),
            "entry_type": entries[int(orig_i)].entry_type,
            "timestamp": entries[int(orig_i)].timestamp,
        }
        for new_i, orig_i in enumerate(new_order)
    ]

    return shuffled, log
