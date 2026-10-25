"""
QoSBoost SQLite Database and Session Management.
Uses SQLModel / SQLAlchemy for light-weight, file-based persistence of telemetry and events.
"""

import os
from typing import List, Optional

from sqlmodel import Session, SQLModel, col, create_engine, select

from backend.models.schemas import (
    AdmissionDecisionDB,
    EventRecordDB,
    MetricSnapshotDB,
    PolicyConfigDB,
)

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


def save_policy_config(policy: PolicyConfigDB):
    """Persists a policy configuration snapshot to SQLite."""
    with Session(engine) as session:
        session.add(policy)
        session.commit()


def get_latest_policy_config() -> Optional[PolicyConfigDB]:
    """Queries the most recent policy configuration from SQLite."""
    with Session(engine) as session:
        statement = select(PolicyConfigDB).order_by(col(PolicyConfigDB.timestamp).desc()).limit(1)
        return session.exec(statement).first()


def save_admission_decision(decision: AdmissionDecisionDB):
    """Persists an admission control decision to SQLite."""
    with Session(engine) as session:
        session.add(decision)
        session.commit()


def get_recent_admission_decisions(limit: int = 50) -> List[AdmissionDecisionDB]:
    """Queries recent admission control decisions ordered by timestamp descending."""
    with Session(engine) as session:
        statement = (
            select(AdmissionDecisionDB)
            .order_by(col(AdmissionDecisionDB.timestamp).desc())
            .limit(limit)
        )
        return list(session.exec(statement).all())


def get_recent_snapshots(limit: int = 60) -> List[MetricSnapshotDB]:
    """Queries the most recent telemetry snapshots ordered by timestamp ascending."""
    with Session(engine) as session:
        statement = (
            select(MetricSnapshotDB).order_by(col(MetricSnapshotDB.timestamp).desc()).limit(limit)
        )
        results = session.exec(statement).all()
        return list(reversed(results))


def get_all_events(limit: int = 100) -> List[EventRecordDB]:
    """Queries recent audit events ordered by timestamp descending."""
    with Session(engine) as session:
        statement = select(EventRecordDB).order_by(col(EventRecordDB.timestamp).desc()).limit(limit)
        return list(session.exec(statement).all())
