import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])

# Active WebSocket connections
_connections: dict[str, list[WebSocket]] = {}


@router.websocket("/ws/runs/{run_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    run_id: str,
    last_seq: int | None = Query(None),
) -> None:
    """WebSocket endpoint for real-time run events."""
    await websocket.accept()

    if run_id not in _connections:
        _connections[run_id] = []
    _connections[run_id].append(websocket)

    logger.info("WebSocket connected", run_id=run_id, last_seq=last_seq)

    try:
        # Send heartbeat every 15 seconds
        while True:
            await websocket.send_json({"type": "heartbeat", "ts": "2024-01-01T00:00:00Z"})
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", run_id=run_id)
    finally:
        _connections[run_id].remove(websocket)
        if not _connections[run_id]:
            del _connections[run_id]
