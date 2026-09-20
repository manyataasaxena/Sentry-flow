from datetime import datetime
from typing import Annotated, Literal, Optional, List

from pydantic import Field

from .common import Contract


class BreakerStatus(Contract):
    dependency: str
    state: Literal["closed", "open", "half_open"]
    failure_count: int
    last_failure_at: Optional[datetime] = None
    opens_at: Optional[datetime] = None


class HealthReport(Contract):
    status: Literal["ok", "degraded", "down"]
    postgres_ms: Optional[float] = None
    redis_ms: Optional[float] = None
    llm_primary: Literal["ok", "degraded", "down"]
    breakers: List[BreakerStatus]
    chaos_enabled: bool