"""
REST routes for active flows and admission control decisions.
"""

from fastapi import APIRouter
from typing import List
from backend.models.schemas import FlowItem
from backend.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/api/flows", tags=["flows"])


@router.get("", response_model=List[FlowItem])
def list_active_flows():
    """Returns active network flows with 5-tuple, classification, queue, rate, and admission status."""
    return telemetry_service.get_active_flows()
