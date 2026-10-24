#!/usr/bin/env python3
"""
QoSBoost Controller Launcher.
Attempts to launch Ryu OpenFlow 1.3 controller manager; if Ryu is unavailable,
runs the standalone QoSBoost Controller Engine.
"""

import sys
import shutil
import subprocess
import logging
from controller.controller import QoSBoostControllerCore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("qosboost.controller.main")


def main():
    ryu_binary = shutil.which("ryu-manager")
    if ryu_binary:
        logger.info("Found ryu-manager at %s. Launching OpenFlow 1.3 controller on port 6653...", ryu_binary)
        cmd = [
            ryu_binary,
            "--ofp-tcp-listen-port", "6653",
            "--verbose",
            "controller.controller"
        ]
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            logger.info("Terminating Ryu controller...")
    else:
        logger.info("ryu-manager binary not found in PATH.")
        logger.info("Starting standalone QoSBoost Controller Core engine...")
        core = QoSBoostControllerCore()
        logger.info("Controller Core active: Classifier, QueueManager, Dynamic Allocator, Admission Control, and QoSRouter ready.")
        print("=" * 60)
        print(" QoSBoost Controller Core Online")
        print(" OpenFlow 1.3 Classification, Queues, and Routing active.")
        print("=" * 60)
        try:
            import time
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            logger.info("Controller stopped.")


if __name__ == "__main__":
    main()
