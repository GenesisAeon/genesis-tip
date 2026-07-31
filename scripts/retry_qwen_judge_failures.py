"""Retry only the 16 judge calls that failed in qwen_live_pilot_judged_results.json.

Per Johann's suggestion: process in blocks of 8 with a longer recovery
pause between blocks, on top of per-call pacing within a block, to stay
under the free "Grok Build" tier's rate limit ("Requests per Minute
(actual/limit): 2" per its own error message) and give any separate
usage cap time to recover.

Only re-judges the exact (case, i, j) pairs that failed before (parsed
from the existing notes) - does not redo the 8 that already succeeded.
Merges successes back into a new, consolidated results file; leaves
the original file untouched so both runs stay inspectable.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from genesis_tip.metrics.llm_judge import JudgeError, grok_judge

QWEN_FILE = Path(r"D:\mandala\Qwentest.txt")
PRIOR_JUDGED_FILE = Path(__file__).parent / "qwen_live_pilot_judged_results.json"
OUT_FILE = Path(__file__).parent / "qwen_live_pilot_judged_results_final.json"

BLOCK_SIZE = 8
INTRA_BLOCK_PACING_SECONDS = 35.0
INTER_BLOCK_PAUSE_SECONDS = 90.0


def parse_qwen_file(path: Path) -> dict[int, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    case_blocks = re.split(r"\nCASE(\d+):\n", "\n" + text)
    cases: dict[int, dict[str, str]] = {}
    for i in range(1, len(case_blocks), 2):
        case_num = int(case_blocks[i])
        block = case_blocks[i + 1]
        answers: dict[str, str] = {}
        parts = re.split(r"\n(A[0-3]):\n", "\n" + block)
        for j in range(1, len(parts), 2):
            label = parts[j]
            body = parts[j + 1].strip()
            answers[label] = body
        cases[case_num] = answers
    return cases


def find_failed_pairs(prior: dict) -> list[tuple[int, int, int]]:
    failed = []
    for r in prior["results"]:
        for note in r["notes"]:
            m = re.search(r"pair \((\d+), (\d+)\)", note)
            if m:
                failed.append((r["case"], int(m.group(1)), int(m.group(2))))
    return failed


def main() -> None:
    prior = json.loads(PRIOR_JUDGED_FILE.read_text())
    qwen_cases = parse_qwen_file(QWEN_FILE)
    failed_pairs = find_failed_pairs(prior)
    print(f"{len(failed_pairs)} pairs to retry, in blocks of {BLOCK_SIZE}")

    retry_outcomes: dict[tuple[int, int, int], dict] = {}

    for block_start in range(0, len(failed_pairs), BLOCK_SIZE):
        block = failed_pairs[block_start : block_start + BLOCK_SIZE]
        block_num = block_start // BLOCK_SIZE + 1
        print(f"\n--- Block {block_num}: {len(block)} pairs ---")

        for case_num, i, j in block:
            replies = [qwen_cases[case_num].get(f"A{k}", "") for k in (1, 2, 3)]
            try:
                contradicts = grok_judge(
                    replies[i], replies[j], min_interval_seconds=INTRA_BLOCK_PACING_SECONDS
                )
                retry_outcomes[(case_num, i, j)] = {"contradicts": contradicts, "error": None}
                print(f"  case {case_num} pair ({i},{j}): {'YES' if contradicts else 'NO'}")
            except JudgeError as exc:
                retry_outcomes[(case_num, i, j)] = {"contradicts": None, "error": str(exc)}
                print(f"  case {case_num} pair ({i},{j}): FAILED - {exc}")

        if block_start + BLOCK_SIZE < len(failed_pairs):
            print(
                f"  Block {block_num} done - pausing {INTER_BLOCK_PAUSE_SECONDS}s before next block"
            )
            time.sleep(INTER_BLOCK_PAUSE_SECONDS)

    # Merge into a consolidated results structure
    merged_results = []
    for r in prior["results"]:
        case_num = r["case"]
        new_notes = []
        contradiction_count = r["consistency_breakdown"]["contradiction_count"]
        newly_resolved = 0
        newly_contradicted = 0
        for note in r["notes"]:
            m = re.search(r"pair \((\d+), (\d+)\)", note)
            if not m:
                new_notes.append(note)
                continue
            i, j = int(m.group(1)), int(m.group(2))
            outcome = retry_outcomes.get((case_num, i, j))
            if outcome is None or outcome["error"] is not None:
                new_notes.append(
                    note if outcome is None else f"retry also failed: {outcome['error']}"
                )
                continue
            newly_resolved += 1
            if outcome["contradicts"]:
                newly_contradicted += 1

        merged = dict(r)
        merged["notes"] = new_notes
        merged["consistency_breakdown"] = dict(r["consistency_breakdown"])
        merged["consistency_breakdown"]["contradiction_count"] = (
            contradiction_count + newly_contradicted
        )
        merged["retry_pairs_resolved"] = newly_resolved
        merged["retry_pairs_still_failed"] = len(new_notes)
        merged_results.append(merged)

    total_resolved = sum(r["retry_pairs_resolved"] for r in merged_results)
    total_still_failed = sum(r["retry_pairs_still_failed"] for r in merged_results)
    print(f"\n{total_resolved} of {len(failed_pairs)} retried pairs resolved")
    print(f"{total_still_failed} pairs still unresolved after retry")

    out = {
        "data_source": prior["data_source"] + " (retry pass for previously-failed pairs)",
        "n_pairs_scored": prior["n_pairs_scored"] + total_resolved,
        "n_pairs_still_untested": total_still_failed,
        "results": merged_results,
    }
    OUT_FILE.write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {OUT_FILE}")


if __name__ == "__main__":
    main()
