from typing import Optional

from ..core.config import settings
from ..core.logging import get_logger
from ..schemas.intent import IntentType, IntentClassification
from ..schemas.plan import Plan, PlanStep
from ..schemas.tools import WebSearchArgs, ToolArgs

logger = get_logger(__name__)


def rule_based_plan(intent: IntentClassification) -> Plan:
    """Create a deterministic plan based on intent keywords.

    Used when LLM is unavailable or validation fails.
    """
    intent_type = intent.intent
    clarification_question = None
    produced_by_fallback = True

    # Determine tools based on intent
    if intent_type == IntentType.RESEARCH:
        steps = [
            PlanStep(
                step_id="s1",
                goal="Search for relevant information",
                args=WebSearchArgs(query=f"Research topic: {intent.rationale[:100]}"),
                depends_on=[],
            )
        ]
        strategy_summary = "Research strategy using web search"
    elif intent_type == IntentType.KNOWLEDGE_QA:
        steps = [
            PlanStep(
                step_id="s1",
                goal="Look up knowledge base",
                args=WebSearchArgs(query=intent.rationale[:100]),
                depends_on=[],
            )
        ]
        strategy_summary = "Knowledge base lookup strategy"
    elif intent_type == IntentType.DATA_ANALYSIS:
        steps = [
            PlanStep(
                step_id="s1",
                goal="Analyze data",
                args=WebSearchArgs(query=f"Data analysis: {intent.rationale[:100]}"),
                depends_on=[],
            )
        ]
        strategy_summary = "Data analysis strategy"
    else:
        steps = []
        strategy_summary = "No safe plan could be generated"
        clarification_question = "Could you clarify your request?"

    risk = "low" if intent.confidence >= 0.7 else "medium" if intent.confidence >= 0.5 else "high"

    return Plan(
        intent=intent,
        steps=steps,
        strategy_summary=strategy_summary,
        risk=risk,
        clarification_question=clarification_question,
        produced_by_fallback=produced_by_fallback,
    )


def degraded_response(message: str) -> str:
    """Create a degraded response when LLM is unavailable."""
    return f"[Degraded mode] {message}. Some features may be limited."