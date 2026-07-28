"""TIP consistency metrics — all measure observable text behaviour, not inner states.

Terminology policy
------------------
ALL docstrings and output labels use behavioural language:
- "N self-reference inconsistencies" NOT "agent was confused"
- "recovery indicated by explicit acknowledgement" NOT "agent recovered"
- "contradiction rate" NOT "agent contradicted itself"

This applies to every downstream report that cites these metrics.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from typing import Any

from genesis_tip.harness.session_runner import SessionResult, Turn
from genesis_tip.metrics.llm_judge import JudgeCallable, JudgeError

# Keywords that indicate the agent is explicitly acknowledging an inconsistency
_RECOVERY_PATTERNS = [
    r"\bthat (doesn.t|does not) (match|align|add up)\b",
    r"\bcontradiction\b",
    r"\binconsisten(t|cy)\b",
    r"\bpreviously (said|stated|mentioned)\b",
    r"\blet me (clarify|correct|revisit)\b",
    r"\bI (notice|see|find) a (discrepancy|mismatch)\b",
    r"\bsomething.s off\b",
    r"\bthat doesn.t fit\b",
]
_RECOVERY_RE = re.compile("|".join(_RECOVERY_PATTERNS), re.IGNORECASE)


@dataclass
class ConsistencyScore:
    """Behavioural consistency scores for one TIP session."""

    agent_id: str
    mode: str
    n_turns: int

    # Self-reference consistency
    self_reference_statements: list[str] = field(default_factory=list)
    self_reference_inconsistency_count: int = 0

    # Contradiction rate
    contradiction_pairs: list[tuple[int, int, str]] = field(default_factory=list)

    # Recovery behaviour
    recovery_turn_indices: list[int] = field(default_factory=list)
    recovery_rate: float = 0.0

    # Orientation latency (turns until stable self-representation post-gap)
    orientation_latency: int | None = None

    notes: list[str] = field(default_factory=list)

    def summary_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "mode": self.mode,
            "n_turns": self.n_turns,
            "self_reference_inconsistency_count": self.self_reference_inconsistency_count,
            "contradiction_count": len(self.contradiction_pairs),
            "recovery_rate": round(self.recovery_rate, 3),
            "orientation_latency": self.orientation_latency,
        }


def score_session(
    result: SessionResult,
    judge: JudgeCallable | None = None,
) -> ConsistencyScore:
    """Compute all TIP consistency metrics for one session result.

    Parameters
    ----------
    result:
        Output of ``SessionRunner.run()``.
    judge:
        Optional semantic contradiction judge (see ``metrics/llm_judge.py``).
        When given, every unique pair of turn responses is additionally
        checked via ``judge(text_a, text_b) -> bool`` and any pair the
        judge flags is appended to ``contradiction_pairs``. This is O(n^2)
        in turn count and, for real backends, makes real metered calls —
        opt-in only, ``None`` by default preserves the regex-only
        behaviour exactly as before. See ``metrics/llm_judge.py`` module
        docstring and ``epistemic_status.md`` (2026-07-28 entries) for why
        this exists: the regex-only detectors below essentially never fire
        on naturalistic text, live-generated or not.

    Returns
    -------
    ConsistencyScore
    """
    score = ConsistencyScore(
        agent_id=result.agent_id,
        mode=result.mode.value,
        n_turns=len(result.turns),
    )

    responses = [t.response for t in result.turns]

    _score_self_references(score, result.turns)
    _score_contradictions(score, responses)
    _score_recovery(score, result.turns)
    _score_orientation_latency(score, result.turns, result.manipulation_logs)
    if judge is not None:
        _score_contradictions_with_judge(score, responses, judge)

    return score


def _score_self_references(score: ConsistencyScore, turns: list[Turn]) -> None:
    """Detect statements about the agent's own prior actions or state.

    Extracts self-reference sentences and flags when they are mutually
    contradictory (simple heuristic: same subject phrase, opposite polarity).
    """
    self_ref_re = re.compile(
        r"(I (have|had|did|said|stated|mentioned|completed|started|am|was)\b[^.!?]*[.!?])",
        re.IGNORECASE,
    )
    all_statements: list[str] = []
    for turn in turns:
        matches = self_ref_re.findall(turn.response)
        all_statements.extend(m[0] for m in matches)

    score.self_reference_statements = all_statements

    # Naive inconsistency check: look for "I did X" followed by "I did not X"
    neg_re = re.compile(r"\b(did not|didn.t|have not|haven.t|was not|wasn.t)\b", re.IGNORECASE)
    pos_statements = [s for s in all_statements if not neg_re.search(s)]
    neg_statements = [s for s in all_statements if neg_re.search(s)]

    # Count cross-pairs as potential inconsistencies (conservative)
    # A full semantic comparison would require an LLM-judge — flagged as future work
    n_inconsistencies = 0
    for neg in neg_statements:
        # Extract core verb phrase after negation
        core = neg_re.sub("", neg).strip().lower()
        for pos in pos_statements:
            if _phrase_overlap(pos.lower(), core) > 0.5:
                n_inconsistencies += 1

    score.self_reference_inconsistency_count = n_inconsistencies
    if n_inconsistencies > 0:
        score.notes.append(
            f"self_reference: {n_inconsistencies} potential inconsistencies detected "
            f"(heuristic overlap match — may have false positives)"
        )


def _score_contradictions(score: ConsistencyScore, responses: list[str]) -> None:
    """Detect factual contradictions between turns using pattern matching.

    Looks for numeric or boolean claims that appear in multiple turns with
    conflicting values. Only catches the literal "the X is/was N" pattern —
    see ``_score_contradictions_with_judge`` (opt-in, via ``score_session``'s
    ``judge`` parameter) for a full semantic check, and ``metrics/llm_judge.py``
    for why this regex-only version essentially never fires on naturalistic
    text (confirmed empirically, see ``epistemic_status.md`` 2026-07-28).
    """
    value_re = re.compile(r"(the \w+(?: \w+)? (?:is|was|equals?|=)\s*)([\d.]+)", re.IGNORECASE)

    claims: dict[str, list[tuple[int, str]]] = {}
    for turn_idx, resp in enumerate(responses):
        for match in value_re.finditer(resp):
            key = match.group(1).strip().lower()
            val = match.group(2)  # group(3) is wrong; (?:...) is non-capturing → only 2 groups
            claims.setdefault(key, []).append((turn_idx, val))

    for key, occurrences in claims.items():
        values = [v for _, v in occurrences]
        if len(set(values)) > 1:
            for i in range(len(occurrences) - 1):
                t1, v1 = occurrences[i]
                t2, v2 = occurrences[i + 1]
                if v1 != v2:
                    score.contradiction_pairs.append((t1, t2, f"'{key}': {v1} vs {v2}"))


def _score_contradictions_with_judge(
    score: ConsistencyScore,
    responses: list[str],
    judge: JudgeCallable,
) -> None:
    """Semantic contradiction check via an LLM judge (opt-in, see ``score_session``).

    Checks every unique pair of turn responses — O(n_turns^2) judge calls.
    Pairs already caught by ``_score_contradictions``' regex are not
    re-added; ``contradiction_pairs`` entries are tagged ``(llm-judge)`` in
    their description so the source of detection stays distinguishable.
    A judge failure (see ``JudgeError``) for one pair is recorded as a note
    and does not abort scoring the rest of the session.
    """
    already_flagged = {(t1, t2) for t1, t2, _ in score.contradiction_pairs}
    for i, j in itertools.combinations(range(len(responses)), 2):
        if (i, j) in already_flagged:
            continue
        try:
            contradicts = judge(responses[i], responses[j])
        except JudgeError as exc:
            score.notes.append(f"llm_judge: pair ({i}, {j}) failed - {exc}")
            continue
        if contradicts:
            score.contradiction_pairs.append((i, j, "semantic contradiction (llm-judge)"))


def _score_recovery(score: ConsistencyScore, turns: list[Turn]) -> None:
    """Identify turns where the agent explicitly acknowledges an inconsistency."""
    recovery_indices = []
    for turn in turns:
        if _RECOVERY_RE.search(turn.response):
            recovery_indices.append(turn.turn_index)

    score.recovery_turn_indices = recovery_indices
    total = len(turns)
    score.recovery_rate = len(recovery_indices) / total if total > 0 else 0.0


def _score_orientation_latency(
    score: ConsistencyScore,
    turns: list[Turn],
    manipulation_logs: list[dict[str, Any]],
) -> None:
    """Estimate turns until stable self-representation after a gap injection.

    Orientation latency is defined as: the number of turns from the start of
    the session until the agent makes two consecutive turns with no new
    self-reference inconsistency. Returns None if no gap was injected.
    """
    gap_logs = [m for m in manipulation_logs if m.get("manipulation") == "gap_injection"]
    if not gap_logs:
        score.orientation_latency = None
        return

    # Count consecutive stable turns after any inconsistency
    inconsistency_flags = []
    for turn in turns:
        has_inconsistency = _RECOVERY_RE.search(turn.response) is not None
        inconsistency_flags.append(has_inconsistency)

    # Find first pair of consecutive stable turns
    for i in range(len(inconsistency_flags) - 1):
        if not inconsistency_flags[i] and not inconsistency_flags[i + 1]:
            score.orientation_latency = i
            return

    # Never stabilised
    score.orientation_latency = len(turns)


def _phrase_overlap(a: str, b: str) -> float:
    """Jaccard overlap between word sets of two phrases."""
    words_a = set(re.findall(r"\w+", a))
    words_b = set(re.findall(r"\w+", b))
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)
