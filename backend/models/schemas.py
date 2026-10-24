"""
QoSBoost Data Models and Schemas (Pydantic v2 & SQLModel).
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, Field as PydanticField


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MetricSnapshotDB(SQLModel, table=True):
    """Persisted periodic metric snapshot."""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: float = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)
    qos_enabled: bool = Field(default=True)
    link_utilization: float = Field(default=0.0)
    voice_latency_ms: float = Field(default=0.0)
    voice_jitter_ms: float = Field(default=0.0)
    voice_loss_percent: float = Field(default=0.0)
    voice_throughput_kbps: float = Field(default=0.0)
    video_throughput_kbps: float = Field(default=0.0)
    bulk_throughput_kbps: float = Field(default=0.0)
    active_path: str = Field(default="Primary (s1 -> s2 -> s4)")


class EventRecordDB(SQLModel, table=True):
    """Audit log entry for dynamic adjustments, meters, and admission decisions."""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: float = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)
    event_type: str = Field(index=True)  # ADAPTATION, METER_DROP, ADMISSION, REROUTE
    message: str
    reason: Optional[str] = None
    before_value: Optional[str] = None
    after_value: Optional[str] = None


class FlowItem(BaseModel):
    """Active network flow descriptor."""
    id: str
    protocol: str
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    class_name: str
    queue_id: int
    path: str
    rate_kbps: float
    packets_count: int
    bytes_count: int
    decision: str = "admit"  # admit, downgrade, reject
    last_seen: float


class MetricSnapshot(BaseModel):
    """Real-time 1-second telemetry payload delivered via WebSocket and REST."""
    timestamp: float
    qos_enabled: bool
    phase: str
    link_utilization: float
    active_flows_count: int = 4
    voice: Dict[str, float]
    video: Dict[str, float]
    bulk: Dict[str, float]
    flooder: Dict[str, float]
    path: str
    rerouted: bool
    events: List[Dict[str, Any]] = PydanticField(default_factory=list)


class ClassPolicy(BaseModel):
    priority: int
    min_rate_kbps: int
    max_rate_kbps: int
    target_latency_ms: float
    target_jitter_ms: float
    max_loss_percent: float
    queue_id: int
    dscp: int


class PolicyProfile(BaseModel):
    name: str
    description: str
    classes: Dict[str, ClassPolicy]


class PolicyUpdateRequest(BaseModel):
    active_profile: str
    qos_enabled: Optional[bool] = True
    profiles: Optional[Dict[str, PolicyProfile]] = None
