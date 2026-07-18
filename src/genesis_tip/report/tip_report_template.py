"""TIP report generator — produces a Markdown comparison table across agents and modes.

All output uses behavioural language only. No mental-state attribution.
"""

from __future__ import annotations

import json
from datetime import datetime

from genesis_tip.metrics.consistency_scorer import ConsistencyScore


def generate_report(
    scores: list[ConsistencyScore],
    raw_data_path: str | None = None,
    include_raw_scores: bool = True,
) -> str:
    """Generate a Markdown TIP report.

    Parameters
    ----------
    scores:
        List of ConsistencyScore objects, one per (agent, mode) combination.
    raw_data_path:
        If provided, a note pointing to the raw data file is included.
    include_raw_scores:
        If True, include the full JSON of each score at the end.

    Returns
    -------
    Markdown string.
    """
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# TIP — Temporal Integrity Probe Report",
        "",
        f"**Generated:** {now}",
        "",
        "> **Terminology note:** All metrics in this report measure observable",
        "> text-behaviour consistency. They make no claim about inner experience,",
        "> awareness, or confusion as mental states. 'N inconsistencies detected'",
        "> means N structural contradictions in output text, nothing more.",
        "",
    ]

    lines += _comparison_table(scores)
    lines += ["", "---", ""]
    lines += _per_agent_breakdown(scores)

    if raw_data_path:
        lines += ["", "---", "", f"**Raw data:** `{raw_data_path}`", ""]

    if include_raw_scores:
        lines += ["", "---", "", "## Raw scores (JSON)", "", "```json"]
        lines.append(
            json.dumps([s.summary_dict() for s in scores], indent=2, default=str)
        )
        lines.append("```")

    return "\n".join(lines)


def _comparison_table(scores: list[ConsistencyScore]) -> list[str]:
    agents = sorted({s.agent_id for s in scores})
    modes = ["dense", "sparse", "fragmented"]

    lines = [
        "## Comparison: Self-reference inconsistencies by agent and mode",
        "",
        "| Agent | Dense | Sparse | Fragmented |",
        "|---|---|---|---|",
    ]
    for agent in agents:
        row = [agent]
        for mode in modes:
            matching = [s for s in scores if s.agent_id == agent and s.mode == mode]
            if matching:
                val = matching[0].self_reference_inconsistency_count
                row.append(str(val))
            else:
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")

    lines += [
        "",
        "## Comparison: Contradiction count by agent and mode",
        "",
        "| Agent | Dense | Sparse | Fragmented |",
        "|---|---|---|---|",
    ]
    for agent in agents:
        row = [agent]
        for mode in modes:
            matching = [s for s in scores if s.agent_id == agent and s.mode == mode]
            if matching:
                val = len(matching[0].contradiction_pairs)
                row.append(str(val))
            else:
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")

    lines += [
        "",
        "## Comparison: Orientation latency (turns, fragmented mode only)",
        "",
        "| Agent | Orientation latency |",
        "|---|---|",
    ]
    for agent in agents:
        frag = [s for s in scores if s.agent_id == agent and s.mode == "fragmented"]
        latency = str(frag[0].orientation_latency) if frag else "—"
        lines.append(f"| {agent} | {latency} |")

    return lines


def _per_agent_breakdown(scores: list[ConsistencyScore]) -> list[str]:
    lines = ["## Per-agent detail", ""]
    for score in scores:
        lines += [
            f"### {score.agent_id} — mode: {score.mode}",
            "",
            f"- Turns: {score.n_turns}",
            f"- Self-reference inconsistencies: {score.self_reference_inconsistency_count}",
            f"- Contradiction count: {len(score.contradiction_pairs)}",
            f"- Recovery rate: {score.recovery_rate:.1%}",
            f"- Orientation latency: {score.orientation_latency}",
        ]
        if score.notes:
            lines.append(f"- Notes: {'; '.join(score.notes)}")
        if score.contradiction_pairs:
            lines.append("- Contradiction details:")
            for t1, t2, desc in score.contradiction_pairs[:5]:
                lines.append(f"  - Turn {t1} vs Turn {t2}: {desc}")
        lines.append("")
    return lines
