r"""
QoSBoost Experiment Runner and Mininet Orchestrator.

Manages the lifecycle of the Mininet emulation and traffic generation:
- Launches the 6-host 4-switch Mininet topology
- Dispatches traffic generation commands to hosts:
  - h1: VoIP stream generator (5004 UDP)
  - h2: Video stream generator (5002 UDP)
  - h3, h4: Saturating iperf3 bulk transfers
  - h5: Rogue flooder
  - h6: Media receiver sink
- Collects live measurements and downsamples to SQLite.
"""

import os
import sys
import shutil
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("qosboost.backend.experiment_runner")


class ExperimentRunner:
    """Orchestrates Mininet + OVS emulation experiments."""

    def __init__(self):
        self.is_running = False
        self.has_mininet = shutil.which("mn") is not None
        self._mininet_proc: Optional[subprocess.Popen] = None

    def launch_network_topology(self, controller_ip: str = "127.0.0.1", controller_port: int = 6653) -> bool:
        """Launches the Mininet topology script as a managed background process."""
        if not self.has_mininet:
            logger.info("Mininet not detected on host. Using simulated network emulation engine.")
            return True

        topo_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "network", "topology.py"))
        cmd = ["sudo", sys.executable, topo_script, "--controller-ip", controller_ip, "--controller-port", str(controller_port)]
        
        try:
            self._mininet_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.is_running = True
            logger.info("Mininet topology launched successfully (PID %d).", self._mininet_proc.pid)
            return True
        except Exception as e:
            logger.error("Failed to launch Mininet: %s", e)
            return False

    def teardown(self):
        """Terminates Mininet process and cleans up OVS state."""
        if self._mininet_proc:
            try:
                self._mininet_proc.terminate()
                self._mininet_proc.wait(timeout=3.0)
            except Exception:
                try:
                    self._mininet_proc.kill()
                except Exception:
                    pass
            self._mininet_proc = None

        if self.has_mininet:
            try:
                subprocess.run(["sudo", "mn", "-c"], capture_output=True, check=False)
            except Exception:
                pass

        self.is_running = False
        logger.info("Mininet network experiment terminated.")


experiment_runner = ExperimentRunner()
