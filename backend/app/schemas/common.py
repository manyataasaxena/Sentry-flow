from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    """Base for every cross-boundary model: immutable, strict."""
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AgentName(StrEnum):
    INTAKE_GUARD = "intake_guard"
    PLANNER = "planner"
    APPROVAL_GATE = "approval_gate"
    WORKER = "worker"
    VERIFIER = "verifier"
    FINALIZE = "finalize"
    SAFE_REFUSAL = "safe_refusal"


class ErrorInfo(Contract):
    code: str = Field(description="e.g. CIRCUIT_OPEN, TIMEOUT, BUDGET_EXCEEDED")
    message: str
    retryable: bool = False
    dependency: str | None = None


class BudgetUsage(Contract):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    steps_executed: int = 0
    elapsed_ms: int = 0
