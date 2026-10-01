
from pydantic import Field

from .common import Contract


class Citation(Contract):
    step_id: str
    source: str = Field(description="url or doc_id")
    quote: str | None = Field(default=None, max_length=200)


class FinalAnswer(Contract):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    degraded: bool = False
