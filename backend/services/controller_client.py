r"""
QoSBoost Ryu Controller REST Client.

Implements the REST interface between the FastAPI backend and the Ryu SDN controller:
1. Standard `ryu.app.ofctl_rest` endpoints:
   - GET /stats/switches
   - GET /stats/flow/{dpid}
   - GET /stats/port/{dpid}
   - GET /stats/meter/{dpid}
2. QoSBoost custom WSGI endpoints:
   - GET  /qosboost/status
   - POST /qosboost/policy
   - GET  /qosboost/flows
   - POST /qosboost/queues
"""

import httpx
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("qosboost.backend.controller_client")


class RyuControllerClient:
    """REST Client communicating with Ryu OpenFlow 1.3 controller."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout: float = 2.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.is_connected = False

    async def check_health(self) -> bool:
        """Verifies if the Ryu controller REST service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/stats/switches")
                self.is_connected = (res.status_code == 200)
                return self.is_connected
        except Exception:
            self.is_connected = False
            return False

    async def get_switches(self) -> List[int]:
        """Queries active switch DPIDs connected to Ryu."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/stats/switches")
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.debug("Failed querying switches from Ryu: %s", e)
        return []

    async def get_flow_stats(self, dpid: int) -> List[Dict[str, Any]]:
        """Queries OpenFlow flow stats on a specific datapath via ofctl_rest."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/stats/flow/{dpid}")
                if res.status_code == 200:
                    data = res.json()
                    return data.get(str(dpid), [])
        except Exception as e:
            logger.debug("Failed querying flow stats for dpid %s: %s", dpid, e)
        return []

    async def get_port_stats(self, dpid: int) -> List[Dict[str, Any]]:
        """Queries port throughput and drop statistics from Ryu ofctl_rest."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/stats/port/{dpid}")
                if res.status_code == 200:
                    data = res.json()
                    return data.get(str(dpid), [])
        except Exception as e:
            logger.debug("Failed querying port stats for dpid %s: %s", dpid, e)
        return []

    async def push_policy_to_controller(self, policy: Dict[str, Any]) -> bool:
        """Pushes updated QoS policies to the custom Ryu WSGI endpoint."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/qosboost/policy", json=policy)
                return res.status_code in (200, 201)
        except Exception as e:
            logger.debug("Could not push policy to Ryu controller (%s). Operating in standalone mode.", e)
            return False


controller_client = RyuControllerClient()
