from typing import Protocol, TypeVar, Awaitable, Optional
from pydantic import BaseModel

T = TypeVar("T")


class LLMPort(Protocol):
    """Protocol for LLM providers."""

    async def structured(
        self,
        model: type[T],
        messages: list[dict],
        *,
        purpose: str,
    ) -> Awaitable[T]: ...


class CachePort(Protocol):
    """Protocol for caching."""

    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None: ...
    async def delete(self, key: str) -> None: ...


class EventBusPort(Protocol):
    """Protocol for event bus."""

    async def publish(self, channel: str, message: str) -> None: ...
    async def subscribe(self, channel: str, callback) -> None: ...


class RunRepositoryPort(Protocol):
    """Protocol for run repository."""

    async def create_run(self, run_data: dict) -> dict: ...
    async def get_run(self, run_id: str) -> Optional[dict]: ...
    async def update_run(self, run_id: str, update_data: dict) -> Optional[dict]: ...
    async def list_runs(self, user_id: Optional[str] = None, status: Optional[str] = None) -> list[dict]: ...


class ToolProviderPort(Protocol):
    """Protocol for tool providers."""

    async def execute(self, tool_name: str, args: dict) -> dict: ...


class RunExecutorPort(Protocol):
    """Protocol for run executor."""

    async def execute(self, run_id: str, task: str, options: dict) -> Awaitable[dict]: ...


class CheckpointerPort(Protocol):
    """Protocol for checkpointer."""

    async def setup(self) -> None: ...
    async def get(self, thread_id: str, checkpoint_id: str) -> Optional[dict]: ...
    async def put(self, thread_id: str, checkpoint_id: str, checkpoint: dict) -> None: ...
    async def list(self, thread_id: str) -> list[dict]: ...