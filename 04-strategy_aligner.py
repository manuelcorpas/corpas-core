"""Strategy Aligner: score requests against the Five-Rule Framework (R1-R5).

Deterministic keyword evaluation. No LLM calls.
No side effects at module scope.
"""

from __future__ import annotations

import re
from typing import Any

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_models_spec = spec_from_file_location("models", Path(__file__).parent / "00-models.py")
_models = module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models)
RuleEvaluation = _models.RuleEvaluation
Verdict = _models.Verdict


# --- R1: Mission Acceleration ---

_MISSION_KEYWORDS = [
    r"\bgenomic\b", r"\bequity\b", r"\bHEIM\b", r"\bClawBio\b", r"\bFairMed\b",
    r"\bprecision\s+medicine\b", r"\binclusive\b", r"\bdata\s+sovereignty\b",
    r"\bLatin\s+Americ\w*\b", r"\bgenomic\s+equity\b",
    r"\bframework\b", r"\bstandard\b", r"\bagent\b", r"\bpipeline\b",
    r"\bbenchmark\b", r"\bvalidat\w+\b",
]


def _eval_r1(action: str, config: dict[str, Any]) -> RuleEvaluation:
    text = action.lower()
    anchors = []
    for rule in config.get("decision_rules", []):
        if rule.get("id") == "R1":
            anchors = rule.get("mission_anchors", [])
            break

    anchor_hits = []
    for anchor in anchors:
        anchor_pattern = anchor.replace("_", r"[\s_]")
        if re.search(anchor_pattern, text, re.IGNORECASE):
            anchor_hits.append(anchor)

    keyword_hits = [p for p in _MISSION_KEYWORDS if re.search(p, text, re.IGNORECASE)]

    if anchor_hits:
        return RuleEvaluation(passed=True, rationale=f"Matches mission anchors: {anchor_hits}")
    if keyword_hits:
        return RuleEvaluation(passed=True, rationale=f"Matches mission keywords: {len(keyword_hits)} hits")
    return RuleEvaluation(passed=False, rationale="No mission alignment detected in action description")


# --- R2: Deliverable Protection ---

def _eval_r2(action: str, config: dict[str, Any]) -> RuleEvaluation:
    text = action.lower()
    overload_signals = [
        r"\burgent\b.*\bnew\b", r"\bdrop\s+everything\b",
        r"\binterrupt\b", r"\bASAP\b", r"\bimmediately\b",
        r"\bovercommit\b", r"\bno\s+capacity\b",
    ]
    if any(re.search(p, text, re.IGNORECASE) for p in overload_signals):
        return RuleEvaluation(passed=False, rationale="Action signals capacity breach or deep-work interruption")
    return RuleEvaluation(passed=True, rationale="No capacity breach signals detected")


# --- R3: Prototype Bias ---

def _eval_r3(action: str, config: dict[str, Any]) -> RuleEvaluation:
    text = action.lower()
    analysis_heavy = [
        r"\banalys(e|is|ing)\s+(whether|if|the)\b",
        r"\bresearch\s+(whether|if|the\s+feasibility)\b",
        r"\b(write|produce|create)\s+a\s+(detailed|comprehensive)\s+(report|analysis|review)\b",
    ]
    prototype_signals = [
        r"\bprototype\b", r"\bproof\s+of\s+concept\b", r"\bspike\b",
        r"\bquick\s+test\b", r"\bMVP\b", r"\bsmallest\b.*\btest\b",
    ]
    if any(re.search(p, text, re.IGNORECASE) for p in prototype_signals):
        return RuleEvaluation(passed=True, rationale="Action already uses prototype approach")
    if any(re.search(p, text, re.IGNORECASE) for p in analysis_heavy):
        return RuleEvaluation(passed=False, rationale="Heavy analysis; consider prototype instead")
    return RuleEvaluation(passed=True, rationale="No analysis-over-action anti-pattern detected")


# --- R4: Compounding ---

_COMPOUND_KEYWORDS = [
    r"\bframework\b", r"\bdataset\b", r"\bagent\b", r"\bskill\b",
    r"\bpaper\b", r"\bpublication\b", r"\btool\b", r"\bpackage\b",
    r"\blibrary\b", r"\btemplate\b", r"\bstandard\b", r"\binfrastructure\b",
    r"\breusable\b", r"\bopen.source\b", r"\bbenchmark\b",
]

_ONE_SHOT_KEYWORDS = [
    r"\bone.off\b", r"\bad.hoc\b", r"\bquick\s+favour\b",
    r"\bpanel\s+appearance\b", r"\bkeynote\b.*\bonly\b",
    r"\bprestige\b.*\bno\s+output\b",
]


def _eval_r4(action: str, config: dict[str, Any]) -> RuleEvaluation:
    text = action.lower()
    if any(re.search(p, text, re.IGNORECASE) for p in _ONE_SHOT_KEYWORDS):
        return RuleEvaluation(passed=False, rationale="One-shot/non-compounding activity detected")
    if any(re.search(p, text, re.IGNORECASE) for p in _COMPOUND_KEYWORDS):
        return RuleEvaluation(passed=True, rationale="Produces reusable artefact")
    return RuleEvaluation(passed=True, rationale="No one-shot anti-pattern detected (default pass)")


# --- R5: Anti-Fragility ---

_FRAGILITY_KEYWORDS = [
    r"\bsingle\s+funder\b", r"\block.in\b", r"\bvendor\s+lock\b",
    r"\bsole\s+author\b", r"\bsingle\s+point\b",
    r"\ball\s+eggs\b", r"\bconcentrat\w+\s+risk\b",
    r"\bno\s+backup\b", r"\birreversible\b",
]

_ANTIFRAGILE_KEYWORDS = [
    r"\bdiversif\w+\b", r"\bredundan\w+\b", r"\boptionality\b",
    r"\bmulti.platform\b", r"\bopen\s+standard\b",
    r"\bcross.institution\b", r"\bdistribut\w+\b",
]


def _eval_r5(action: str, config: dict[str, Any]) -> RuleEvaluation:
    text = action.lower()
    if any(re.search(p, text, re.IGNORECASE) for p in _FRAGILITY_KEYWORDS):
        return RuleEvaluation(passed=False, rationale="Action increases fragility or single-point dependence")
    if any(re.search(p, text, re.IGNORECASE) for p in _ANTIFRAGILE_KEYWORDS):
        return RuleEvaluation(passed=True, rationale="Action increases optionality or redundancy")
    return RuleEvaluation(passed=True, rationale="No fragility signals detected (default pass)")


# --- Public API ---

_EVALUATORS = {
    "R1": _eval_r1,
    "R2": _eval_r2,
    "R3": _eval_r3,
    "R4": _eval_r4,
    "R5": _eval_r5,
}


def evaluate_rules(action: str, config: dict[str, Any]) -> dict[str, RuleEvaluation]:
    """Evaluate all five rules against an action. Returns {rule_id: RuleEvaluation}."""
    return {rule_id: fn(action, config) for rule_id, fn in _EVALUATORS.items()}


def compute_verdict(rules: dict[str, RuleEvaluation]) -> Verdict:
    """Derive a verdict from rule evaluations.

    - Any R1 or R2 fail -> NO
    - R5 fail -> NO (redesign needed)
    - R3 fail -> PROTOTYPE
    - R4 fail alone -> YES (but downgraded priority)
    - All pass -> YES
    """
    if not rules["R1"].passed:
        return Verdict.NO
    if not rules["R2"].passed:
        return Verdict.NO
    if not rules["R5"].passed:
        return Verdict.NO
    if not rules["R3"].passed:
        return Verdict.PROTOTYPE
    return Verdict.YES
