from typing import Annotated

from pydantic import Field

from .common import Contract, RiskLevel
from .intent import IntentClassification
from .tools import ToolArgs


class PlanStep(Contract):
    step_id: str = Field(pattern=r"^s\d{1,2}$")
    goal: str = Field(max_length=200)
    args: ToolArgs
    depends_on: list[str] = Field(default_factory=list)


class Plan(Contract):
    intent: IntentClassification
    steps: list[PlanStep] = Field(max_length=8)
    strategy_summary: str = Field(max_length=500)
    risk: RiskLevel
    clarification_question: str | None = None
    produced_by_fallback: bool = False