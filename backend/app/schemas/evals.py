from enum import StrEnum

from pydantic import Field

from .common import Contract, Severity


class AttackCategory(StrEnum):
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    JAILBREAK = "jailbreak"
    PII_EXFILTRATION = "pii_exfiltration"
    TOOL_ABUSE = "tool_abuse"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    BENIGN_CONTROL = "benign_control"


class ExpectedOutcome(StrEnum):
    BLOCK = "block"
    SANITIZE = "sanitize"
    PASS = "pass"


class AdversarialCase(Contract):
    id: str
    category: AttackCategory
    severity: Severity
    prompt: str
    fixture: str | None = None
    expected: ExpectedOutcome
    must_not_contain: list[str] = Field(default_factory=list)


class EvalResult(Contract):
    case_id: str
    category: AttackCategory
    expected: ExpectedOutcome
    actual: ExpectedOutcome
    passed: bool
    latency_ms: int
    detail: str


class EvalReport(Contract):
    id: str
    total: int
    passed: int
    pass_rate: float
    critical_block_rate: float
    false_positive_rate: float
    by_category: dict[AttackCategory, float]
    results: list[EvalResult]
