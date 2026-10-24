"""
Unit tests for Phase 2: Topology and L2 Learning Switch logic.
"""

import pytest
from network.topology import get_topology_dict
from controller.learning_switch import PureL2LearningTable


def test_topology_structure():
    topo = get_topology_dict()
    assert "switches" in topo
    assert "hosts" in topo
    assert "links" in topo
    
    # 4 switches, 6 hosts
    assert len(topo["switches"]) == 4
    assert len(topo["hosts"]) == 6
    
    # Check bottleneck link presence
    bottlenecks = [link for link in topo["links"] if link.get("is_bottleneck")]
    assert len(bottlenecks) == 1
    assert bottlenecks[0]["source"] == "s1"
    assert bottlenecks[0]["target"] == "s2"
    assert bottlenecks[0]["bw_mbps"] == 10


def test_learning_switch_table():
    table = PureL2LearningTable()
    dpid = "0000000000000001"
    
    # 1. Packet from h1 (port 1) to unknown destination -> should flood (-1) and NOT install flow
    out_port, install_flow = table.learn_and_route(
        dpid=dpid,
        src_mac="00:00:00:00:00:01",
        dst_mac="00:00:00:00:00:06",
        in_port=1
    )
    assert out_port == -1
    assert install_flow is False
    
    # 2. Reply packet from h6 (port 6) to h1 -> destination is now known (port 1)!
    out_port, install_flow = table.learn_and_route(
        dpid=dpid,
        src_mac="00:00:00:00:00:06",
        dst_mac="00:00:00:00:00:01",
        in_port=6
    )
    assert out_port == 1
    assert install_flow is True

    # 3. Subsequent packet from h1 to h6 -> destination is known (port 6)!
    out_port, install_flow = table.learn_and_route(
        dpid=dpid,
        src_mac="00:00:00:00:00:01",
        dst_mac="00:00:00:00:00:06",
        in_port=1
    )
    assert out_port == 6
    assert install_flow is True

    # 4. Broadcast packet (FF:FF:FF:FF:FF:FF) -> flood
    out_port, install_flow = table.learn_and_route(
        dpid=dpid,
        src_mac="00:00:00:00:00:01",
        dst_mac="ff:ff:ff:ff:ff:ff",
        in_port=1
    )
    assert out_port == -1
    assert install_flow is False
