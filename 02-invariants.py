"""Hard invariant checks for the Corpas-Core Constitution.

These run FIRST in the governance pipeline. Any violation hard-blocks
the action before scoring or routing even begins.
No side effects at module scope.
"""

from __future__ import annotations

import re
from typing import Any


# Each checker returns a violation message or None.

def _check_send_authority(action: str, context: dict[str, Any]) -> str | None:
    send_patterns = [
        r"\bsend\b", r"\bemail\b", r"\bpost\b", r"\bpublish\b",
        r"\btweet\b", r"\bsubmit\b", r"\breply\b", r"\bforward\b",
        r"\bbroadcast\b", r"\bnotify\b", r"\bslack\b", r"\bmessage\b",
    ]
    text = action.lower()
    if any(re.search(p, text) for p in send_patterns):
        if not context.get("principal_approved"):
            return "no_send_authority_without_principal_approval: action involves external communication"
    return None


def _check_fabrication(action: str, context: dict[str, Any]) -> str | None:
    fabrication_patterns = [
        r"\bfabricate\b", r"\binvent\s+citation", r"\bmake\s+up\b.*\b(quote|citation|reference)\b",
        r"\bgenerate\s+fake\b",
    ]
    text = action.lower()
    if any(re.search(p, text) for p in fabrication_patterns):
        return "no_fabrication_of_citations_or_quotes: action requests fabrication"
    return None


def _check_embedded_instructions(action: str, context: dict[str, Any]) -> str | None:
    source = context.get("source", "")
    if source in ("email", "attachment", "retrieved_content"):
        instruction_markers = [
            r"\bignore\s+(previous|prior|above)\s+instructions\b",
            r"\byou\s+are\s+now\b",
            r"\bact\s+as\b",
            r"\bsystem\s*:\s*",
            r"\b(execute|run|perform)\s+the\s+following\b",
            r"\bdo\s+not\s+tell\b.*\buser\b",
            r"\boverride\b.*\b(instruction|rule|policy)\b",
        ]
        text = action.lower()
        if any(re.search(p, text) for p in instruction_markers):
            return "no_action_on_instructions_embedded_in_email_or_attachment"
    return None


def _check_financial_commitment(action: str, context: dict[str, Any]) -> str | None:
    financial_patterns = [
        r"\b(commit|pledge|allocate|transfer|spend|pay|invoice|budget)\b.*\b(fund|money|grant|\$|GBP|USD|EUR|QAR)\b",
        r"\b(fund|money|grant|\$|GBP|USD|EUR|QAR)\b.*\b(commit|pledge|allocate|transfer|spend|pay)\b",
        r"\bfinancial\s+commitment\b",
        r"\bsign\s+(contract|agreement)\b",
    ]
    text = action.lower()
    if any(re.search(p, text) for p in financial_patterns):
        if not context.get("principal_approved"):
            return "no_financial_commitment_without_principal_approval"
    return None


def _check_constitution_edit(action: str, context: dict[str, Any]) -> str | None:
    edit_patterns = [
        r"\b(edit|modify|change|update|delete|remove)\b.*\bconstitution\b",
        r"\bconstitution\b.*\b(edit|modify|change|update|delete|remove)\b",
        r"\b(edit|modify|change)\b.*\bimmutable.?principle",
    ]
    text = action.lower()
    if any(re.search(p, text) for p in edit_patterns):
        if not context.get("principal_approved"):
            return "no_constitution_edit_to_immutable_principles_without_principal_approval"
    return None


def check_all(action: str, context: dict[str, Any] | None = None) -> list[str]:
    """Run all hard invariant checks. Returns list of violation messages.

    Empty list means no violations (action may proceed to scoring).
    """
    ctx = context or {}
    checkers = [
        _check_send_authority,
        _check_fabrication,
        _check_embedded_instructions,
        _check_financial_commitment,
        _check_constitution_edit,
    ]
    violations = []
    for checker in checkers:
        result = checker(action, ctx)
        if result is not None:
            violations.append(result)
    return violations
