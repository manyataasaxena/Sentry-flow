from enum import StrEnum

from pydantic import Field

from .common import Contract


class IntentType(StrEnum):
    RESEARCH = "research"
    DATA_ANALYSIS = "data_analysis"
    KNOWLEDGE_QA = "knowledge_qa"
    ACTION_EXECUTION = "action_execution"
    SMALLTALK = "smalltalk"
    UNSAFE = "unsafe"


class IntentClassification(Contract):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0, description="LLM confidence 0-1")
    rationale: str = Field(max_length=300, description="Human-readable rationale")