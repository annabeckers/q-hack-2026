"""WebSocket data stream — push real-time data to frontend 3D visualizations.

The frontend useRealtimeData hook connects to this endpoint.
Push any typed data points for Globe3D, Scene3D, or GeoMap.
"""

import json
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Simple in-memory broadcast. Replace with Redis pub/sub for multi-worker.
_connections: set[WebSocket] = set()


@router.websocket("/stream")
async def data_stream(websocket: WebSocket):
    """WebSocket endpoint for streaming data to 3D visualizations.

    Clients receive: {"type": "point", "data": {...}}
    Clients can send: {"action": "subscribe", "channel": "geo|3d|globe"}
    """
    await websocket.accept()
    _connections.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            # Echo back to confirm subscription
            if msg.get("action") == "subscribe":
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": msg.get("channel", "all"),
                })
    except WebSocketDisconnect:
        _connections.discard(websocket)


async def broadcast_data(data: dict) -> None:
    """Broadcast data to all connected visualization clients."""
    if not _connections:
        return

    message = json.dumps(data)
    dead = set()
    for ws in _connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    _connections -= dead
