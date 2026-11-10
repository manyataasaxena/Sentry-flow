import asyncio
import time
from datetime import datetime

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ...core.logging import get_logger
from ...schemas.run import RunStatus
from .runs import _convert_seq, _events, _runs

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/ws", tags=["websocket"])


@router.websocket("/runs/{run_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    run_id: str,
    last_seq: int | None = Query(None),
) -> None:
    """Replay and stream run events over WebSocket."""
    await websocket.accept()
    sequence = last_seq or 0
    last_heartbeat = time.monotonic()
    logger.info("WebSocket connected", run_id=run_id, last_seq=sequence)

    try:
        while True:
            events = _events.get(run_id, [])
            new_events = [event for event in events if _convert_seq(event.get("seq", 0)) > sequence]
            for event in new_events:
                await websocket.send_json(event)
                sequence = _convert_seq(event.get("seq", sequence))

            run_data = _runs.get(run_id)
            status = run_data.get("status") if run_data else None
            if status in (RunStatus.COMPLETED, RunStatus.BLOCKED, RunStatus.FAILED, RunStatus.CANCELLED):
                if not any(_convert_seq(event.get("seq", 0)) > sequence for event in _events.get(run_id, [])):
                    break

            now = time.monotonic()
            if now - last_heartbeat >= 15:
                await websocket.send_json(
                    {
                        "type": "heartbeat",
                        "run_id": run_id,
                        "seq": sequence,
                        "ts": datetime.now().isoformat(),
                    }
                )
                last_heartbeat = now
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", run_id=run_id)
    finally:
        logger.info("WebSocket stream ended", run_id=run_id, last_seq=sequence)
