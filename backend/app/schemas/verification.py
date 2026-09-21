from enum import StrEnum
from typing import Annotated, Literal, Optional

from pydantic import Field

from .common import Contract, Severity


class Verdict(StrEnum):
    PASS = "pass"
    REVISE = "revise"
    BLOCK = "block"


class CheckType(StrEnum):
    SCHEMA = "schema"
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    PII_LEAK = "pii_leak"
    POLICY = "policy"
    GROUNDEDNESS = "groundedness"
    TOOL_ABUSE = "tool_abuse"


class CheckResult(Contract):
    check: CheckType
    passed: bool
    severity: Severity
    detail: str


class VerificationReport(Contract):
    verdict: Verdict
    score: float = Field(ge=0.0, le=1.0)
    feedback: str
    suggested_improvements: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    revision_instructions: Optional[str] = None
    safe_message: Optional[str] = None