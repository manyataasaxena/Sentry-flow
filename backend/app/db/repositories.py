import re
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings
from ..core.errors import SentryFlowError
from ..core.logging import get_logger
from .models import AuditLog, Base, EvalResult, EvalRun, KbDocument, Run, RunEvent, User

logger = get_logger(__name__)
KB_STOPWORDS = frozenset({
    "what", "is", "the", "of", "a", "an", "how", "to", "in",
    "and", "or", "but", "for", "with", "about", "between", "explain", "describe", "tell", "me", "give", "why", "when", "where", "which", "who", "does", "do", "are", "was", "be", "it", "this", "that", "on", "at", "by", "from", "as",
})


def score_kb_relevance(query: str, text: str) -> float:
    """Return the proportion of non-stopword query terms found in text."""
    keywords = [
        word
        for word in re.findall(r"[a-z0-9]+", query.lower())
        if len(word) >= 3 and word not in KB_STOPWORDS
    ]
    if not keywords:
        return 0.0

    document_words = set(re.findall(r"[a-z0-9]+", text.lower()))
    matches = sum(
        1 for keyword in keywords
        if keyword in document_words or f"{keyword}s" in document_words
    )
    return matches / len(keywords)


class DatabaseRepository:
    """Repository for database operations."""

    def __init__(self) -> None:
        self._engine = create_async_engine(settings.asyncpg_dsn)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init(self) -> None:
        """Initialize database and create tables."""
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized")
            await self._seed_kb_documents()
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise SentryFlowError("Database initialization failed", error_info={"error": str(e)}) from e

    async def _seed_kb_documents(self) -> None:
        """Seed KB documents if table is empty."""
        async with self._session_factory() as session:
            result = await session.execute(select(KbDocument).limit(1))
            if result.scalar_one_or_none() is not None:
                return  # Already seeded

            seed_docs = [
                KbDocument(
                    title="Python Programming Language",
                    body="Python is a high-level, interpreted programming language known for its readability and versatility. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
                ),
                KbDocument(
                    title="Quantum Computing Basics",
                    body="Quantum computing leverages quantum mechanical phenomena like superposition and entanglement to perform computations. Qubits can represent 0, 1, or both simultaneously, enabling parallel processing for certain problems.",
                ),
                KbDocument(
                    title="Capital Cities of Europe",
                    body="Major European capitals include: Paris (France), Berlin (Germany), Rome (Italy), Madrid (Spain), London (UK), Amsterdam (Netherlands), Vienna (Austria), Warsaw (Poland), Stockholm (Sweden), and Copenhagen (Denmark).",
                ),
                KbDocument(
                    title="Machine Learning Fundamentals",
                    body="Machine learning is a subset of AI that enables systems to learn from data without explicit programming. Key types include supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), and reinforcement learning.",
                ),
                KbDocument(
                    title="Web Development with FastAPI",
                    body="FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints. It provides automatic OpenAPI documentation, dependency injection, and high performance through Starlette and Pydantic.",
                ),
                KbDocument(
                    title="PostgreSQL Database",
                    body="PostgreSQL is an advanced open-source relational database with support for JSON, full-text search, and advanced indexing. It's known for reliability, feature robustness, and performance.",
                ),
                KbDocument(
                    title="Redis In-Memory Store",
                    body="Redis is an in-memory data structure store used as a database, cache, and message broker. It supports strings, hashes, lists, sets, and sorted sets with atomic operations.",
                ),
                KbDocument(
                    title="LangGraph Orchestration",
                    body="LangGraph is a library for building stateful, multi-actor applications with LLMs. It provides graph-based orchestration with cycles, persistence, and human-in-the-loop capabilities for complex agent workflows.",
                ),
                KbDocument(
                    title="Docker Containerization",
                    body="Docker is a platform for developing, shipping, and running applications in containers. Containers package code and dependencies together, ensuring consistency across environments.",
                ),
                KbDocument(
                    title="Kubernetes Orchestration",
                    body="Kubernetes (K8s) is an open-source container orchestration platform that automates deployment, scaling, and management of containerized applications. It provides service discovery, load balancing, and self-healing.",
                ),
            ]

            session.add_all(seed_docs)
            await session.commit()
            logger.info("Seeded KB documents", count=len(seed_docs))

    async def close(self) -> None:
        """Close database connection."""
        await self._engine.dispose()

    async def health_check(self) -> bool:
        """Check if database is healthy."""
        try:
            async with self._session_factory() as session:
                await session.execute(select(1))
            return True
        except Exception:
            return False

    # Run operations
    async def create_run(self, run_data: dict[str, Any]) -> Run:
        """Create a new run."""
        async with self._session_factory() as session:
            run = Run(**run_data)
            session.add(run)
            await session.commit()
            await session.refresh(run)
            return run

    async def get_run(self, run_id: str) -> Run | None:
        """Get a run by ID."""
        async with self._session_factory() as session:
            return await session.get(Run, run_id)

    async def update_run(self, run_id: str, update_data: dict[str, Any]) -> Run | None:
        """Update a run."""
        async with self._session_factory() as session:
            run = await session.get(Run, run_id)
            if not run:
                return None
            for key, value in update_data.items():
                setattr(run, key, value)
            await session.commit()
            await session.refresh(run)
            return run

    async def list_runs(self, user_id: str | None = None, status: str | None = None, limit: int = 100) -> list[Run]:
        """List runs with optional filters."""
        async with self._session_factory() as session:
            query = select(Run)
            if user_id:
                query = query.where(Run.user_id == user_id)
            if status:
                query = query.where(Run.status == status)
            query = query.order_by(Run.created_at.desc()).limit(limit)
            result = await session.execute(query)
            return cast(list[Run], result.scalars().all())

    async def create_run_event(self, event_data: dict[str, Any]) -> RunEvent:
        """Create a run event."""
        async with self._session_factory() as session:
            event = RunEvent(**event_data)
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event

    async def get_run_events(self, run_id: str, after_seq: int | None = None, limit: int = 100) -> list[RunEvent]:
        """Get run events."""
        async with self._session_factory() as session:
            query = select(RunEvent).where(RunEvent.run_id == run_id)
            if after_seq:
                query = query.where(RunEvent.seq > after_seq)
            query = query.order_by(RunEvent.seq).limit(limit)
            result = await session.execute(query)
            return cast(list[RunEvent], result.scalars().all())

    # User operations
    async def get_user(self, user_id: str) -> User | None:
        """Get a user by ID."""
        async with self._session_factory() as session:
            return await session.get(User, user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        async with self._session_factory() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()

    # KB operations
    async def search_kb(self, query: str, top_k: int = 10) -> list[tuple[KbDocument, float]]:
        """Search KB documents by matching and ranking query keywords."""
        async with self._session_factory() as session:
            result = await session.execute(select(KbDocument))
            ranked: list[tuple[KbDocument, float]] = []
            for document in result.scalars().all():
                score = score_kb_relevance(query, f"{document.title} {document.body}")
                if score >= 0.34:
                    ranked.append((document, score))

            ranked.sort(key=lambda item: item[1], reverse=True)
            return ranked[:top_k]

    # Eval operations
    async def create_eval_run(self, eval_run_data: dict[str, Any]) -> EvalRun:
        """Create an eval run."""
        async with self._session_factory() as session:
            eval_run = EvalRun(**eval_run_data)
            session.add(eval_run)
            await session.commit()
            await session.refresh(eval_run)
            return eval_run

    async def create_eval_result(self, result_data: dict[str, Any]) -> EvalResult:
        """Create an eval result."""
        async with self._session_factory() as session:
            result = EvalResult(**result_data)
            session.add(result)
            await session.commit()
            await session.refresh(result)
            return result

    async def get_eval_run(self, eval_run_id: str) -> EvalRun | None:
        """Get an eval run by ID."""
        async with self._session_factory() as session:
            return await session.get(EvalRun, eval_run_id)

    # Audit operations
    async def create_audit_log(self, audit_data: dict[str, Any]) -> AuditLog:
        """Create an audit log entry."""
        async with self._session_factory() as session:
            audit = AuditLog(**audit_data)
            session.add(audit)
            await session.commit()
            await session.refresh(audit)
            return audit

    async def list_audit_logs(self, actor_id: str | None = None, action: str | None = None, limit: int = 100) -> list[AuditLog]:
        """List audit logs with optional filters."""
        async with self._session_factory() as session:
            query = select(AuditLog)
            if actor_id:
                query = query.where(AuditLog.actor_id == actor_id)
            if action:
                query = query.where(AuditLog.action == action)
            query = query.order_by(AuditLog.created_at.desc()).limit(limit)
            result = await session.execute(query)
            return cast(list[AuditLog], result.scalars().all())


# Global instance
repository = DatabaseRepository()
