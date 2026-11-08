"""SentryFlow LangGraph agent orchestration."""

import ast
import operator
import time
from collections.abc import Callable

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ..core.fallbacks import get_finalizer_fallback, get_planner_fallback, get_verifier_fallback
from ..core.llm_gateway import llm_gateway
from ..core.logging import get_logger
from ..core.observability import observe
from ..db.repositories import repository
from ..schemas.answer import FinalAnswer
from ..schemas.common import ErrorInfo, RiskLevel
from ..schemas.intent import IntentClassification
from ..schemas.plan import Plan, PlanStep
from ..schemas.run import ApprovalDecision, RunStatus
from ..schemas.tools import (
    CalcOutput,
    FetchOutput,
    KbOutput,
    Passage,
    SearchHit,
    SearchOutput,
    ToolName,
    ToolOutput,
    ToolResult,
    ToolStatus,
    WebhookOutput,
)
from ..schemas.verification import VerificationReport
from .state import RunState, StateUpdate, as_update

logger = get_logger(__name__)


# Safe calculator using AST
class SafeCalculator:
    """Safe expression evaluator using AST (no eval)."""

    _bin_operators: dict[type[ast.operator], Callable[[float, float], float]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }

    _un_operators: dict[type[ast.unaryop], Callable[[float], float]] = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    @classmethod
    def evaluate(cls, expression: str) -> float:
        """Safely evaluate a mathematical expression."""
        try:
            node = ast.parse(expression, mode="eval")
            return float(cls._eval_node(node.body))
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}") from e

    @classmethod
    def _eval_node(cls, node: ast.AST) -> float:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("Only numeric constants allowed")
        elif isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)
            op_type = type(node.op)
            if op_type in cls._bin_operators:
                return cls._bin_operators[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in cls._un_operators:
                return cls._un_operators[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")
        else:
            raise ValueError(f"Unsupported expression type: {type(node)}")


# Mock web search results
MOCK_SEARCH_RESULTS: dict[str, list[dict[str, str]]] = {
    "capital of france": [
        {"title": "Paris - Wikipedia", "url": "https://en.wikipedia.org/wiki/Paris", "snippet": "Paris is the capital and most populous city of France."},
        {"title": "France - Britannica", "url": "https://www.britannica.com/place/France", "snippet": "France is a country in Western Europe. Its capital is Paris."},
        {"title": "Capital Cities of Europe", "url": "https://example.com/europe-capitals", "snippet": "List of European capitals including Paris, France."},
    ],
    "quantum computing": [
        {"title": "Quantum Computing - IBM", "url": "https://www.ibm.com/quantum", "snippet": "Quantum computing uses quantum mechanics to solve complex problems."},
        {"title": "Quantum Computing Explained", "url": "https://example.com/quantum", "snippet": "A beginner's guide to quantum computing concepts and applications."},
        {"title": "Recent Advances in Quantum Computing", "url": "https://arxiv.org/quantum", "snippet": "Latest research papers on quantum algorithms and hardware."},
    ],
    "python": [
        {"title": "Python.org", "url": "https://www.python.org", "snippet": "Official Python programming language website."},
        {"title": "Python Tutorial - Real Python", "url": "https://realpython.com", "snippet": "Comprehensive Python tutorials and guides."},
        {"title": "Python Documentation", "url": "https://docs.python.org", "snippet": "Official Python documentation and reference."},
    ],
    "default": [
        {"title": "Search Result 1", "url": "https://example.com/1", "snippet": "Relevant information about the query topic."},
        {"title": "Search Result 2", "url": "https://example.com/2", "snippet": "Additional details and context for the search."},
        {"title": "Search Result 3", "url": "https://example.com/3", "snippet": "Further reading and related resources."},
    ],
}


def _get_mock_search_hits(query: str) -> list[dict[str, str]]:
    """Get mock search hits based on query keywords."""
    query_lower = query.lower()
    for key, hits in MOCK_SEARCH_RESULTS.items():
        if key in query_lower:
            return hits
    return MOCK_SEARCH_RESULTS["default"]


@observe(name="intake_guard")
async def intake_guard(state: RunState) -> dict[str, object]:
    """Validate and classify the user task."""
    try:
        response = await llm_gateway.structured(
            IntentClassification,
            [
                {"role": "system", "content": "Classify the task into an intent type."},
                {"role": "user", "content": f"Task: {state.task}"},
            ],
            purpose="intent_classification",
        )
        return as_update(StateUpdate(intent=response))
    except Exception as e:
        logger.error("Intent classification failed", error=str(e))
        fallback = get_planner_fallback()
        return as_update(StateUpdate(intent=fallback.classify_intent(state.task)))


@observe(name="planner")
async def planner(state: RunState) -> dict[str, object]:
    """Create an execution plan based on the classified intent."""
    if not state.intent:
        fallback = get_planner_fallback()
        return as_update(StateUpdate(plan=fallback.create_plan(state.task)))

    try:
        response = await llm_gateway.structured(
            Plan,
            [
                {"role": "system", "content": "Create a step-by-step plan for the task."},
                {"role": "user", "content": f"Task: {state.task}\nIntent: {state.intent.intent.value}"},
            ],
            purpose="plan_creation",
        )
        return as_update(StateUpdate(plan=response))
    except Exception as e:
        logger.error("Plan creation failed", error=str(e))
        fallback = get_planner_fallback()
        return as_update(StateUpdate(plan=fallback.create_plan(state.task, state.intent)))


@observe(name="approval_gate")
async def approval_gate(state: RunState) -> dict[str, object]:
    """Review and approve the plan before execution."""
    if not state.plan or not state.plan.steps:
        return as_update(StateUpdate(status=RunStatus.BLOCKED, approval=ApprovalDecision(approved=False, note="No plan to approve")))

    high_risk_steps = [s for s in state.plan.steps if state.plan.risk == RiskLevel.HIGH]
    if high_risk_steps:
        return as_update(StateUpdate(approval=ApprovalDecision(approved=True, note=f"Auto-approved with {len(high_risk_steps)} high-risk steps")))
    return as_update(StateUpdate(approval=ApprovalDecision(approved=True, note="Plan approved automatically")))


@observe(name="worker")
async def worker(state: RunState) -> dict[str, object]:
    """Execute the approved plan steps."""
    if not state.plan or not state.plan.steps:
        return as_update(StateUpdate(status=RunStatus.BLOCKED, results=[]))

    results: list[ToolResult] = []
    for step in state.plan.steps:
        try:
            result = await _execute_step(step)
            results.append(result)
        except Exception as e:
            logger.error(f"Step {step.step_id} failed", error=str(e))
            results.append(ToolResult(
                step_id=step.step_id,
                tool=ToolName.WEB_SEARCH,
                status=ToolStatus.FAILED,
                output=None,
                error=ErrorInfo(code="EXECUTION_ERROR", message=str(e)),
                latency_ms=0,
                cache_hit=False,
            ))

    return as_update(StateUpdate(results=results))


async def _execute_step(step: PlanStep) -> ToolResult:
    """Execute a single plan step with real mock implementations."""
    start_time = time.perf_counter()

    tool_name = step.args.tool if hasattr(step.args, "tool") else ToolName.WEB_SEARCH
    args = step.args.model_dump() if hasattr(step.args, "model_dump") else {}

    output: ToolOutput | None = None

    try:
        if tool_name == ToolName.WEB_SEARCH:
            query = args.get("query", "")
            max_results = args.get("max_results", 3)
            hits = _get_mock_search_hits(query)[:max_results]
            output = SearchOutput(
                hits=[
                    SearchHit(title=h["title"], url=h["url"], snippet=h["snippet"])
                    for h in hits
                ]
            )

        elif tool_name == ToolName.HTTP_FETCH:
            url = args.get("url", "")
            output = FetchOutput(url=url, text=f"Mock content from {url}", truncated=False)

        elif tool_name == ToolName.CALCULATOR:
            expr = args.get("expression", "0")
            value = SafeCalculator.evaluate(expr)
            output = CalcOutput(value=value)

        elif tool_name == ToolName.KB_LOOKUP:
            query = args.get("query", "")
            top_k = args.get("top_k", 3)
            docs = await repository.search_kb(query, top_k)
            passages = [
                Passage(doc_id=str(doc.id), text=doc.body[:500], score=0.9)
                for doc in docs
            ]
            output = KbOutput(passages=passages)

        elif tool_name == ToolName.EXECUTE_WEBHOOK:
            output = WebhookOutput(status_code=200, summary="Webhook executed successfully (mock)")

        else:
            output = None

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return ToolResult(
            step_id=step.step_id,
            tool=tool_name,
            status=ToolStatus.SUCCESS,
            output=output,
            latency_ms=latency_ms,
            cache_hit=False,
        )

    except Exception as e:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"Step {step.step_id} failed", error=str(e))
        return ToolResult(
            step_id=step.step_id,
            tool=tool_name,
            status=ToolStatus.FAILED,
            output=None,
            error=ErrorInfo(code="EXECUTION_ERROR", message=str(e)),
            latency_ms=latency_ms,
            cache_hit=False,
        )


@observe(name="verifier")
async def verifier(state: RunState) -> dict[str, object]:
    """Verify the results and provide feedback."""
    try:
        response = await llm_gateway.structured(
            VerificationReport,
            [
                {"role": "system", "content": "Verify the execution results."},
                {"role": "user", "content": f"Task: {state.task}\nResults: {state.results}"},
            ],
            purpose="verification",
        )
        return as_update(StateUpdate(report=response))
    except Exception as e:
        logger.error("Verification failed", error=str(e))
        fallback = get_verifier_fallback()
        return as_update(StateUpdate(report=fallback.verify(state.task, state.results)))


@observe(name="finalize")
async def finalize(state: RunState) -> dict[str, object]:
    """Create the final answer based on all results."""
    try:
        response = await llm_gateway.structured(
            FinalAnswer,
            [
                {"role": "system", "content": "Create a comprehensive final answer."},
                {"role": "user", "content": f"Task: {state.task}\nResults: {state.results}"},
            ],
            purpose="final_answer",
        )
        return as_update(StateUpdate(draft=response, status=RunStatus.COMPLETED))
    except Exception as e:
        logger.error("Finalization failed", error=str(e))
        fallback = get_finalizer_fallback()
        return as_update(StateUpdate(draft=fallback.create_final_answer(state.task, state.results), status=RunStatus.COMPLETED))


def create_agent_graph() -> CompiledStateGraph[RunState, None, RunState, RunState]:
    """Create and return the agent execution graph."""
    workflow = StateGraph(RunState)

    workflow.add_node("intake_guard", intake_guard)
    workflow.add_node("planner", planner)
    workflow.add_node("approval_gate", approval_gate)
    workflow.add_node("worker", worker)
    workflow.add_node("verifier", verifier)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("intake_guard")

    workflow.add_edge("intake_guard", "planner")
    workflow.add_edge("planner", "approval_gate")
    workflow.add_edge("approval_gate", "worker")
    workflow.add_edge("worker", "verifier")
    workflow.add_edge("verifier", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


agent_graph = create_agent_graph()