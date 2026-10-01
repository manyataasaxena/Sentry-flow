from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.errors import SentryFlowError
from .core.logging import configure_logging
from .db.postgres import postgres
from .db.checkpointer import checkpointer
from .db.redis import redis_client
from .db.repositories import repository
from .api.v1.runs import router as runs_router
from .api.v1.tools import router as tools_router
from .api.v1.evals import router as evals_router
from .api.v1.system import router as system_router
from .api.v1.audit import router as audit_router
from .api.v1.auth import router as auth_router
from .api.v1.ws import router as ws_router


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Initialize database connections
    await postgres.connect()
    await redis_client.connect()
    await repository.init()
    
    # Setup LangGraph checkpointer
    await checkpointer.setup()
    
    yield
    
    # Cleanup
    await repository.close()
    await redis_client.close()
    await postgres.close()


app = FastAPI(
    title="SentryFlow",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(runs_router)
app.include_router(tools_router)
app.include_router(evals_router)
app.include_router(system_router)
app.include_router(audit_router)
app.include_router(ws_router)


@app.exception_handler(SentryFlowError)
async def _handle_sentryflow_error(_request: object, exc: SentryFlowError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": exc.error_info, "request_id": "local"},
    )


@app.get("/livez")
async def livez() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    # Check if all dependencies are healthy
    postgres_healthy = await postgres.health_check()
    redis_healthy = await redis_client.health_check()
    repo_healthy = await repository.health_check()
    checkpointer_healthy = await checkpointer.health_check()
    
    if postgres_healthy and redis_healthy and repo_healthy and checkpointer_healthy:
        return {"status": "ok"}
    else:
        return {"status": "degraded"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}