import asyncpg
from asyncpg import Pool
from asyncpg.pool import PoolConnectionProxy
from typing import Optional

from ..core.config import settings


class PostgresAdapter:
    """PostgreSQL adapter for LangGraph checkpointer and app tables."""

    def __init__(self):
        self._pool: Optional[Pool] = None

    async def connect(self) -> None:
        """Create connection pool using psycopg DSN."""
        self._pool = await asyncpg.create_pool(
            settings.psycopg_dsn,
            min_size=1,
            max_size=settings.PG_POOL_MAX,
            command_timeout=60,
        )
        if not self._pool:
            raise RuntimeError("Failed to create PostgreSQL connection pool")

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def get_connection(self) -> PoolConnectionProxy:
        """Get a connection from the pool."""
        if not self._pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        return await self._pool.acquire()

    async def release_connection(self, conn: PoolConnectionProxy) -> None:
        """Release a connection back to the pool."""
        await self._pool.release(conn)

    async def execute(self, query: str, *args) -> list[dict]:
        """Execute a query and return results as list of dicts."""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)

    async def execute_one(self, query: str, *args) -> Optional[dict]:
        """Execute a query and return a single result."""
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)

    async def execute_script(self, script: str) -> None:
        """Execute a SQL script."""
        async with self.get_connection() as conn:
            await conn.executescript(script)

    async def health_check(self) -> bool:
        """Check if PostgreSQL is reachable."""
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False


# Global instance
postgres = PostgresAdapter()