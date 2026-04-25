"""Tests for decision ledger append/read."""


def test_append_and_read(ledger_mod, models, tmp_ledger):
    entry = models.LedgerEntry(
        timestamp="2026-04-25T10:00:00Z",
        input_hash="abc123",
        constitution_hash="def456",
        mode_classification=models.Mode.MISSION_CRITICAL,
        verdict=models.Verdict.YES,
        rules_evaluated={
            "R1": models.RuleEvaluation(passed=True, rationale="ok"),
        },
        confidence=0.9,
    )
    ledger_mod.append(entry, tmp_ledger)
    entries = ledger_mod.read_all(tmp_ledger)
    assert len(entries) == 1
    assert entries[0].verdict == models.Verdict.YES


def test_append_only(ledger_mod, models, tmp_ledger):
    for i in range(3):
        entry = models.LedgerEntry(
            timestamp=f"2026-04-25T1{i}:00:00Z",
            input_hash=f"hash_{i}",
            constitution_hash="const",
            mode_classification=models.Mode.CORE_RESPONSIBILITY,
            verdict=models.Verdict.YES,
            rules_evaluated={},
            confidence=0.8,
        )
        ledger_mod.append(entry, tmp_ledger)
    assert ledger_mod.count(tmp_ledger) == 3


def test_read_last(ledger_mod, models, tmp_ledger):
    for i in range(5):
        entry = models.LedgerEntry(
            timestamp=f"2026-04-25T1{i}:00:00Z",
            input_hash=f"hash_{i}",
            constitution_hash="const",
            mode_classification=models.Mode.CORE_RESPONSIBILITY,
            verdict=models.Verdict.YES,
            rules_evaluated={},
            confidence=0.8,
        )
        ledger_mod.append(entry, tmp_ledger)
    recent = ledger_mod.read_last(2, tmp_ledger)
    assert len(recent) == 2
    assert recent[-1].input_hash == "hash_4"


def test_read_empty(ledger_mod, tmp_path):
    empty = tmp_path / "empty.jsonl"
    assert ledger_mod.read_all(empty) == []
    assert ledger_mod.count(empty) == 0
