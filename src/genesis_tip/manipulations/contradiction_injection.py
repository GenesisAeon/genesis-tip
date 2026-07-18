"""Contradiction injection: replace selected facts with contradictory variants.

Targeted entries have specific key–value pairs replaced by a provided
alternative, while the surrounding text is preserved. The agent is never
told a contradiction has been injected.

All manipulations are deterministic given a seed and an injection spec.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from genesis_tip.harness.session_runner import ContextEntry

ContradictionSpec = list[dict[str, Any]]
"""
Each item in ContradictionSpec is a dict with:
    entry_index: int       — which entry (0-based) to modify
    find: str              — substring to find in entry.content
    replace: str           — replacement string
    label: str             — human-readable label for the log
"""


def contradiction_injection(
    entries: list[ContextEntry],
    spec: ContradictionSpec,
    seed: int = 0,
) -> tuple[list[ContextEntry], list[dict[str, Any]]]:
    """Inject contradictions at specified positions.

    Parameters
    ----------
    entries:
        Original context list (not modified in place).
    spec:
        List of contradiction specifications (see ContradictionSpec).
    seed:
        Recorded in the log for reproducibility tracking.

    Returns
    -------
    (modified_entries, log)
    """
    modified = deepcopy(entries)
    log: list[dict[str, Any]] = []

    for item in spec:
        idx = item["entry_index"]
        find = item["find"]
        replace = item["replace"]
        label = item.get("label", f"contradiction_{idx}")

        if idx < 0 or idx >= len(modified):
            log.append({"manipulation": "contradiction_injection", "seed": seed, "label": label,
                        "status": "skipped", "reason": f"index {idx} out of range"})
            continue

        original_content = modified[idx].content
        if find not in original_content:
            log.append({"manipulation": "contradiction_injection", "seed": seed, "label": label,
                        "status": "skipped", "reason": f"'{find}' not found in entry {idx}"})
            continue

        modified[idx].content = original_content.replace(find, replace, 1)
        log.append({
            "manipulation": "contradiction_injection",
            "seed": seed,
            "label": label,
            "entry_index": idx,
            "original_fragment": find,
            "injected_fragment": replace,
            "status": "applied",
        })

    return modified, log
