"""
QoSBoost SQLite Database and Session Management.
Uses SQLModel / SQLAlchemy for light-weight, file-based persistence of telemetry and events.
"""

import os
from sqlmodel import SQLModel, create_engine, Session, select
from typing import List, Optional
from backend.models.schemas import MetricSnapshotDB, EventRecordDB

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "qosboost.db")
sqlite_url = f"sqlite:///{os.path.abspath(DB_FILE)}"

# connect_args={"check_same_thread": False} is required for SQLite with multi-threaded FastAPI
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


def init_db():
    """Creates database tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def save_snapshot(snapshot: MetricSnapshotDB):
    """Persists a single metric snapshot to SQLite."""
    with Session(engine) as session:
        session.add(snapshot)
        session.commit()


def save_event(event: EventRecordDB):
    """Persists an audit log event to SQLite."""
    with Session(engine) as session:
        session.add(event)
        session.commit()


def get_recent_snapshots(limit: int = 60) -> List[MetricSnapshotDB]:
    """Queries the most recent telemetry snapshots ordered by timestamp ascending."""
    with Session(engine) as session:
        statement = select(MetricSnapshotDB).order_by(MetricSnapshotDB.timestamp.desc()).limit(limit)
        results = session.exec(statement).all()
        return list(reversed(results))


def get_all_events(limit: int = 100) -> List[EventRecordDB]:
    """Queries recent audit events ordered by timestamp descending."""
    with Session(engine) as session:
        statement = select(EventRecordDB).order_by(EventRecordDB.timestamp.desc()).limit(limit)
        return list(session.exec(statement).all())
