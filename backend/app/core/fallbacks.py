from typing import Optional, List

from ..core.config import settings
from ..core.logging import get_logger
from ..schemas.intent import IntentType, IntentClassification
from ..schemas.plan import Plan, PlanStep
from ..schemas.tools import WebSearchArgs, ToolArgs, ToolResult, ToolStatus
from ..schemas.verification import VerificationReport, Verdict
from ..schemas.answer import FinalAnswer, Citation

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


def get_planner_fallback():
    """Get the planner fallback instance."""
    return _PlannerFallback()


class _PlannerFallback:
    """Planner fallback implementation."""
    
    def classify_intent(self, task: str) -> IntentClassification:
        """Classify intent using rule-based approach."""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["search", "find", "lookup", "research"]):
            intent_type = IntentType.RESEARCH
        elif any(word in task_lower for word in ["calculate", "compute", "math", "sum", "average"]):
            intent_type = IntentType.DATA_ANALYSIS
        elif any(word in task_lower for word in ["what is", "who is", "explain", "define"]):
            intent_type = IntentType.KNOWLEDGE_QA
        else:
            intent_type = IntentType.RESEARCH
            
        return IntentClassification(
            intent=intent_type,
            confidence=0.6,
            rationale="Classified by fallback rules"
        )
    
    def create_plan(self, task: str, intent: Optional[IntentClassification] = None) -> Plan:
        """Create a plan using rule-based approach."""
        if intent is None:
            intent = self.classify_intent(task)
            
        return rule_based_plan(intent)


def get_verifier_fallback():
    """Get the verifier fallback instance."""
    return _VerifierFallback()


class _VerifierFallback:
    """Verifier fallback implementation."""
    
    def verify(self, task: str, results: List[ToolResult]) -> VerificationReport:
        """Verify results using rule-based approach."""
        successful_results = sum(1 for r in results if r.status == ToolStatus.SUCCESS)
        total_results = len(results)
        
        if total_results == 0:
            score = 0.0
            verdict = Verdict.NEEDS_REVIEW
        elif successful_results == total_results:
            score = 100.0
            verdict = Verdict.PASS
        elif successful_results >= total_results * 0.5:
            score = 60.0
            verdict = Verdict.PASS
        else:
            score = 30.0
            verdict = Verdict.FAIL
            
        return VerificationReport(
            verdict=verdict,
            score=score,
            feedback=f"Fallback verification: {successful_results}/{total_results} steps succeeded",
            suggested_improvements=["Consider using a more capable LLM for verification"],
            confidence=0.5
        )


def get_finalizer_fallback():
    """Get the finalizer fallback instance."""
    return _FinalizerFallback()


class _FinalizerFallback:
    """Finalizer fallback implementation."""
    
    def create_final_answer(self, task: str, results: List[ToolResult]) -> FinalAnswer:
        """Create final answer using rule-based approach."""
        successful_results = sum(1 for r in results if r.status == ToolStatus.SUCCESS)
        
        answer = f"Based on your task '{task}', I executed {successful_results} steps. "
        
        if successful_results > 0:
            answer += "Here are the key findings:\n"
            for i, result in enumerate(results):
                if result.status == ToolStatus.SUCCESS:
                    answer += f"- Step {i+1}: Successfully completed\n"
                else:
                    answer += f"- Step {i+1}: Failed - {result.error.message if result.error else 'Unknown error'}\n"
        else:
            answer += "No steps were successfully completed. Please try a different approach."
            
        return FinalAnswer(
            answer=answer,
            key_findings=[f"Executed {successful_results} steps"],
            confidence=0.5 if successful_results > 0 else 0.2,
            citations=[],
            next_steps=["Review the results and consider alternative approaches"]
        )