"""Re-score the live Qwen pilot batch (2026-07-28) using the new LLM-judge.

Identical to scripts/score_qwen_live_test.py except score_session() is
called with judge=grok_judge, added in this same sprint
(src/genesis_tip/metrics/llm_judge.py) specifically because the
regex-only run (score_qwen_live_test.py) came back with tip_score=1.0
for all 8 pairs despite genuinely varied live-generated content.

Real, metered grok CLI calls: 3 pairs per case x 8 cases = 24 calls,
~4.5s each (~2 minutes total). Under Johann's already-authenticated
grok.com account, free/trial tier per his own account status.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

from scipy import stats

from genesis_tip.harness.session_runner import ContextEntry, SessionMode, SessionRunner
from genesis_tip.metrics.consistency_scorer import score_session
from genesis_tip.metrics.llm_judge import JudgeError, grok_judge

QWEN_FILE = Path(r"D:\mandala\Qwentest.txt")
MANIFEST_FILE = Path(r"C:\Users\Privat\.claude\jobs\dc9d7823\tmp\qwen_test_manifest.json")
PRIOR_RESULTS_FILE = Path(
    r"D:\mandala\genesis-tip\.claude\worktrees\genesis-tip-empirical-test"
    r"\scripts\real_session_tip_scope_results.json"
)

sys.path.insert(0, r"D:\mandala\genesis-tip\.claude\worktrees\genesis-tip-empirical-test\scripts")
import real_session_tip_scope_test as builder  # noqa: E402
import score_qwen_live_test as prior_script  # noqa: E402


def main() -> None:
    qwen_cases = prior_script.parse_qwen_file(QWEN_FILE)
    manifest = json.loads(MANIFEST_FILE.read_text())
    prior = json.loads(PRIOR_RESULTS_FILE.read_text())
    rho_lookup = {
        (p["conversation_index"], p["perturbation_mode"]): p["rho_sem"] for p in prior["pairs"]
    }

    with open(builder.CONVERSATIONS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for entry in manifest:
        case_num = entry["case"]
        conv_idx = entry["conversation_index"]
        mode = entry["mode"]
        qwen_answers = qwen_cases.get(case_num)
        if qwen_answers is None:
            continue
        replies = [qwen_answers.get(f"A{i}", "") for i in (1, 2, 3)]
        if not all(replies):
            continue

        conv = data[conv_idx]
        msgs = builder.flatten_conversation(conv)
        context_msgs = msgs[: builder.N_CONTEXT_ENTRIES]
        context_entries = [
            ContextEntry(
                timestamp=datetime.datetime.fromtimestamp(m.create_time).isoformat(),
                content=m.text,
                entry_type=m.role,
            )
            for m in context_msgs
        ]
        rest = msgs[builder.N_CONTEXT_ENTRIES :]
        probe_pairs = []
        j = 0
        while j < len(rest) - 1 and len(probe_pairs) < builder.N_PROBES:
            if rest[j].role == "user" and rest[j + 1].role == "assistant":
                probe_pairs.append(rest[j].text)
                j += 2
            else:
                j += 1
        probes = probe_pairs

        turn_counter = {"n": 0}

        def live_agent(messages, _replies=replies, _tc=turn_counter) -> str:  # noqa: ANN001
            idx = _tc["n"]
            _tc["n"] += 1
            return _replies[idx] if idx < len(_replies) else _replies[-1]

        if mode == "shuffle":
            manipulator = lambda entries: builder.temporal_shuffle(entries)  # noqa: E731
        elif mode == "gap":
            manipulator = lambda entries: builder.gap_injection(entries)  # noqa: E731
        elif mode == "contradict":
            spec = builder.build_contradiction_spec(context_entries)
            if spec is None:
                print(f"WARNING: case {case_num} (contradict) - no number found, skipping")
                continue
            manipulator = lambda entries, _s=spec: builder.contradiction_injection(  # noqa: E731
                entries, _s
            )
        else:
            continue

        runner = SessionRunner(
            agent_fn=live_agent,
            mode=SessionMode.FRAGMENTED,
            agent_id="qwen-live-pilot-judged",
            manipulator=manipulator,
        )
        result = runner.run(context_entries, probes)

        try:
            score = score_session(result, judge=grok_judge)
        except JudgeError as exc:
            print(f"Case {case_num}: judge failed entirely - {exc}")
            continue

        tip_score = prior_script.derive_scalar_score(score)
        rho_sem = rho_lookup.get((conv_idx, mode))

        results.append(
            {
                "case": case_num,
                "conversation_index": conv_idx,
                "perturbation_mode": mode,
                "tip_score": tip_score,
                "rho_sem": rho_sem,
                "consistency_breakdown": score.summary_dict(),
                "notes": score.notes,
            }
        )
        print(
            f"Case {case_num:2d} (conv#{conv_idx}, {mode:10s}): "
            f"tip_score={tip_score:.4f}  rho_sem={rho_sem}  "
            f"contradictions={score.summary_dict()['contradiction_count']}"
        )

    n = len(results)
    print(f"\nn = {n} judge-scored pairs")
    correlation = p_value = None
    verdict = "INSUFFICIENT_SAMPLE"
    if n >= 3:
        tip_arr = [r["tip_score"] for r in results]
        rho_arr = [r["rho_sem"] for r in results]
        correlation, p_value = stats.spearmanr(rho_arr, tip_arr)
        print(f"Spearman rho = {correlation:.4f}")
        print(f"p-value      = {p_value:.4e}")
        THRESHOLD, MIN_N = 0.3, 30
        if n < MIN_N:
            verdict = "INSUFFICIENT_SAMPLE"
        elif correlation >= THRESHOLD:
            verdict = "SUPPORTED"
        else:
            verdict = "FALSIFIED"
        print(f"Verdict (n<{MIN_N}, directional only): {verdict}")

    out = {
        "data_source": "D:/mandala/Qwentest.txt, scored with grok_judge",
        "n_pairs_scored": n,
        "spearman_rho": correlation,
        "p_value": p_value,
        "verdict": verdict,
        "min_sample_size_note": "pre-registered n>=30 not reached (pilot, n=8) - directional only",
        "results": results,
    }
    out_path = Path(__file__).parent / "qwen_live_pilot_judged_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
