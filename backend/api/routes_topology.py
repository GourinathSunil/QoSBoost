"""
REST route for Network Topology graph metadata.
"""

from fastapi import APIRouter
from typing import Dict, Any
from network.topology import get_topology_dict

router = APIRouter(prefix="/api/topology", tags=["topology"])


@router.get("")
def get_topology() -> Dict[str, Any]:
    """Returns nodes, links, and coordinates for the 6-host 4-switch topology."""
    return get_topology_dict()
