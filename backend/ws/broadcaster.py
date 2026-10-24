"""
QoSBoost WebSocket Connection and Telemetry Broadcaster.
"""

import json
import logging
from typing import Any, Dict, Set

from fastapi import WebSocket

logger = logging.getLogger("qosboost.backend.ws")


class ConnectionManager:
    """Manages connected WebSocket clients for real-time telemetry streaming."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected. Active clients: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(
            "WebSocket client disconnected. Remaining clients: %d", len(self.active_connections)
        )

    async def broadcast_json(self, data: Dict[str, Any]):
        """Pushes JSON payload to all active WebSocket connections."""
        if not self.active_connections:
            return

        text_data = json.dumps(data)
        stale_connections = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(text_data)
            except Exception as e:
                logger.debug("Failed sending to client: %s", e)
                stale_connections.append(connection)

        for stale in stale_connections:
            self.disconnect(stale)


manager = ConnectionManager()
