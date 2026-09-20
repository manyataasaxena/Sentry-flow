from enum import StrEnum
from typing import Annotated, Literal

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
    mode: Literal["input", "output"]
    verdict: Verdict
    score: float = Field(ge=0.0, le=1.0)
    checks: list[CheckResult]
    revision_instructions: str | None = None
    safe_message: str | None = None