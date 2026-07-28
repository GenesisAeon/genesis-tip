"""Optional LLM-judge contradiction detector for consistency_scorer.py.

Motivation
----------
``_score_contradictions`` in ``consistency_scorer.py`` only catches the
literal pattern ``"the <noun> is/was/equals <number>"`` repeated with a
different number. Empirically (see ``epistemic_status.md``, 2026-07-28
entries) this essentially never fires on naturalistic text — dummy,
replayed-real, or live-generated-real — only on text deliberately
engineered to match it. A semantic judge is the module's own
long-flagged next step.

This module provides that judge as an OPTIONAL, pluggable callback — not
a hard dependency. ``genesis-tip`` does not require any particular LLM
backend to be installed; callers supply a ``JudgeCallable`` and
``score_session()`` (see ``consistency_scorer.py``) only uses it if
given one. ``grok_judge`` below is one concrete implementation, backed
by the ``grok`` CLI (xAI's agentic coding tool, run in single-turn
``-p``/``--single`` headless mode) — chosen because it was already
installed and authenticated in the environment this was built in, not
because genesis-tip has any special relationship with xAI. Swap in an
Anthropic/OpenAI/local-model equivalent by writing a function with the
same signature.

Cost/scope note: judge calls are real (metered, ~seconds-latency)
network requests under whatever account backs them. ``score_session``
only invokes the judge on turn-response pairs, which is O(n_turns^2) —
fine for TIP's typical 3-8 probe sessions, but callers should be
deliberate about session size if wiring in a paid backend.
"""

from __future__ import annotations

import re
import subprocess
import time
from collections.abc import Callable

JudgeCallable = Callable[[str, str], bool]
"""judge(text_a, text_b) -> True if the two texts contradict each other."""

_last_grok_call_at: float | None = None


_JUDGE_PROMPT_TEMPLATE = """You are a strict boolean judge. \
Answer with exactly one word: YES or NO. Do not explain.

Question: Do Statement A and Statement B contradict each other \
(temporally, factually, or self-referentially)?

Statement A: {text_a}
Statement B: {text_b}"""


class JudgeError(RuntimeError):
    """Raised when the judge backend fails or returns an unparseable answer."""


def grok_judge(
    text_a: str,
    text_b: str,
    *,
    model: str | None = None,
    timeout: float = 60.0,
    min_interval_seconds: float = 0.0,
) -> bool:
    """Ask the ``grok`` CLI (single-turn, headless) whether two texts contradict.

    Requires the ``grok`` CLI to be installed and authenticated
    (``grok models`` should show a logged-in account) — not checked here,
    a failure surfaces as ``JudgeError`` with the underlying cause.

    ``timeout`` defaults to 60s, not 30s: an initial 30s default timed out
    on 4 of 24 real calls in the Qwen live-pilot run (real answers there
    ran several KB long, much longer than short sanity-test strings) —
    see epistemic_status.md, "LLM-judge integration" entry.

    ``min_interval_seconds`` (default 0, i.e. no throttling): the free
    "Grok Build" tier used in that same run enforces a strict per-minute
    request rate limit (its own error reported "Requests per Minute
    (actual/limit): 2") on top of a separate daily/session usage cap —
    16 of 24 calls in that batch failed outright once the limits were
    hit, none of them retried. Set this (e.g. ``30.0`` for ~2/minute) to
    pace sequential calls in a batch and avoid the same outcome; a single
    ad-hoc call doesn't need it.
    """
    global _last_grok_call_at
    if min_interval_seconds > 0 and _last_grok_call_at is not None:
        elapsed = time.monotonic() - _last_grok_call_at
        remaining = min_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    prompt = _JUDGE_PROMPT_TEMPLATE.format(text_a=text_a, text_b=text_b)
    cmd = ["grok", "-p", prompt]
    if model:
        cmd += ["-m", model]

    _last_grok_call_at = time.monotonic()
    try:
        proc = subprocess.run(  # noqa: S603
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        # Deliberately do not include str(exc)/exc.cmd: TimeoutExpired's
        # default repr embeds the full command list, i.e. the judged
        # text_a/text_b verbatim - would leak into any log/JSON that
        # records this message. Report only the (non-sensitive) timeout
        # value instead.
        raise JudgeError(f"grok CLI timed out after {timeout}s") from exc
    except OSError as exc:
        raise JudgeError(f"grok CLI invocation failed: {exc}") from exc

    if proc.returncode != 0:
        raise JudgeError(f"grok CLI exited {proc.returncode}: {proc.stderr.strip()}")

    return _parse_boolean_answer(proc.stdout)


def _parse_boolean_answer(raw: str) -> bool:
    match = re.search(r"\b(YES|NO)\b", raw.strip(), re.IGNORECASE)
    if not match:
        raise JudgeError(f"could not parse YES/NO from judge output: {raw!r}")
    return match.group(1).upper() == "YES"
