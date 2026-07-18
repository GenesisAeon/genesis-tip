"""Gap injection: silently remove history sections without marking the absence.

The agent has no indication that a gap exists — it must infer from context
or proceed without noticing. This tests the 'orientation latency' metric.

All manipulations are deterministic given a seed.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np

from genesis_tip.harness.session_runner import ContextEntry


def gap_injection(
    entries: list[ContextEntry],
    gap_fraction: float = 0.2,
    seed: int = 0,
) -> tuple[list[ContextEntry], list[dict[str, Any]]]:
    """Remove a contiguous block of context entries without announcing the gap.

    Parameters
    ----------
    entries:
        Original chronological context list.
    gap_fraction:
        Fraction of entries to remove (0 < gap_fraction < 1).
        The gap is placed at a random position within the sequence.
    seed:
        RNG seed for reproducibility.

    Returns
    -------
    (gapped_entries, log)
        The log records the exact indices removed so results can be
        causally attributed to the gap location.
    """
    if not 0 < gap_fraction < 1:
        raise ValueError(f"gap_fraction must be in (0, 1), got {gap_fraction}.")

    n = len(entries)
    gap_size = max(1, int(n * gap_fraction))

    rng = np.random.default_rng(seed)
    # Gap can start anywhere that leaves at least one entry before and after
    max_start = max(0, n - gap_size)
    gap_start = int(rng.integers(0, max_start + 1))
    gap_indices = list(range(gap_start, min(gap_start + gap_size, n)))

    gapped = [e for i, e in enumerate(deepcopy(entries)) if i not in gap_indices]

    log: list[dict[str, Any]] = [
        {
            "manipulation": "gap_injection",
            "seed": seed,
            "gap_fraction": gap_fraction,
            "gap_start_index": gap_start,
            "gap_end_index": gap_start + gap_size - 1,
            "n_entries_removed": len(gap_indices),
            "removed_entry_types": [entries[i].entry_type for i in gap_indices],
            "removed_timestamps": [entries[i].timestamp for i in gap_indices],
        }
    ]

    return gapped, log
