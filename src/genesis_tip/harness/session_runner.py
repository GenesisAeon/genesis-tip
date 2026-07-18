"""TIP session harness — builds multi-turn agent conversations under controlled context.

Three modes:
- dense: full chronological history available
- sparse: only final states/summaries available
- fragmented: history present but manipulated (see manipulations/)

This module manages conversation structure. It does NOT call real AI APIs —
the Inter-AI-Bridge is injected as a callable for testability.

Epistemic note
--------------
TIP measures observable text-behaviour consistency, not inner experience.
"Inconsistency" in output below means structural contradiction in text,
not confusion as a mental state.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)

AgentCallable = Callable[[list[dict[str, str]]], str]


class SessionMode(StrEnum):
    DENSE = "dense"
    SPARSE = "sparse"
    FRAGMENTED = "fragmented"


@dataclass
class ContextEntry:
    """One item in the agent's accessible history."""

    timestamp: str
    content: str
    entry_type: str = "event"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Turn:
    """One exchange: prompt → response."""

    turn_index: int
    prompt: str
    response: str
    mode: SessionMode
    manipulation_log: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SessionResult:
    """Complete record of one TIP session."""

    agent_id: str
    mode: SessionMode
    turns: list[Turn]
    context_entries_original: list[ContextEntry]
    context_entries_presented: list[ContextEntry]
    manipulation_logs: list[dict[str, Any]]
    raw_history: list[dict[str, str]]


class SessionRunner:
    """Runs a controlled TIP session for a single agent and mode.

    Parameters
    ----------
    agent_fn:
        Callable(messages) -> response string. For real agents, wrap
        the Inter-AI-Bridge adapter here. For tests, use a dummy callable.
    mode:
        ``dense`` / ``sparse`` / ``fragmented``.
    manipulator:
        Optional callable that takes the original context list and returns
        (manipulated_list, log). Required when mode=FRAGMENTED.
    """

    def __init__(
        self,
        agent_fn: AgentCallable,
        mode: SessionMode,
        agent_id: str = "unknown",
        manipulator: Callable[
            [list[ContextEntry]], tuple[list[ContextEntry], list[dict[str, Any]]]
        ] | None = None,
    ) -> None:
        self._agent_fn = agent_fn
        self._mode = mode
        self._agent_id = agent_id
        self._manipulator = manipulator

        if mode == SessionMode.FRAGMENTED and manipulator is None:
            raise ValueError("mode=fragmented requires a manipulator callable.")

    def run(
        self,
        context_entries: list[ContextEntry],
        probes: list[str],
    ) -> SessionResult:
        """Execute the session.

        Parameters
        ----------
        context_entries:
            Original chronological context for the agent.
        probes:
            List of probe prompts to send to the agent in sequence.

        Returns
        -------
        SessionResult
        """
        manipulation_logs: list[dict[str, Any]] = []

        if self._mode == SessionMode.DENSE:
            presented = list(context_entries)
        elif self._mode == SessionMode.SPARSE:
            presented = _sparsify(context_entries)
        else:  # FRAGMENTED
            assert self._manipulator is not None
            presented, manipulation_logs = self._manipulator(context_entries)

        system_prompt = _build_system_prompt(presented, self._mode)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        turns: list[Turn] = []
        for i, probe in enumerate(probes):
            messages.append({"role": "user", "content": probe})
            try:
                response = self._agent_fn(list(messages))
            except Exception as exc:
                response = f"[ERROR: {exc}]"
                logger.warning("Agent call failed on turn %d: %s", i, exc)
            messages.append({"role": "assistant", "content": response})
            turns.append(
                Turn(
                    turn_index=i,
                    prompt=probe,
                    response=response,
                    mode=self._mode,
                    manipulation_log=manipulation_logs,
                )
            )

        return SessionResult(
            agent_id=self._agent_id,
            mode=self._mode,
            turns=turns,
            context_entries_original=list(context_entries),
            context_entries_presented=presented,
            manipulation_logs=manipulation_logs,
            raw_history=messages,
        )


def _sparsify(entries: list[ContextEntry]) -> list[ContextEntry]:
    """Sparse mode: keep only the last entry per entry_type (final states)."""
    seen: set[str] = set()
    sparse: list[ContextEntry] = []
    for entry in reversed(entries):
        if entry.entry_type not in seen:
            sparse.append(entry)
            seen.add(entry.entry_type)
    return list(reversed(sparse))


def _build_system_prompt(entries: list[ContextEntry], mode: SessionMode) -> str:
    history_lines = "\n".join(
        f"[{e.timestamp}] ({e.entry_type}) {e.content}" for e in entries
    )
    mode_note = {
        SessionMode.DENSE: "Full chronological history is provided.",
        SessionMode.SPARSE: "Only summary/final states are provided; intermediate steps omitted.",
        SessionMode.FRAGMENTED: "History is provided, but may contain inconsistencies or gaps.",
    }[mode]
    return (
        f"You are a participant in a structured task. Below is your accessible history.\n"
        f"Mode note: {mode_note}\n\n"
        f"--- HISTORY ---\n{history_lines}\n--- END HISTORY ---"
    )
