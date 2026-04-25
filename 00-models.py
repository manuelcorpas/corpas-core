"""Pydantic models for the Corpas-Core Constitution governance system.

All schemas used by the governance gateway, decision ledger, and CLI.
No side effects at module scope.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    YES = "yes"
    NO = "no"
    DEFER = "defer"
    ESCALATE = "escalate"
    PROTOTYPE = "prototype"


class Mode(str, Enum):
    MISSION_CRITICAL = "mission_critical"
    CORE_RESPONSIBILITY = "core_responsibility"
    DECLINE = "decline"
    DEFER = "defer"


class RuleEvaluation(BaseModel):
    passed: bool
    rationale: str


class CriticOutput(BaseModel):
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    violations: list[str] = Field(default_factory=list)
    suggested_revision: Optional[str] = None
    requires_principal_approval: bool = False


class GovernResult(BaseModel):
    allowed: bool
    block_reason: Optional[str] = None
    verdict: Verdict
    mode: Mode
    rules_evaluated: dict[str, RuleEvaluation]
    confidence: float = Field(ge=0.0, le=1.0)
    is_high_stakes: bool = False
    requires_principal_approval: bool = False
    manipulation_flags: list[str] = Field(default_factory=list)
    critic_result: Optional[CriticOutput] = None
    rationale: str = ""
    recommended_next_action: str = ""
    constitution_hash: str = ""
    output_hash: Optional[str] = None


class LedgerEntry(BaseModel):
    timestamp: str
    input_hash: str
    constitution_hash: str
    output_hash: Optional[str] = None
    mode_classification: Mode
    verdict: Verdict
    rules_evaluated: dict[str, RuleEvaluation]
    confidence: float = Field(ge=0.0, le=1.0)
    is_high_stakes: bool = False
    requires_principal_approval: bool = False
    manipulation_flags: list[str] = Field(default_factory=list)
    allowed: bool = True
    block_reason: Optional[str] = None
    rationale: str = ""
    recommended_next_action: str = ""
    critic_result: Optional[CriticOutput] = None
    alternatives_considered_and_declined: Optional[list[str]] = None
    principal_override: Optional[str] = None
    outcome_signal: Optional[str] = None
