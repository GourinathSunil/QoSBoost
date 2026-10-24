"""
QoSBoost FastAPI Backend Application.
The unified API and real-time streaming surface for the QoSBoost Dashboard.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.services.telemetry_service import telemetry_service
from backend.ws.broadcaster import manager
from backend.api.routes_telemetry import router as telemetry_router
from backend.api.routes_flows import router as flows_router
from backend.api.routes_policies import router as policies_router
from backend.api.routes_events import router as events_router
from backend.api.routes_scenarios import router as scenarios_router
from backend.api.routes_topology import router as topology_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("qosboost.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing QoSBoost database...")
    init_db()
    logger.info("Starting background telemetry stream loop...")
    await telemetry_service.start_loop()
    yield
    # Shutdown actions
    logger.info("Shutting down telemetry loop...")
    await telemetry_service.stop_loop()


app = FastAPI(
    title="QoSBoost API",
    description="SDN-Based QoS Management Backend API and Telemetry Broadcaster",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST Routers
app.include_router(telemetry_router)
app.include_router(flows_router)
app.include_router(policies_router)
app.include_router(events_router)
app.include_router(scenarios_router)
app.include_router(topology_router)


@app.get("/")
def root():
    return {
        "system": "QoSBoost SDN QoS Management",
        "status": "online",
        "docs_url": "/docs",
        "websocket_url": "/ws/telemetry"
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """Real-time 1-second JSON telemetry stream to frontend dashboard."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client can send pings or messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug("WebSocket connection closed: %s", e)
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
