r"""
QoSBoost Queue Manager.

Configures and manages Linux Hierarchical Token Bucket (HTB) QoS queues on Open vSwitch
interfaces via `ovs-vsctl`.

Queue Mappings:
- Queue 0: 'web'   (Default class: min 1000 kbps, max 4000 kbps)
- Queue 1: 'voice' (Highest priority: min 200 kbps, max 500 kbps)
- Queue 2: 'video' (Medium priority: min 2500 kbps, max 4500 kbps)
- Queue 3: 'bulk'  (Scavenger/Lowest: min 500 kbps, dynamic ceiling)

Provides:
- Idempotent queue provisioning
- Dynamic live queue rate adjustment without restarting switches
- Clean teardown on shutdown
- Platform-aware fallback for non-Linux simulation
"""

import os
import shutil
import logging
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger("qosboost.controller.queue_manager")


class QueueManager:
    """Manages OVS HTB queues for QoS traffic classes."""

    def __init__(self, bottleneck_port: str = "s1-eth6"):
        self.bottleneck_port = bottleneck_port
        self.has_ovs_vsctl = shutil.which("ovs-vsctl") is not None
        # In-memory shadow state for rates (in kbps)
        self.active_queues: Dict[int, Dict[str, int]] = {
            0: {"class": "web", "min_rate_kbps": 1000, "max_rate_kbps": 4000},
            1: {"class": "voice", "min_rate_kbps": 200, "max_rate_kbps": 500},
            2: {"class": "video", "min_rate_kbps": 2500, "max_rate_kbps": 4500},
            3: {"class": "bulk", "min_rate_kbps": 500, "max_rate_kbps": 8000},
        }

    def setup_queues(self, port_name: Optional[str] = None) -> bool:
        """
        Configures HTB QoS and queues 0..3 on the specified OVS port.
        Idempotent: destroys prior QoS record before applying new configuration.
        """
        port = port_name or self.bottleneck_port
        logger.info("Configuring HTB QoS queues on port '%s'...", port)

        if not self.has_ovs_vsctl:
            logger.info("ovs-vsctl not available (Simulated mode). Applying shadow queue configurations.")
            return True

        # Clear existing QoS on port
        self.destroy_queues(port)

        try:
            # Build ovs-vsctl command:
            # ovs-vsctl -- set port <port> qos=@newqos \
            #   -- --id=@newqos create qos type=linux-htb other-config:max-rate=10000000 queues=0=@q0,1=@q1,2=@q2,3=@q3 \
            #   -- --id=@q0 create queue other-config:min-rate=1000000 other-config:max-rate=4000000 \
            #   -- --id=@q1 create queue other-config:min-rate=200000 other-config:max-rate=500000 \
            #   -- --id=@q2 create queue other-config:min-rate=2500000 other-config:max-rate=4500000 \
            #   -- --id=@q3 create queue other-config:min-rate=500000 other-config:max-rate=8000000
            cmd = [
                "sudo", "ovs-vsctl", "--",
                "set", "port", port, "qos=@newqos",
                "--", "--id=@newqos", "create", "qos", "type=linux-htb",
                "other-config:max-rate=10000000",
                "queues=0=@q0,1=@q1,2=@q2,3=@q3",
                "--", "--id=@q0", "create", "queue",
                f"other-config:min-rate={self.active_queues[0]['min_rate_kbps'] * 1000}",
                f"other-config:max-rate={self.active_queues[0]['max_rate_kbps'] * 1000}",
                "--", "--id=@q1", "create", "queue",
                f"other-config:min-rate={self.active_queues[1]['min_rate_kbps'] * 1000}",
                f"other-config:max-rate={self.active_queues[1]['max_rate_kbps'] * 1000}",
                "--", "--id=@q2", "create", "queue",
                f"other-config:min-rate={self.active_queues[2]['min_rate_kbps'] * 1000}",
                f"other-config:max-rate={self.active_queues[2]['max_rate_kbps'] * 1000}",
                "--", "--id=@q3", "create", "queue",
                f"other-config:min-rate={self.active_queues[3]['min_rate_kbps'] * 1000}",
                f"other-config:max-rate={self.active_queues[3]['max_rate_kbps'] * 1000}",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Successfully established HTB queues on %s: %s", port, res.stdout.strip())
            return True
        except Exception as e:
            logger.warning("Could not execute ovs-vsctl for queue setup: %s. Continuing in simulated queue mode.", e)
            return False

    def update_queue_rate(self, queue_id: int, min_rate_kbps: Optional[int] = None, max_rate_kbps: Optional[int] = None, port_name: Optional[str] = None) -> bool:
        """
        Dynamically adjusts bandwidth limits on a specific queue.
        Used by the Dynamic Bandwidth Allocation engine during congestion.
        """
        if queue_id not in self.active_queues:
            logger.error("Queue %d does not exist.", queue_id)
            return False

        if min_rate_kbps is not None:
            self.active_queues[queue_id]["min_rate_kbps"] = min_rate_kbps
        if max_rate_kbps is not None:
            self.active_queues[queue_id]["max_rate_kbps"] = max_rate_kbps

        logger.info("Adjusted Queue %d (%s) limits: min=%d kbps, max=%d kbps",
                    queue_id, self.active_queues[queue_id]["class"],
                    self.active_queues[queue_id]["min_rate_kbps"],
                    self.active_queues[queue_id]["max_rate_kbps"])

        if not self.has_ovs_vsctl:
            return True

        # In OVS, dynamic updates can be executed via:
        # ovs-vsctl set queue <queue-uuid> other-config:max-rate=<rate>
        # Re-applying setup_queues is guaranteed idempotent and updates all queues cleanly
        return self.setup_queues(port_name or self.bottleneck_port)

    def destroy_queues(self, port_name: Optional[str] = None):
        """Clears all QoS records on the port."""
        port = port_name or self.bottleneck_port
        if not self.has_ovs_vsctl:
            return

        try:
            subprocess.run(["sudo", "ovs-vsctl", "clear", "port", port, "qos"], capture_output=True, check=False)
            subprocess.run(["sudo", "ovs-vsctl", "--all", "destroy", "qos"], capture_output=True, check=False)
            subprocess.run(["sudo", "ovs-vsctl", "--all", "destroy", "queue"], capture_output=True, check=False)
            logger.info("Cleared QoS records on %s", port)
        except Exception as e:
            logger.debug("destroy_queues: %s", e)

    def get_queue_info(self) -> Dict[int, Dict[str, Any]]:
        """Returns active queue limits and class mappings."""
        return dict(self.active_queues)
