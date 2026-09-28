from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_current_user
from ...schemas.tools import ToolSpec, ToolName
from ...schemas.common import RiskLevel
from ...core.logging import get_logger

logger = get_logger(__name__)

__all__ = ["RiskLevel"]

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])

# Demo tool specs
_tool_specs = [
    ToolSpec(
        name=ToolName.WEB_SEARCH,
        description="Search the web for information",
        risk=RiskLevel.LOW,
        capabilities=["research", "knowledge_qa"],
        cacheable=True,
        cache_ttl_seconds=300,
        timeout_seconds=15.0,
        max_concurrency=5,
    ),
    ToolSpec(
        name=ToolName.HTTP_FETCH,
        description="Fetch content from a URL",
        risk=RiskLevel.MEDIUM,
        capabilities=["research", "data_analysis"],
        cacheable=False,
        timeout_seconds=30.0,
        max_concurrency=3,
    ),
    ToolSpec(
        name=ToolName.CALCULATOR,
        description="Perform mathematical calculations",
        risk=RiskLevel.LOW,
        capabilities=["data_analysis"],
        cacheable=True,
        cache_ttl_seconds=3600,
        timeout_seconds=5.0,
        max_concurrency=10,
    ),
    ToolSpec(
        name=ToolName.KB_LOOKUP,
        description="Search the knowledge base",
        risk=RiskLevel.LOW,
        capabilities=["knowledge_qa"],
        cacheable=True,
        cache_ttl_seconds=600,
        timeout_seconds=10.0,
        max_concurrency=5,
    ),
    ToolSpec(
        name=ToolName.EXECUTE_WEBHOOK,
        description="Execute a pre-registered webhook (HIGH RISK)",
        risk=RiskLevel.HIGH,
        capabilities=["action_execution"],
        cacheable=False,
        timeout_seconds=30.0,
        max_concurrency=1,
    ),
]


@router.get("", response_model=List[ToolSpec])
async def list_tools(current_user: dict[str, Any] = Depends(get_current_user)) -> List[ToolSpec]:
    """List available tools."""
    return _tool_specs


@router.get("/{tool_name}", response_model=ToolSpec)
async def get_tool(tool_name: ToolName, current_user: dict[str, Any] = Depends(get_current_user)) -> ToolSpec:
    """Get tool specification."""
    for spec in _tool_specs:
        if spec.name == tool_name:
            return spec
    raise HTTPException(status_code=404, detail="Tool not found")