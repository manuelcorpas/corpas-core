"""Router: classify incoming requests into operating modes.

Deterministic keyword matching against mode triggers defined in the constitution.
No LLM calls. No side effects at module scope.
"""

from __future__ import annotations

import re
from typing import Any

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_models_spec = spec_from_file_location("models", Path(__file__).parent / "00-models.py")
_models = module_from_spec(_models_spec)
_models_spec.loader.exec_module(_models)
Mode = _models.Mode


# Keyword patterns for each mode, derived from constitution trigger definitions.
_MODE_PATTERNS: dict[Mode, list[str]] = {
    Mode.MISSION_CRITICAL: [
        r"\bframework\b", r"\bHEIM\b", r"\bClawBio\b", r"\bFairMed\b",
        r"\bflagship\s+publication\b", r"\bseed\s+funding\b",
        r"\bcategory.defining\b", r"\bgenomic\s+equity\b",
        r"\bprecision\s+medicine\b", r"\bdata\s+sovereignty\b",
        r"\barchitecture\b.*\b(core|agent|system)\b",
        r"\bstandard\b.*\b(global|international)\b",
    ],
    Mode.CORE_RESPONSIBILITY: [
        r"\bteaching\b", r"\bsupervision\b", r"\bsupervis(e|or)\b",
        r"\bstudent\b", r"\bWestminster\b", r"\binstitutional\b",
        r"\bco.author\b", r"\bcollaborat(e|or|ion)\b",
        r"\bCRUK\b", r"\bTuring\b", r"\bNHS\b",
        r"\bmarking\b", r"\bexam\b", r"\blecture\b",
    ],
    Mode.DECLINE: [
        r"\boff.mission\b", r"\bunrelated\b",
        r"\bno\s+compounding\b", r"\bone.shot\b",
        r"\bprestige\s+only\b",
    ],
    Mode.DEFER: [
        r"\blater\b", r"\bnext\s+quarter\b", r"\bafter\b.*\bdeadline\b",
        r"\bwhen\s+.*\b(ready|available|funded)\b",
        r"\bpostpone\b", r"\bdefer\b", r"\bparked\b",
    ],
}


def classify(action: str, config: dict[str, Any]) -> Mode:
    """Classify an action string into an operating mode.

    Checks modes in priority order: mission_critical > core_responsibility > defer > decline.
    Falls back to core_responsibility if no pattern matches (safe default).
    """
    text = action.lower()

    # Priority order: most important modes first
    for mode in [Mode.MISSION_CRITICAL, Mode.CORE_RESPONSIBILITY, Mode.DEFER, Mode.DECLINE]:
        patterns = _MODE_PATTERNS.get(mode, [])
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            return mode

    # Also check constitution-defined triggers dynamically
    modes_config = config.get("modes", {})
    for mode_name, mode_def in modes_config.items():
        triggers = mode_def.get("triggers", [])
        for trigger in triggers:
            trigger_words = trigger.replace("_", " ").lower()
            if trigger_words in text:
                try:
                    return Mode(mode_name)
                except ValueError:
                    continue

    return Mode.CORE_RESPONSIBILITY
