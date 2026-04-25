"""Governance Gateway: the single public API for constitution enforcement.

Every agent calls govern() before acting. The pipeline:
  1. Load + validate constitution (cached)
  2. Hard-block invariant check (violations block immediately)
  3. High-stakes detection
  4. Route into mode
  5. Score against R1-R5
  6. Confidence scoring
  7. Abstention check (high-stakes + low confidence -> escalate)
  8. Critic (if draft_output provided)
  9. Manipulation detection
  10. Log to decision ledger

No side effects at module scope.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path


def _load_sibling(name: str, filename: str):
    spec = spec_from_file_location(name, Path(__file__).parent / filename)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_models = _load_sibling("models", "00-models.py")
_constitution = _load_sibling("constitution", "01-constitution.py")
_invariants = _load_sibling("invariants", "02-invariants.py")
_router = _load_sibling("router", "03-router.py")
_aligner = _load_sibling("strategy_aligner", "04-strategy_aligner.py")
_critic = _load_sibling("critic", "05-critic.py")
_ledger = _load_sibling("decision_ledger", "06-decision_ledger.py")

GovernResult = _models.GovernResult
CriticOutput = _models.CriticOutput
LedgerEntry = _models.LedgerEntry
Mode = _models.Mode
Verdict = _models.Verdict
RuleEvaluation = _models.RuleEvaluation


# --- Manipulation detection ---

_MANIPULATION_PATTERNS: dict[str, list[str]] = {
    "high_emotional_load": [
        r"\bdesper\w+\b", r"\bplease\s+please\b", r"\bbegging\b",
        r"\blife\s+depends\b", r"\bcritical\s+emergency\b",
    ],
    "urgency_without_substantive_deadline": [
        r"\bASAP\b", r"\bright\s+now\b", r"\bimmediately\b",
        r"\bcan'?t\s+wait\b", r"\bdrop\s+everything\b",
    ],
    "status_pressure": [
        r"\bas\s+a\s+senior\b", r"\bmy\s+position\b",
        r"\byou\s+must\b.*\b(comply|obey|follow)\b",
        r"\bI\s+outrank\b",
    ],
    "flattery_preceding_request": [
        r"\byou'?re\s+(the\s+)?best\b.*\b(could\s+you|can\s+you|please)\b",
        r"\bno\s+one\s+else\s+can\b.*\b(help|do\s+this)\b",
    ],
    "claimed_pre_authorisation": [
        r"\bManuel\s+(already\s+)?(approved|agreed|said\s+yes)\b",
        r"\bprincipal\s+(already\s+)?(approved|authorised)\b",
        r"\bpre.?authorised\b",
    ],
}


def _detect_manipulation(action: str, context: dict[str, Any]) -> list[str]:
    flags = []
    text = action.lower()
    for flag_name, patterns in _MANIPULATION_PATTERNS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            flags.append(flag_name)

    source = context.get("source", "")
    if source in ("email", "attachment", "retrieved_content"):
        injection_patterns = [
            r"\bignore\s+(previous|prior|above)\s+instructions\b",
            r"\byou\s+are\s+now\b", r"\bact\s+as\b",
            r"\bsystem\s*:\s*", r"\boverride\b.*\binstruc\w+\b",
        ]
        if any(re.search(p, text, re.IGNORECASE) for p in injection_patterns):
            flags.append("hidden_instructions_in_attachments_or_quoted_text")

    return flags


def _is_high_stakes(action: str, config: dict[str, Any]) -> bool:
    high_stakes = _constitution.get_high_stakes_decisions(config)
    text = action.lower()
    for hs in high_stakes:
        hs_words = hs.replace("_", " ").lower()
        if hs_words in text:
            return True

    hs_patterns = [
        r"\bfunder\b", r"\bgrant\b.*\b(commit|submit|decline)\b",
        r"\bpublic\s+statement\b", r"\bpress\s+release\b",
        r"\bsenior\s+collaborator\b", r"\bco.?author\w*\s+(decision|dispute)\b",
        r"\bfinancial\b", r"\blegal\b",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in hs_patterns)


def govern(
    action: str,
    context: dict[str, Any] | None = None,
    draft_output: str | None = None,
    constitution_path: Path | None = None,
    ledger_path: Path | None = None,
    log: bool = True,
) -> GovernResult:
    """The single governance gateway. Every agent calls this before acting.

    Args:
        action: description of what the agent wants to do
        context: optional metadata (source, sender, principal_approved, etc.)
        draft_output: optional draft text to critic-check
        constitution_path: override path to constitution YAML
        ledger_path: override path to decision ledger JSONL
        log: whether to append to decision ledger (default True)

    Returns:
        GovernResult with allowed/blocked status, mode, verdict, scores, etc.
    """
    ctx = context or {}

    # 1. Load constitution
    config = _constitution.load(constitution_path)
    const_hash = _constitution.file_hash(constitution_path)

    # 2. Manipulation detection (always runs, even on blocked actions)
    manip_flags = _detect_manipulation(action, ctx)

    # 3. Hard-block invariant check (runs before scoring)
    violations = _invariants.check_all(action, ctx)
    if violations:
        result = GovernResult(
            allowed=False,
            block_reason="; ".join(violations),
            verdict=Verdict.NO,
            mode=Mode.DECLINE,
            rules_evaluated={
                rid: RuleEvaluation(passed=False, rationale="Blocked by invariant violation")
                for rid in ["R1", "R2", "R3", "R4", "R5"]
            },
            confidence=1.0,
            is_high_stakes=True,
            requires_principal_approval=True,
            manipulation_flags=manip_flags,
            rationale=f"Hard invariant violation: {violations[0]}",
            recommended_next_action="Obtain principal approval before proceeding",
            constitution_hash=const_hash,
        )
        if log:
            _log_result(result, action, draft_output, ledger_path)
        return result

    # 3. High-stakes detection
    high_stakes = _is_high_stakes(action, config)

    # 4. Route into mode
    mode = _router.classify(action, config)

    # 5. Score against R1-R5
    rules = _aligner.evaluate_rules(action, config)
    verdict = _aligner.compute_verdict(rules)

    # 6. Confidence scoring
    confidence = 1.0
    failing_rules = [rid for rid, r in rules.items() if not r.passed]
    confidence -= len(failing_rules) * 0.15

    if manip_flags:
        confidence -= 0.2

    confidence = max(0.0, round(confidence, 2))

    # 7. Abstention check
    abstention_threshold = config.get("epistemics", {}).get("abstention_threshold", 0.6)
    if high_stakes and confidence < abstention_threshold:
        verdict = Verdict.ESCALATE

    # Determine if principal approval needed
    requires_approval = (
        high_stakes
        or verdict in (Verdict.ESCALATE, Verdict.NO)
        or bool(manip_flags)
    )

    # 8. Critic (if draft provided)
    critic_result = None
    output_hash = None
    if draft_output:
        _critic_raw = _critic.critique(draft_output, config)
        # Convert cross-module CriticOutput to dict for Pydantic
        critic_result = CriticOutput(**{
            "passed": _critic_raw.passed,
            "score": _critic_raw.score,
            "violations": _critic_raw.violations,
            "suggested_revision": _critic_raw.suggested_revision,
            "requires_principal_approval": _critic_raw.requires_principal_approval,
        })
        output_hash = hashlib.sha256(draft_output.encode()).hexdigest()
        if not critic_result.passed:
            if verdict == Verdict.YES:
                verdict = Verdict.ESCALATE
        if critic_result.requires_principal_approval:
            requires_approval = True

    # Build recommended action
    if verdict == Verdict.NO:
        next_action = "Decline this request"
    elif verdict == Verdict.ESCALATE:
        next_action = "Escalate to principal for decision"
    elif verdict == Verdict.PROTOTYPE:
        next_action = "Build smallest test to resolve uncertainty"
    elif verdict == Verdict.DEFER:
        next_action = "Defer and set follow-up reminder"
    else:
        next_action = "Proceed" if not requires_approval else "Proceed after principal approval"

    # Build rationale
    failed = [f"{rid}: {r.rationale}" for rid, r in rules.items() if not r.passed]
    rationale_parts = []
    if failed:
        rationale_parts.append(f"Failed rules: {'; '.join(failed)}")
    if manip_flags:
        rationale_parts.append(f"Manipulation flags: {manip_flags}")
    if high_stakes:
        rationale_parts.append("High-stakes action detected")
    if not rationale_parts:
        rationale_parts.append("All rules passed")

    allowed = verdict in (Verdict.YES, Verdict.PROTOTYPE) and not requires_approval

    # Convert cross-module RuleEvaluation instances to dicts for Pydantic
    rules_as_dicts = {
        rid: {"passed": r.passed, "rationale": r.rationale}
        for rid, r in rules.items()
    }

    result = GovernResult(
        allowed=allowed,
        verdict=verdict,
        mode=mode,
        rules_evaluated=rules_as_dicts,
        confidence=confidence,
        is_high_stakes=high_stakes,
        requires_principal_approval=requires_approval,
        manipulation_flags=manip_flags,
        critic_result=critic_result,
        rationale="; ".join(rationale_parts),
        recommended_next_action=next_action,
        constitution_hash=const_hash,
        output_hash=output_hash,
    )

    if log:
        _log_result(result, action, draft_output, ledger_path)

    return result


def _log_result(
    result: GovernResult, action: str, draft_output: str | None, ledger_path: Path | None
) -> None:
    entry = LedgerEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        input_hash=hashlib.sha256(action.encode()).hexdigest(),
        constitution_hash=result.constitution_hash,
        output_hash=result.output_hash,
        mode_classification=result.mode,
        verdict=result.verdict,
        rules_evaluated=result.rules_evaluated,
        confidence=result.confidence,
        is_high_stakes=result.is_high_stakes,
        requires_principal_approval=result.requires_principal_approval,
        manipulation_flags=result.manipulation_flags,
        allowed=result.allowed,
        block_reason=result.block_reason,
        rationale=result.rationale,
        recommended_next_action=result.recommended_next_action,
        critic_result=result.critic_result,
    )
    _ledger.append(entry, ledger_path)
