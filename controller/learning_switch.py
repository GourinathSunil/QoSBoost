"""
QoSBoost OpenFlow 1.3 L2 Learning Switch.

Implements standard self-learning MAC table logic:
1. Installs table-miss flow entry (send to controller) on switch connection.
2. Learns source MAC to ingress port mapping upon packet-in.
3. If destination MAC is known, installs a precise flow entry with priority 1.
4. If destination MAC is unknown or broadcast/multicast, floods packet.

Designed to execute as a Ryu application (`RyuApp`) or directly within the QoSBoost controller.
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger("qosboost.controller.learning_switch")

# Try importing Ryu components if installed
try:
    from ryu.base import app_manager
    from ryu.controller import ofp_event
    from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
    from ryu.lib.packet import ether_types, ethernet, packet
    from ryu.ofproto import ofproto_v1_3

    HAS_RYU = True
except ImportError:
    HAS_RYU = False
    app_manager = object  # type: ignore


class PureL2LearningTable:
    """
    Pure Python L2 learning switch table logic.
    Decoupled from Ryu networking runtime so it can be verified with unit tests anywhere.
    """

    def __init__(self):
        # mac_to_port[dpid][mac_address] = port_no
        self.mac_to_port: Dict[str, Dict[str, int]] = {}

    def learn_and_route(
        self, dpid: str, src_mac: str, dst_mac: str, in_port: int
    ) -> Tuple[int, bool]:
        """
        Learns source MAC on in_port for datapath dpid, and determines forwarding port.

        Returns:
            (out_port, should_install_flow_rule)
            out_port: port number or -1 for FLOOD.
        """
        self.mac_to_port.setdefault(dpid, {})
        # Learn MAC location
        self.mac_to_port[dpid][src_mac] = in_port

        # Check if dst is broadcast/multicast or unknown
        if dst_mac.lower() in ("ff:ff:ff:ff:ff:ff", "01:00:5e:00:00:01") or dst_mac.startswith(
            "33:33"
        ):
            return -1, False  # Flood broadcast

        if dst_mac in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst_mac]
            return out_port, True  # Unicast: forward & install flow rule
        else:
            return -1, False  # Unknown unicast: flood


if HAS_RYU:

    class RyuL2LearningSwitch(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.learning_table = PureL2LearningTable()
            logger.info("RyuL2LearningSwitch initialized for OpenFlow 1.3")

        @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
        def switch_features_handler(self, ev):
            """Installs table-miss flow entry sending unhandled packets to controller."""
            datapath = ev.msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            # Priority 0 table-miss flow entry
            match = parser.OFPMatch()
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=match, instructions=inst)
            datapath.send_msg(mod)
            logger.info("Installed table-miss flow rule on Datapath %s", datapath.id)

        @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
        def packet_in_handler(self, ev):
            msg = ev.msg
            datapath = msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            in_port = msg.match["in_port"]

            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocols(ethernet.ethernet)[0]

            if eth.ethertype == ether_types.ETH_TYPE_LLDP:
                # Ignore LLDP packets
                return

            dpid = str(datapath.id)
            src = eth.src
            dst = eth.dst

            out_port, install_flow = self.learning_table.learn_and_route(dpid, src, dst, in_port)

            actions = []
            if out_port == -1:
                actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            else:
                actions = [parser.OFPActionOutput(out_port)]

            # Install a flow rule if destination was already learned
            if install_flow and out_port != -1:
                match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
                # Verify if we have a valid buffer_id
                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                    mod = parser.OFPFlowMod(
                        datapath=datapath,
                        buffer_id=msg.buffer_id,
                        priority=1,
                        match=match,
                        instructions=inst,
                    )
                    datapath.send_msg(mod)
                    return
                else:
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                    mod = parser.OFPFlowMod(
                        datapath=datapath, priority=1, match=match, instructions=inst
                    )
                    datapath.send_msg(mod)

            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data

            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=msg.buffer_id,
                in_port=in_port,
                actions=actions,
                data=data,
            )
            datapath.send_msg(out)
