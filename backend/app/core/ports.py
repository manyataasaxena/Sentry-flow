from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMPort(Protocol):
    """Protocol for LLM providers."""

    async def structured(
            self,
            model: type[T],
            messages: list[dict[str, Any]],
            *,
            purpose: str,
        ) -> T: ...


class CachePort(Protocol):
    """Protocol for caching."""

    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...


class EventBusPort(Protocol):
    """Protocol for event bus."""

    async def publish(self, channel: str, message: str) -> None: ...
    async def subscribe(self, channel: str, callback: Callable[[str], Awaitable[None]]) -> None: ...


class RunRepositoryPort(Protocol):
    """Protocol for run repository."""

    async def create_run(self, run_data: dict[str, Any]) -> dict[str, Any]: ...
    async def get_run(self, run_id: str) -> dict[str, Any] | None: ...
    async def update_run(self, run_id: str, update_data: dict[str, Any]) -> dict[str, Any] | None: ...
    async def list_runs(self, user_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]: ...


class ToolProviderPort(Protocol):
    """Protocol for tool providers."""

    async def execute(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]: ...


class RunExecutorPort(Protocol):
    """Protocol for run executor."""

    async def execute(self, run_id: str, task: str, options: dict[str, Any]) -> Awaitable[dict[str, Any]]: ...


class CheckpointerPort(Protocol):
    """Protocol for checkpointer."""

    async def setup(self) -> None: ...
    async def get(self, thread_id: str, checkpoint_id: str) -> dict[str, Any] | None: ...
    async def put(self, thread_id: str, checkpoint_id: str, checkpoint: dict[str, Any]) -> None: ...
    async def list(self, thread_id: str) -> list[dict[str, Any]]: ...
