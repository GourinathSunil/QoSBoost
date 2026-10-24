#!/usr/bin/env python3
r"""
QoSBoost Network Topology Definition.
Defines a 6-host, 4-switch SDN topology with a calibrated 10 Mbps bottleneck link
and an alternate routed path.

Topology Architecture:
                       [Alternate Path: 20 Mbps, 15ms]
                      /----------------- s3 ---------------\
                     /                                       \
  h1 (VoIP)   ----\ /                                         \
  h2 (Video)  ---- s1                                          s4 ---- h6 (Receiver/Sink)
  h3 (Bulk1)  ----/ \                                         /
  h4 (Bulk2)  ----/  \                                       /
  h5 (Flood)  ---/    \----------------- s2 ----------------/
                       [Bottleneck Path: 10 Mbps, 2ms, HTB]
"""

import argparse
import json
import sys
from typing import Any, Dict

# Metadata representation of topology for frontend React Flow and backend graph
TOPOLOGY_METADATA: Dict[str, Any] = {
    "switches": [
        {
            "id": "s1",
            "label": "Switch 1 (Ingress)",
            "dpid": "0000000000000001",
            "x": 300,
            "y": 240,
            "role": "ingress",
        },
        {
            "id": "s2",
            "label": "Switch 2 (Bottleneck)",
            "dpid": "0000000000000002",
            "x": 580,
            "y": 140,
            "role": "core_bottleneck",
        },
        {
            "id": "s3",
            "label": "Switch 3 (Alternate)",
            "dpid": "0000000000000003",
            "x": 580,
            "y": 340,
            "role": "core_alternate",
        },
        {
            "id": "s4",
            "label": "Switch 4 (Egress)",
            "dpid": "0000000000000004",
            "x": 860,
            "y": 240,
            "role": "egress",
        },
    ],
    "hosts": [
        {
            "id": "h1",
            "label": "h1: VoIP Sender",
            "ip": "10.0.0.1",
            "mac": "00:00:00:00:00:01",
            "role": "voice",
            "x": 60,
            "y": 80,
        },
        {
            "id": "h2",
            "label": "h2: Video Sender",
            "ip": "10.0.0.2",
            "mac": "00:00:00:00:00:02",
            "role": "video",
            "x": 60,
            "y": 160,
        },
        {
            "id": "h3",
            "label": "h3: Bulk Sender 1",
            "ip": "10.0.0.3",
            "mac": "00:00:00:00:00:03",
            "role": "bulk",
            "x": 60,
            "y": 240,
        },
        {
            "id": "h4",
            "label": "h4: Bulk Sender 2",
            "ip": "10.0.0.4",
            "mac": "00:00:00:00:00:04",
            "role": "bulk",
            "x": 60,
            "y": 320,
        },
        {
            "id": "h5",
            "label": "h5: Rogue Flooder",
            "ip": "10.0.0.5",
            "mac": "00:00:00:00:00:05",
            "role": "flooder",
            "x": 60,
            "y": 400,
        },
        {
            "id": "h6",
            "label": "h6: Media Sink",
            "ip": "10.0.0.6",
            "mac": "00:00:00:00:00:06",
            "role": "receiver",
            "x": 1080,
            "y": 240,
        },
    ],
    "links": [
        # Host to Ingress Switch (100 Mbps, 1ms)
        {
            "source": "h1",
            "target": "s1",
            "src_port": 1,
            "dst_port": 1,
            "bw_mbps": 100,
            "delay_ms": 1.0,
            "is_bottleneck": False,
        },
        {
            "source": "h2",
            "target": "s1",
            "src_port": 1,
            "dst_port": 2,
            "bw_mbps": 100,
            "delay_ms": 1.0,
            "is_bottleneck": False,
        },
        {
            "source": "h3",
            "target": "s1",
            "src_port": 1,
            "dst_port": 3,
            "bw_mbps": 100,
            "delay_ms": 1.0,
            "is_bottleneck": False,
        },
        {
            "source": "h4",
            "target": "s1",
            "src_port": 1,
            "dst_port": 4,
            "bw_mbps": 100,
            "delay_ms": 1.0,
            "is_bottleneck": False,
        },
        {
            "source": "h5",
            "target": "s1",
            "src_port": 1,
            "dst_port": 5,
            "bw_mbps": 100,
            "delay_ms": 1.0,
            "is_bottleneck": False,
        },
        # Primary Bottleneck Link: s1-eth6 <-> s2-eth1 (10 Mbps, 2ms, HTB Queues)
        {
            "source": "s1",
            "target": "s2",
            "src_port": 6,
            "dst_port": 1,
            "bw_mbps": 10,
            "delay_ms": 2.0,
            "is_bottleneck": True,
            "bottleneck_port": "s1-eth6",
        },
        # Alternate Path: s1-eth7 <-> s3-eth1 (20 Mbps, 15ms higher latency)
        {
            "source": "s1",
            "target": "s3",
            "src_port": 7,
            "dst_port": 1,
            "bw_mbps": 20,
            "delay_ms": 15.0,
            "is_bottleneck": False,
        },
        # Core to Egress Links: s2-eth2 <-> s4-eth1, s3-eth2 <-> s4-eth2 (100 Mbps, 1ms)
        {
            "source": "s2",
            "target": "s4",
            "src_port": 2,
            "dst_port": 1,
            "bw_mbps": 100,
            "delay_ms": 1.0,
            "is_bottleneck": False,
        },
        {
            "source": "s3",
            "target": "s4",
            "src_port": 2,
            "dst_port": 2,
            "bw_mbps": 100,
            "delay_ms": 1.0,
            "is_bottleneck": False,
        },
        # Egress Switch to Receiver: s4-eth3 <-> h6-eth1 (100 Mbps, 1ms)
        {
            "source": "s4",
            "target": "h6",
            "src_port": 3,
            "dst_port": 1,
            "bw_mbps": 100,
            "delay_ms": 1.0,
            "is_bottleneck": False,
        },
    ],
}


def get_topology_dict() -> Dict[str, Any]:
    """Returns the JSON-serializable dictionary representation of the network topology."""
    return TOPOLOGY_METADATA


try:
    from mininet.cli import CLI
    from mininet.link import TCLink
    from mininet.log import info, setLogLevel
    from mininet.net import Mininet
    from mininet.node import OVSSwitch, RemoteController
    from mininet.topo import Topo

    HAS_MININET = True
except ImportError:
    HAS_MININET = False
    Topo = object  # type: ignore


if HAS_MININET:

    class QoSBoostTopo(Topo):
        """Mininet custom topology class for QoSBoost."""

        def build(self):
            # Create 4 Open vSwitch instances (OF1.3)
            s1 = self.addSwitch("s1", dpid="0000000000000001", protocols="OpenFlow13")
            s2 = self.addSwitch("s2", dpid="0000000000000002", protocols="OpenFlow13")
            s3 = self.addSwitch("s3", dpid="0000000000000003", protocols="OpenFlow13")
            s4 = self.addSwitch("s4", dpid="0000000000000004", protocols="OpenFlow13")

            # Create 6 hosts
            h1 = self.addHost("h1", ip="10.0.0.1/24", mac="00:00:00:00:00:01")
            h2 = self.addHost("h2", ip="10.0.0.2/24", mac="00:00:00:00:00:02")
            h3 = self.addHost("h3", ip="10.0.0.3/24", mac="00:00:00:00:00:03")
            h4 = self.addHost("h4", ip="10.0.0.4/24", mac="00:00:00:00:00:04")
            h5 = self.addHost("h5", ip="10.0.0.5/24", mac="00:00:00:00:00:05")
            h6 = self.addHost("h6", ip="10.0.0.6/24", mac="00:00:00:00:00:06")

            # Connect senders to s1 (ports 1 through 5 on s1)
            self.addLink(h1, s1, port1=1, port2=1, bw=100, delay="1ms")
            self.addLink(h2, s1, port1=1, port2=2, bw=100, delay="1ms")
            self.addLink(h3, s1, port1=1, port2=3, bw=100, delay="1ms")
            self.addLink(h4, s1, port1=1, port2=4, bw=100, delay="1ms")
            self.addLink(h5, s1, port1=1, port2=5, bw=100, delay="1ms")

            # Bottleneck Link: s1-port6 <-> s2-port1 (10 Mbps, 2ms delay, 100 packet buffer)
            self.addLink(s1, s2, port1=6, port2=1, bw=10, delay="2ms", max_queue_size=100)

            # Alternate Route: s1-port7 <-> s3-port1 (20 Mbps, 15ms delay)
            self.addLink(s1, s3, port1=7, port2=1, bw=20, delay="15ms", max_queue_size=200)

            # Core to Egress Links: s2-port2 <-> s4-port1, s3-port2 <-> s4-port2
            self.addLink(s2, s4, port1=2, port2=1, bw=100, delay="1ms")
            self.addLink(s3, s4, port1=2, port2=2, bw=100, delay="1ms")

            # Receiver Link: s4-port3 <-> h6-port1
            self.addLink(s4, h6, port1=3, port2=1, bw=100, delay="1ms")


def run_mininet(
    controller_ip: str = "127.0.0.1", controller_port: int = 6653, interactive: bool = False
):
    """Launches the Mininet network and connects to remote Ryu OpenFlow 1.3 controller."""
    if not HAS_MININET:
        print("ERROR: Mininet is not installed in the current environment.")
        print("To run native Mininet emulation, use an Ubuntu/Debian system or WSL2:")
        print("   sudo apt-get install -y mininet openvswitch-switch")
        print("   sudo python3 network/topology.py")
        sys.exit(1)

    setLogLevel("info")
    info("*** Building QoSBoost SDN Topology...\n")
    topo = QoSBoostTopo()

    controller = RemoteController(name="ryu_c0", ip=controller_ip, port=controller_port)

    net = Mininet(
        topo=topo,
        switch=OVSSwitch,
        controller=controller,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True,
    )

    info("*** Starting Network...\n")
    net.start()

    info("*** Verifying Initial Connectivity (Ping All)...\n")
    loss = net.pingAll()
    info(f"*** Initial Ping Loss: {loss}%\n")

    if interactive:
        info("*** Starting Mininet CLI (type 'exit' to quit)...\n")
        CLI(net)
        info("*** Stopping Mininet...\n")
        net.stop()
    else:
        return net


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QoSBoost Mininet Topology Runner")
    parser.add_argument("--json", action="store_true", help="Print topology metadata JSON and exit")
    parser.add_argument(
        "--controller-ip", default="127.0.0.1", help="Ryu controller IP (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--controller-port", type=int, default=6653, help="Ryu OpenFlow port (default: 6653)"
    )
    parser.add_argument(
        "--cli", action="store_true", help="Start interactive Mininet CLI after launch"
    )
    args = parser.parse_args()

    if args.json:
        print(json.dumps(get_topology_dict(), indent=2))
    else:
        run_mininet(
            controller_ip=args.controller_ip,
            controller_port=args.controller_port,
            interactive=args.cli,
        )
