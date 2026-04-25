"""Critic: score draft outputs against constitution voice and quality rules.

Deterministic pattern matching for forbidden constructs, anti-patterns,
and invariant violations. No LLM calls. No side effects at module scope.
"""

from __future__ import annotations

import re
from typing import Any

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_models_spec = spec_from_file_location("models", Path(__file__).parent / "00-models.py")
_models = module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models)
CriticOutput = _models.CriticOutput


# Concrete patterns for each forbidden construct category.
_FORBIDDEN_PATTERNS: dict[str, list[str]] = {
    "hype_language": [
        r"\brevolution\w*\b", r"\bgroundbreaking\b", r"\bgame.changing\b",
        r"\bcutting.edge\b", r"\bparadigm\s+shift\b", r"\bunprecedented\b",
        r"\btransformative\b", r"\bdisruptive\b",
    ],
    "over_hedging": [
        r"\bI\s+think\s+maybe\b", r"\bperhaps\s+somewhat\b",
        r"\bit\s+might\s+possibly\b", r"\bcould\s+potentially\b",
        r"\bI\s+would\s+suggest\s+that\s+perhaps\b",
    ],
    "false_modesty": [
        r"\bjust\s+trying\s+to\b", r"\bonly\s+a\s+small\s+contribution\b",
        r"\bhumble\s+attempt\b", r"\bmodest\s+effort\b",
    ],
    "apologetic_framing": [
        r"\bsorry\s+to\s+bother\b", r"\bapologies\s+for\s+(the\s+)?delay\b",
        r"\bsorry\s+for\s+(the\s+)?(inconvenience|delay|trouble)\b",
        r"\bI\s+apologise\s+for\b",
    ],
    "empty_pleasantries": [
        r"\bhope\s+this\s+(email\s+)?finds\s+you\s+well\b",
        r"\bhope\s+you\s+are\s+(doing\s+)?well\b",
        r"\btrust\s+this\s+finds\s+you\b",
        r"\bhope\s+all\s+is\s+well\b",
    ],
    "emotional_reactivity": [
        r"\bfrankly\s+(I\s+am|I'm)\s+(frustrated|angry|disappointed)\b",
        r"\bI\s+resent\b", r"\bthis\s+is\s+(outrageous|unacceptable|ridiculous)\b",
    ],
    "ai_sounding": [
        r"\bdelve\b", r"\bleverage\b", r"\bharness\b", r"\bstreamline\b",
        r"\bit'?s\s+worth\s+noting\b", r"\bimportantly\b",
        r"\bin\s+today'?s\s+world\b", r"\bthe\s+landscape\s+of\b",
    ],
    "em_dash": [
        r"\u2014",  # em dash
        r"\u2013",  # en dash
    ],
}

# Patterns that indicate the output requires principal approval.
_APPROVAL_PATTERNS = [
    r"\b(send|submit|publish|post|forward|broadcast)\b",
    r"\bfinancial\b", r"\bgrant\b.*\bcommit\b",
    r"\bdecline\b.*\bsenior\b",
]


def critique(draft: str, config: dict[str, Any]) -> CriticOutput:
    """Score a draft output against constitution quality rules.

    Returns CriticOutput with pass/fail, score, and list of violations.
    """
    violations: list[str] = []

    for category, patterns in _FORBIDDEN_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, draft, re.IGNORECASE)
            if matches:
                violations.append(f"{category}: matched '{matches[0]}'")
                break  # one violation per category is enough

    # Check for overly long output (brevity check)
    word_count = len(draft.split())
    if word_count > 500:
        violations.append(f"brevity: draft is {word_count} words (aim for conciseness)")

    # Check principal approval requirement
    requires_approval = any(
        re.search(p, draft, re.IGNORECASE) for p in _APPROVAL_PATTERNS
    )

    # Score: start at 1.0, deduct per violation
    deduction_per_violation = 0.15
    score = max(0.0, 1.0 - len(violations) * deduction_per_violation)

    passed = score >= config.get("agents", {}).get("critic", {}).get("pass_threshold", 0.8)

    suggested_revision = None
    if violations:
        suggested_revision = "Remove or rephrase: " + "; ".join(violations)

    return CriticOutput(
        passed=passed,
        score=round(score, 2),
        violations=violations,
        suggested_revision=suggested_revision,
        requires_principal_approval=requires_approval,
    )
