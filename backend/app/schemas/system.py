from datetime import datetime
from typing import Literal

from .common import Contract


class BreakerStatus(Contract):
    dependency: str
    state: Literal["closed", "open", "half_open"]
    failure_count: int
    last_failure_at: datetime | None = None
    opens_at: datetime | None = None


class HealthReport(Contract):
    status: Literal["ok", "degraded", "down"]
    postgres_ms: float | None = None
    redis_ms: float | None = None
    llm_primary: Literal["ok", "degraded", "down"]
    breakers: list[BreakerStatus]
    chaos_enabled: bool
