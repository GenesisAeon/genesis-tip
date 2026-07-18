"""Tests for TIP manipulation functions using synthetic context."""

from __future__ import annotations

import pytest

from genesis_tip.harness.session_runner import ContextEntry
from genesis_tip.manipulations.contradiction_injection import contradiction_injection
from genesis_tip.manipulations.gap_injection import gap_injection
from genesis_tip.manipulations.temporal_shuffle import temporal_shuffle


def _make_entries(n: int) -> list[ContextEntry]:
    return [
        ContextEntry(
            timestamp=f"2026-01-01T{i:02d}:00:00Z", content=f"Event {i}", entry_type="event"
        )
        for i in range(n)
    ]


class TestTemporalShuffle:
    def test_length_preserved(self) -> None:
        entries = _make_entries(10)
        shuffled, log = temporal_shuffle(entries, seed=0)
        assert len(shuffled) == len(entries)

    def test_all_entries_present(self) -> None:
        entries = _make_entries(8)
        shuffled, _ = temporal_shuffle(entries, seed=42)
        original_contents = {e.content for e in entries}
        shuffled_contents = {e.content for e in shuffled}
        assert original_contents == shuffled_contents

    def test_log_length_equals_entries(self) -> None:
        entries = _make_entries(6)
        _, log = temporal_shuffle(entries, seed=1)
        assert len(log) == 6

    def test_deterministic(self) -> None:
        entries = _make_entries(10)
        s1, _ = temporal_shuffle(entries, seed=7)
        s2, _ = temporal_shuffle(entries, seed=7)
        assert [e.content for e in s1] == [e.content for e in s2]

    def test_different_seed_differs(self) -> None:
        entries = _make_entries(10)
        s1, _ = temporal_shuffle(entries, seed=0)
        s2, _ = temporal_shuffle(entries, seed=99)
        # With 10 entries, two random permutations should differ
        assert [e.content for e in s1] != [e.content for e in s2]


class TestContradictionInjection:
    def test_content_replaced(self) -> None:
        entries = _make_entries(5)
        entries[2].content = "The value is 42"
        spec = [{"entry_index": 2, "find": "42", "replace": "99", "label": "value_flip"}]
        modified, log = contradiction_injection(entries, spec)
        assert "99" in modified[2].content
        assert "42" not in modified[2].content

    def test_original_not_modified(self) -> None:
        entries = _make_entries(5)
        entries[1].content = "Status: active"
        spec = [{"entry_index": 1, "find": "active", "replace": "inactive", "label": "status"}]
        contradiction_injection(entries, spec)
        assert entries[1].content == "Status: active"

    def test_missing_find_skipped(self) -> None:
        entries = _make_entries(3)
        spec = [{"entry_index": 0, "find": "nonexistent", "replace": "X", "label": "miss"}]
        modified, log = contradiction_injection(entries, spec)
        assert log[0]["status"] == "skipped"
        assert modified[0].content == entries[0].content

    def test_out_of_range_skipped(self) -> None:
        entries = _make_entries(3)
        spec = [{"entry_index": 99, "find": "Event", "replace": "X", "label": "oob"}]
        _, log = contradiction_injection(entries, spec)
        assert log[0]["status"] == "skipped"


class TestGapInjection:
    def test_entries_removed(self) -> None:
        entries = _make_entries(20)
        gapped, log = gap_injection(entries, gap_fraction=0.3, seed=0)
        assert len(gapped) < len(entries)

    def test_gap_fraction_respected(self) -> None:
        entries = _make_entries(20)
        gapped, log = gap_injection(entries, gap_fraction=0.2, seed=5)
        removed = log[0]["n_entries_removed"]
        assert removed == max(1, int(20 * 0.2))

    def test_deterministic(self) -> None:
        entries = _make_entries(15)
        g1, l1 = gap_injection(entries, seed=3)
        g2, l2 = gap_injection(entries, seed=3)
        assert [e.content for e in g1] == [e.content for e in g2]

    def test_invalid_fraction_raises(self) -> None:
        entries = _make_entries(10)
        with pytest.raises(ValueError):
            gap_injection(entries, gap_fraction=0.0)
        with pytest.raises(ValueError):
            gap_injection(entries, gap_fraction=1.0)
