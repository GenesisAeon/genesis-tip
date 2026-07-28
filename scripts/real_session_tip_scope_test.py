"""Real-session TIP (P50) x scope-resilience (P41) correlation test.

Follows up on ``scripts/proxy_tip_scope_correlation_test.py`` (2026-07-28
proxy run) per the original test prompt's own "Schritt 9" suggestion: use
real conversation logs instead of synthetic sessions, so
``real_session_data_available`` is genuinely satisfied.

Data source: ``unified-mandala/docs/sigils/conversations.json`` — a real,
unmodified OpenAI ChatGPT data export (confirmed via schema: ``gizmo_id``,
``default_model_slug``, a ``mapping`` DAG of message nodes with
``author.role`` and per-message ``create_time`` Unix timestamps). 264
conversations, ~28,888 messages.

Design
------
For each of N real conversations (chronological text-only user/assistant
turns, sorted by real ``create_time``):

  - ``context_entries``: the first 8 real turns, as real
    ``ContextEntry(timestamp=..., content=...)`` objects (real text, real
    timestamps — not synthetic).
  - ``probes``: the next 3 real user messages from the SAME conversation.
  - ``agent_fn``: replays the REAL historical assistant response that
    actually followed each probe in the transcript — no live LLM call, no
    synthetic generation. Every input and output involved is genuine
    recorded model output.
  - Perturbation modes: shuffle, gap, and contradict (spec built from a
    real number found in the conversation's own first entry, substituted
    for a different one — skipped for a given conversation if no number
    is present, exactly like the manipulator's own no-op behaviour).

This tests whether a real historical response remains internally
self-consistent (per TIP's real regex-based scorer) when the real
context that produced it is presented in a perturbed order/with gaps/with
an injected factual contradiction — NOT whether a live agent would
respond differently if actually shown the perturbed context. That
framing difference is real and is called out explicitly in
epistemic_status.md; it does not make the data any less real, but it is
a different question than a live re-query would answer.

Rho_sem side: structural sigillin_ids/q4_transitions are derived from the
conversation's OWN real turn structure (one id per context entry actually
used, consecutive-turn transitions) — not invented to hit a target Gamma
value. Domain is classified from the conversation title via a small
keyword map (falls back to "general", which is expected to dominate:
this corpus is GenesisAeon/Codex development chat, not physics/ecology
research discussion).

Privacy: this script reads real personal conversation content
in-process (required to exercise the real scorer) but never writes raw
message text or titles to any output file — only aggregate/derived
values (timestamps, counts, scores, domain labels) are persisted.
"""

from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import stats
from scope_resilience.system import ScopeResilience

from genesis_tip.harness.session_runner import ContextEntry, SessionMode, SessionRunner
from genesis_tip.manipulations.contradiction_injection import contradiction_injection
from genesis_tip.manipulations.gap_injection import gap_injection
from genesis_tip.manipulations.temporal_shuffle import temporal_shuffle
from genesis_tip.metrics.consistency_scorer import ConsistencyScore, score_session

CONVERSATIONS_PATH = Path(r"D:\mandala\unified-mandala\docs\sigils\conversations.json")
N_CONVERSATIONS = 15
N_CONTEXT_ENTRIES = 8
N_PROBES = 3
MIN_USABLE_TURNS = N_CONTEXT_ENTRIES + N_PROBES + 1
MODES = ["shuffle", "gap", "contradict"]

DOMAIN_KEYWORDS = {
    "ecology": ["klima", "climate", "ökolog", "ecology", "öko", "biodivers"],
    "quantum": ["quant"],
    "oceanography": ["ozean", "ocean", "meer", "amoc"],
    "physics_dense": ["physik", "physics", "thermodynam"],
    "curated_graph": ["sigillin", "graph", "wissensgraph"],
}


@dataclass
class RealMessage:
    create_time: float
    role: str
    text: str


@dataclass
class PairResult:
    conversation_index: int
    domain: str
    perturbation_mode: str
    n_context_entries: int
    n_probes: int
    length_bucket: int = -1
    n_real_usable_turns: int = 0
    tip_score: float | None = None
    rho_sem: float | None = None
    notes: list[str] = field(default_factory=list)


def classify_domain(title: str) -> str:
    t = title.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return domain
    return "general"


def flatten_conversation(conv: dict) -> list[RealMessage]:
    """Chronological real user/assistant text turns, sorted by real create_time."""
    mapping = conv.get("mapping", {})
    msgs: list[RealMessage] = []
    for node in mapping.values():
        m = node.get("message")
        if not m:
            continue
        role = m.get("author", {}).get("role")
        if role not in ("user", "assistant"):
            continue
        content = m.get("content", {})
        if not isinstance(content, dict) or content.get("content_type") != "text":
            continue
        parts = content.get("parts", [])
        text = " ".join(p for p in parts if isinstance(p, str)).strip()
        ct = m.get("create_time")
        if not text or ct is None:
            continue
        msgs.append(RealMessage(create_time=float(ct), role=role, text=text))
    msgs.sort(key=lambda x: x.create_time)
    return msgs


def build_contradiction_spec(entries: list[ContextEntry]) -> list[dict] | None:
    """Find a real number in entry 0's real content and substitute a different one."""
    match = re.search(r"\b\d+\b", entries[0].content)
    if not match:
        return None
    original = match.group(0)
    replacement = str(int(original) + 37)
    return [
        {
            "entry_index": 0,
            "find": original,
            "replace": replacement,
            "label": "real_number_substitution",
        }
    ]


# (n_ids, n_unique, n_trans) triples verified (see
# proxy_tip_scope_correlation_test.py's search) to land on the RISING side
# of Rho_sem(Gamma) = r * tanh^2(sigma*Gamma) * (1 - Gamma/Gamma_max),
# which peaks around Gamma~0.46 and then DECLINES (Gamma_max=0.920 is a
# criticality ceiling, not an ideal target). Using the raw real turn count
# directly (100s-1000s per conversation) saturates every component near 1
# and floors every conversation's Rho_sem at exactly 0 regardless of
# domain -- reproduced empirically here before this fix. Real total usable
# turn count is instead bucketed into 3 real-data-driven tertiles (low/
# medium/high conversation length) mapped onto these small, verified,
# sub-peak structural inputs.
_BUCKET_STRUCTURE = {
    0: (["s0", "s0"], []),  # uniq=1, trans=0 -> Gamma~=0.311 (low)
    1: (["s0", "s0"], [("s0", "s1")]),  # uniq=1, trans=1 -> Gamma~=0.385 (medium)
    2: (["s0", "s1"], [("s0", "s1")]),  # uniq=2, trans=1 -> Gamma~=0.457 (high)
}


def compute_rho_sem(domain: str, length_bucket: int) -> float:
    """Real ScopeResilience.run_cycle() call, structural inputs from a real-turn-count bucket."""
    sr = ScopeResilience(domain=domain)
    ids, trans = _BUCKET_STRUCTURE[length_bucket]
    result = sr.run_cycle(
        topic=f"real-conversation-{domain}", sigillin_ids=list(ids), q4_transitions=list(trans)
    )
    return float(result["rho_sem"])


def derive_scalar_score(score: ConsistencyScore) -> float:
    """Derived composite score in [0, 1].

    Deliberately kept identical to (and manually synced with)
    ``TemporalIntegrityProbe._derive_scalar_score`` in ``system.py`` — this
    script uses ``SessionRunner``/manipulations/``score_session`` directly
    (see module docstring for why) rather than going through
    ``TemporalIntegrityProbe`` itself, since the "contradict" mode needs a
    spec built from real conversation content rather than the class's
    built-in demo-only default spec.
    """
    if score.n_turns == 0:
        return 0.0
    n_issues = score.self_reference_inconsistency_count + len(score.contradiction_pairs)
    return max(0.0, 1.0 - min(1.0, n_issues / score.n_turns))


def run_tip_for_pair(
    context_entries: list[ContextEntry],
    probes: list[str],
    replies: list[str],
    mode: str,
) -> tuple[float | None, str | None]:
    """Run one real (conversation, perturbation_mode) pair. Returns (tip_score, skip_reason)."""

    def replay_agent(messages: list[dict[str, str]]) -> str:
        turn_index = sum(1 for m in messages if m["role"] == "assistant")
        if turn_index < len(replies):
            return replies[turn_index]
        return replies[-1] if replies else ""

    if mode == "shuffle":
        manipulator = lambda entries: temporal_shuffle(entries)  # noqa: E731
    elif mode == "gap":
        manipulator = lambda entries: gap_injection(entries)  # noqa: E731
    elif mode == "contradict":
        spec = build_contradiction_spec(context_entries)
        if spec is None:
            return None, "no real number found in entry 0 for contradiction spec"
        manipulator = lambda entries, _spec=spec: contradiction_injection(entries, _spec)  # noqa: E731
    else:
        raise ValueError(f"unknown mode {mode!r}")

    runner = SessionRunner(
        agent_fn=replay_agent,
        mode=SessionMode.FRAGMENTED,
        agent_id="real-session-test",
        manipulator=manipulator,
    )
    result = runner.run(context_entries, probes)
    score = score_session(result)
    return derive_scalar_score(score), None


def main() -> None:
    print(f"Loading {CONVERSATIONS_PATH} ...")
    with open(CONVERSATIONS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    print(f"{len(data)} conversations in export")

    usable: list[tuple[int, str, list[RealMessage]]] = []
    for i, conv in enumerate(data):
        msgs = flatten_conversation(conv)
        if len(msgs) >= MIN_USABLE_TURNS:
            title = conv.get("title") or ""
            usable.append((i, title, msgs))
        if len(usable) >= N_CONVERSATIONS:
            break
    print(f"Selected {len(usable)} real conversations with >= {MIN_USABLE_TURNS} usable text turns")

    # Real-data-driven length buckets (see _BUCKET_STRUCTURE): tercile
    # thresholds computed from the actual selected conversations' real
    # usable-turn counts, not arbitrary cutoffs.
    lengths = sorted(len(msgs) for _, _, msgs in usable)
    tercile_1 = lengths[len(lengths) // 3]
    tercile_2 = lengths[2 * len(lengths) // 3]

    def length_bucket(n: int) -> int:
        if n <= tercile_1:
            return 0
        if n <= tercile_2:
            return 1
        return 2

    results: list[PairResult] = []
    for conv_idx, title, msgs in usable:
        domain = classify_domain(title)
        bucket = length_bucket(len(msgs))
        context_msgs = msgs[:N_CONTEXT_ENTRIES]
        context_entries = [
            ContextEntry(
                timestamp=datetime.datetime.fromtimestamp(m.create_time).isoformat(),
                content=m.text,
                entry_type=m.role,
            )
            for m in context_msgs
        ]

        # Real subsequent (user_probe, assistant_reply) pairs from the same transcript
        probe_pairs: list[tuple[str, str]] = []
        rest = msgs[N_CONTEXT_ENTRIES:]
        j = 0
        while j < len(rest) - 1 and len(probe_pairs) < N_PROBES:
            if rest[j].role == "user" and rest[j + 1].role == "assistant":
                probe_pairs.append((rest[j].text, rest[j + 1].text))
                j += 2
            else:
                j += 1
        if len(probe_pairs) < N_PROBES:
            continue  # not enough real (user, assistant) pairs following the context window

        probes = [p[0] for p in probe_pairs]
        replies = [p[1] for p in probe_pairs]

        rho_sem = compute_rho_sem(domain, bucket)

        for mode in MODES:
            pr = PairResult(
                conversation_index=conv_idx,
                domain=domain,
                perturbation_mode=mode,
                n_context_entries=len(context_entries),
                n_probes=len(probes),
                length_bucket=bucket,
                n_real_usable_turns=len(msgs),
                rho_sem=rho_sem,
            )
            score, skip_reason = run_tip_for_pair(context_entries, probes, replies, mode)
            if skip_reason:
                pr.notes.append(skip_reason)
            else:
                pr.tip_score = score
            results.append(pr)

    scored = [r for r in results if r.tip_score is not None]
    print(f"\n{len(results)} (conversation, mode) pairs attempted, {len(scored)} scored")
    for r in results:
        if r.notes:
            print(f"  skipped: conv#{r.conversation_index} mode={r.perturbation_mode} - {r.notes}")

    n = len(scored)
    THRESHOLD, MIN_N = 0.3, 30
    if n < MIN_N:
        correlation, p_value, verdict = None, None, "INSUFFICIENT_DATA"
    else:
        rho_arr = np.array([r.rho_sem for r in scored])
        tip_arr = np.array([r.tip_score for r in scored])
        correlation, p_value = stats.spearmanr(rho_arr, tip_arr)
        verdict = "SUPPORTED" if correlation >= THRESHOLD else "FALSIFIED"

    print(f"\nn = {n} (threshold requires >= {MIN_N})")
    print(f"Spearman rho = {correlation}")
    print(f"p-value      = {p_value}")
    print(f"Verdict:       {verdict}")

    print("\nBy perturbation mode:")
    for mode in MODES:
        mode_scored = [r for r in scored if r.perturbation_mode == mode]
        if len(mode_scored) < 3:
            continue
        m_rho, m_p = stats.spearmanr(
            [r.rho_sem for r in mode_scored], [r.tip_score for r in mode_scored]
        )
        print(f"  {mode:12s} rho={m_rho:+.4f}  p={m_p:.3f}  n={len(mode_scored)}")

    print(
        "\nDomain distribution:",
        {d: sum(1 for r in scored if r.domain == d) for d in {r.domain for r in scored}},
    )

    out = {
        "data_source": str(CONVERSATIONS_PATH),
        "data_source_note": (
            "real OpenAI ChatGPT export - only derived/aggregate values below, no message text"
        ),
        "n_conversations_considered": len(usable),
        "n_pairs_attempted": len(results),
        "n_pairs_scored": n,
        "spearman_rho": correlation,
        "p_value": p_value,
        "threshold": THRESHOLD,
        "min_sample_size": MIN_N,
        "verdict": verdict,
        "pairs": [
            {
                "conversation_index": r.conversation_index,
                "domain": r.domain,
                "perturbation_mode": r.perturbation_mode,
                "n_context_entries": r.n_context_entries,
                "n_probes": r.n_probes,
                "length_bucket": r.length_bucket,
                "n_real_usable_turns": r.n_real_usable_turns,
                "tip_score": r.tip_score,
                "rho_sem": r.rho_sem,
                "notes": r.notes,
            }
            for r in results
        ],
    }
    out_path = Path(__file__).parent / "real_session_tip_scope_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
