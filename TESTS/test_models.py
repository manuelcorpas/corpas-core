"""Tests for Pydantic models."""

import pytest


def test_rule_evaluation_valid(models):
    r = models.RuleEvaluation(passed=True, rationale="Aligns with mission")
    assert r.passed is True
    assert r.rationale == "Aligns with mission"


def test_verdict_enum(models):
    assert models.Verdict.YES.value == "yes"
    assert models.Verdict.ESCALATE.value == "escalate"


def test_mode_enum(models):
    assert models.Mode.MISSION_CRITICAL.value == "mission_critical"
    assert models.Mode.DECLINE.value == "decline"


def test_critic_output_bounds(models):
    with pytest.raises(Exception):
        models.CriticOutput(passed=True, score=1.5)  # above 1.0


def test_govern_result_minimal(models):
    r = models.GovernResult(
        allowed=True,
        verdict=models.Verdict.YES,
        mode=models.Mode.MISSION_CRITICAL,
        rules_evaluated={
            "R1": models.RuleEvaluation(passed=True, rationale="ok"),
        },
        confidence=0.9,
        constitution_hash="abc123",
    )
    assert r.allowed is True
    assert r.confidence == 0.9


def test_ledger_entry_serialisation(models):
    entry = models.LedgerEntry(
        timestamp="2026-04-25T10:00:00Z",
        input_hash="abc",
        constitution_hash="def",
        mode_classification=models.Mode.CORE_RESPONSIBILITY,
        verdict=models.Verdict.YES,
        rules_evaluated={
            "R1": models.RuleEvaluation(passed=True, rationale="ok"),
        },
        confidence=0.85,
    )
    json_str = entry.model_dump_json()
    restored = models.LedgerEntry.model_validate_json(json_str)
    assert restored.confidence == 0.85
    assert restored.verdict == models.Verdict.YES
