"""
QoSBoost Telemetry and Orchestration Service.

Maintains:
- 1-second periodic telemetry polling/simulation
- In-memory circular buffer (rolling window of 120 seconds)
- SQLite persistence of downsampled historical metrics
- Active flow table tracking 5-tuples and QoS queues
- WebSocket live broadcasting
"""

import time
import asyncio
import logging
from typing import List, Dict, Any, Optional
from collections import deque

from backend.models.schemas import MetricSnapshot, MetricSnapshotDB, FlowItem, EventRecordDB
from backend.database import save_snapshot, save_event
from backend.ws.broadcaster import manager
from network.traffic import SimulatedScenarioEngine

logger = logging.getLogger("qosboost.backend.telemetry")


class TelemetryService:
    def __init__(self, buffer_size: int = 120):
        self.buffer_size = buffer_size
        self.history: deque = deque(maxlen=buffer_size)
        self.qos_enabled = True
        self.scenario_engine = SimulatedScenarioEngine(qos_enabled=self.qos_enabled)
        self.scenario_running = False
        self.scenario_start_time = 0.0
        self._loop_task: Optional[asyncio.Task] = None
        self.active_flows: Dict[str, FlowItem] = {}
        self._init_default_flows()

    def _init_default_flows(self):
        """Populates baseline active flows across the 4 classes."""
        self.active_flows = {
            "flow-voip-1": FlowItem(
                id="flow-voip-1",
                protocol="UDP",
                src_ip="10.0.0.1",
                src_port=49152,
                dst_ip="10.0.0.6",
                dst_port=5004,
                class_name="voice",
                queue_id=1,
                path="s1 -> s2 -> s4",
                rate_kbps=100.0,
                packets_count=1240,
                bytes_count=198400,
                decision="admit",
                last_seen=time.time()
            ),
            "flow-video-1": FlowItem(
                id="flow-video-1",
                protocol="UDP",
                src_ip="10.0.0.2",
                src_port=52345,
                dst_ip="10.0.0.6",
                dst_port=5002,
                class_name="video",
                queue_id=2,
                path="s1 -> s2 -> s4",
                rate_kbps=3200.0,
                packets_count=45100,
                bytes_count=59351600,
                decision="admit",
                last_seen=time.time()
            ),
            "flow-bulk-1": FlowItem(
                id="flow-bulk-1",
                protocol="TCP",
                src_ip="10.0.0.3",
                src_port=41002,
                dst_ip="10.0.0.6",
                dst_port=5201,
                class_name="bulk",
                queue_id=3,
                path="s1 -> s2 -> s4",
                rate_kbps=4800.0,
                packets_count=98200,
                bytes_count=147300000,
                decision="admit",
                last_seen=time.time()
            ),
            "flow-bulk-2": FlowItem(
                id="flow-bulk-2",
                protocol="TCP",
                src_ip="10.0.0.4",
                src_port=41004,
                dst_ip="10.0.0.6",
                dst_port=5202,
                class_name="bulk",
                queue_id=3,
                path="s1 -> s2 -> s4",
                rate_kbps=3000.0,
                packets_count=62100,
                bytes_count=93150000,
                decision="admit",
                last_seen=time.time()
            )
        }

    def set_qos_enabled(self, enabled: bool):
        self.qos_enabled = enabled
        self.scenario_engine.qos_enabled = enabled
        logger.info("QoS Master state toggled to: %s", enabled)

    def start_scenario(self, qos_enabled: Optional[bool] = None):
        """Starts a scripted 60-90 second demo scenario."""
        if qos_enabled is not None:
            self.set_qos_enabled(qos_enabled)
        self.scenario_running = True
        self.scenario_start_time = time.time()
        self.scenario_engine = SimulatedScenarioEngine(qos_enabled=self.qos_enabled)
        self.scenario_engine.start()
        logger.info("Demo scenario started (QoS=%s)", self.qos_enabled)

    def stop_scenario(self):
        self.scenario_running = False
        logger.info("Demo scenario stopped.")

    async def start_loop(self):
        """Starts the asynchronous 1-second telemetry publication loop."""
        if self._loop_task is None or self._loop_task.done():
            self._loop_task = asyncio.create_task(self._ticker())
            logger.info("Telemetry broadcasting loop started.")

    async def stop_loop(self):
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

    async def _ticker(self):
        """Ticks every 1.0 second, collects/generates metrics, updates history, and broadcasts."""
        t_counter = 0.0
        while True:
            try:
                t_counter += 1.0
                if self.scenario_running:
                    elapsed = time.time() - self.scenario_start_time
                    snapshot_raw = self.scenario_engine.tick(elapsed=elapsed)
                else:
                    # Idle steady-state telemetry
                    snapshot_raw = self.scenario_engine.tick(elapsed=t_counter % 10.0)

                # Format snapshot
                snapshot = MetricSnapshot(
                    timestamp=round(time.time(), 2),
                    qos_enabled=self.qos_enabled,
                    phase=snapshot_raw.get("phase", "Active Telemetry"),
                    link_utilization=snapshot_raw["link_utilization"],
                    active_flows_count=len(self.active_flows),
                    voice=snapshot_raw["voice"],
                    video=snapshot_raw["video"],
                    bulk=snapshot_raw["bulk"],
                    flooder=snapshot_raw["flooder"],
                    path=snapshot_raw["path"],
                    rerouted=snapshot_raw["rerouted"],
                    events=snapshot_raw.get("events", [])
                )

                # Add to in-memory rolling history
                self.history.append(snapshot.model_dump())

                # Persist downsampled (every 2 seconds) to SQLite
                if int(t_counter) % 2 == 0:
                    db_snap = MetricSnapshotDB(
                        timestamp=snapshot.timestamp,
                        qos_enabled=snapshot.qos_enabled,
                        link_utilization=snapshot.link_utilization,
                        voice_latency_ms=snapshot.voice.get("latency_ms", 0.0),
                        voice_jitter_ms=snapshot.voice.get("jitter_ms", 0.0),
                        voice_loss_percent=snapshot.voice.get("loss_percent", 0.0),
                        voice_throughput_kbps=snapshot.voice.get("throughput_kbps", 0.0),
                        video_throughput_kbps=snapshot.video.get("throughput_kbps", 0.0),
                        bulk_throughput_kbps=snapshot.bulk.get("throughput_kbps", 0.0),
                        active_path=snapshot.path
                    )
                    save_snapshot(db_snap)

                # Broadcast via WebSocket
                await manager.broadcast_json(snapshot.model_dump())

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in telemetry loop: %s", e)

            await asyncio.sleep(1.0)

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        return self.history[-1] if self.history else None

    def get_history(self, limit: int = 60) -> List[Dict[str, Any]]:
        return list(self.history)[-limit:]

    def get_active_flows(self) -> List[FlowItem]:
        return list(self.active_flows.values())


telemetry_service = TelemetryService()
