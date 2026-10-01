from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, HttpUrl

from .common import Contract, ErrorInfo, RiskLevel


class ToolName(StrEnum):
    WEB_SEARCH = "web_search"
    HTTP_FETCH = "http_fetch"
    CALCULATOR = "calculator"
    KB_LOOKUP = "kb_lookup"
    EXECUTE_WEBHOOK = "execute_webhook"


class WebSearchArgs(Contract):
    tool: Literal["web_search"] = "web_search"
    query: str = Field(min_length=2, max_length=300)
    max_results: int = Field(default=5, ge=1, le=10)


class HttpFetchArgs(Contract):
    tool: Literal["http_fetch"] = "http_fetch"
    url: HttpUrl


class CalculatorArgs(Contract):
    tool: Literal["calculator"] = "calculator"
    expression: str = Field(max_length=200)


class KbLookupArgs(Contract):
    tool: Literal["kb_lookup"] = "kb_lookup"
    query: str = Field(min_length=2, max_length=300)
    top_k: int = Field(default=4, ge=1, le=10)


class WebhookArgs(Contract):
    tool: Literal["execute_webhook"] = "execute_webhook"
    endpoint_id: str = Field(description="Pre-registered endpoint id")
    payload_summary: str = Field(max_length=500)


ToolArgs = Annotated[
    WebSearchArgs | HttpFetchArgs | CalculatorArgs | KbLookupArgs | WebhookArgs,
    Field(discriminator="tool"),
]


class SearchHit(Contract):
    title: str
    url: str
    snippet: str


class SearchOutput(Contract):
    kind: Literal["search"] = "search"
    hits: list[SearchHit]


class FetchOutput(Contract):
    kind: Literal["fetch"] = "fetch"
    url: str
    text: str
    truncated: bool


class CalcOutput(Contract):
    kind: Literal["calc"] = "calc"
    value: float


class Passage(Contract):
    doc_id: str
    text: str
    score: float


class KbOutput(Contract):
    kind: Literal["kb"] = "kb"
    passages: list[Passage]


class WebhookOutput(Contract):
    kind: Literal["webhook"] = "webhook"
    status_code: int
    summary: str


ToolOutput = Annotated[
    SearchOutput | FetchOutput | CalcOutput | KbOutput | WebhookOutput,
    Field(discriminator="kind"),
]


class ToolStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"
    REJECTED = "rejected"


class ToolResult(Contract):
    step_id: str
    tool: ToolName
    status: ToolStatus
    output: ToolOutput | None = None
    error: ErrorInfo | None = None
    latency_ms: int = Field(ge=0)
    cache_hit: bool = False


class ToolSpec(Contract):
    name: ToolName
    description: str
    risk: RiskLevel
    capabilities: list[str]  # IntentType values
    cacheable: bool
    cache_ttl_seconds: int = 0
    timeout_seconds: float = 15.0
    max_concurrency: int = 5
