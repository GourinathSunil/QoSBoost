r"""
QoSBoost Ryu OpenFlow 1.3 Controller Application.

Coordinates:
- OpenFlow 1.3 event processing (SwitchFeatures, PacketIn, PortStatsReply, FlowStatsReply)
- L2 MAC address learning
- Dynamic traffic classification (first packet-in)
- OpenFlow flow rule installation with `set_queue` actions
- Periodic port stats polling (1s interval)
- Dynamic Bandwidth Allocation and Hysteresis
- Admission Control and QoS Routing
"""

import logging
from typing import Any, Dict, Optional

from controller.admission import AdmissionController
from controller.classifier import Flow5Tuple, TrafficClassifier
from controller.learning_switch import PureL2LearningTable
from controller.policy_engine import DynamicBandwidthAllocator, MeterManager
from controller.qos_router import QoSRouter
from controller.queue_manager import QueueManager

try:
    from ryu.app.wsgi import ControllerBase, route  # type: ignore
    from ryu.base import app_manager  # type: ignore
    from ryu.controller import ofp_event  # type: ignore
    from ryu.controller.handler import (  # type: ignore
        CONFIG_DISPATCHER,
        DEAD_DISPATCHER,
        MAIN_DISPATCHER,
        set_ev_cls,
    )
    from ryu.lib import hub  # type: ignore
    from ryu.lib.packet import ethernet, ipv4, packet, tcp, udp  # type: ignore
    from ryu.ofproto import ofproto_v1_3  # type: ignore
    from webob import Response  # type: ignore

    HAS_RYU = True
except ImportError:
    HAS_RYU = False
    app_manager = object  # type: ignore
    ControllerBase = object  # type: ignore

    def route(*args, **kwargs):  # type: ignore
        return lambda f: f

    def set_ev_cls(*args, **kwargs):  # type: ignore
        return lambda f: f


logger = logging.getLogger("qosboost.controller")


class QoSBoostControllerCore:
    """Core controller logic decoupled from Ryu networking eventlet loop."""

    def __init__(self):
        self.classifier = TrafficClassifier()
        self.queue_mgr = QueueManager()
        self.policy_engine = DynamicBandwidthAllocator(queue_manager=self.queue_mgr)
        self.meter_mgr = MeterManager()
        self.admission = AdmissionController()
        self.router = QoSRouter()
        self.learning_table = PureL2LearningTable()
        self.active_flow_stats: Dict[str, Any] = {}
        self.port_stats_cache: Dict[str, Any] = {}

    def handle_packet_in(
        self,
        dpid: str,
        in_port: int,
        src_mac: str,
        dst_mac: str,
        ip_proto: Optional[str] = None,
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
        src_port: Optional[int] = None,
        dst_port: Optional[int] = None,
        dscp: Optional[int] = None,
        packet_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Processes an OpenFlow PacketIn:
        1. Learns L2 forwarding port.
        2. If IP packet, classifies flow into voice/video/web/bulk (Rule-based or ML).
        3. Evaluates Admission Control for real-time flows.
        4. Assigns corresponding queue (0=web, 1=voice, 2=video, 3=bulk).
        5. Computes multi-metric QoS routing path.
        """
        out_port, should_install = self.learning_table.learn_and_route(
            dpid, src_mac, dst_mac, in_port
        )

        flow_class = "web"
        queue_id = 0
        path = ["s1", "s2", "s4"]
        admission_decision = "admit"
        admission_reason = "Headroom available."
        meter_id = None

        if ip_proto and src_ip and dst_ip and src_port and dst_port:
            flow_tuple = Flow5Tuple(
                proto=ip_proto, src_ip=src_ip, src_port=src_port, dst_ip=dst_ip, dst_port=dst_port
            )
            flow_class = self.classifier.classify(
                flow_tuple, dscp=dscp, packet_size=packet_size
            )

            # Map class to queue
            class_to_queue = {"web": 0, "voice": 1, "video": 2, "bulk": 3}
            queue_id = class_to_queue.get(flow_class, 0)

            # Admission Control check for voice and video
            if flow_class in ("voice", "video"):
                req_rate = 100.0 if flow_class == "voice" else 3000.0
                decision_obj = self.admission.evaluate(
                    flow_id=flow_tuple.to_key(),
                    class_name=flow_class,
                    requested_kbps=req_rate,
                    current_in_use_kbps=7000.0,
                )
                admission_decision = decision_obj.decision
                admission_reason = decision_obj.reason

                if admission_decision == "reject":
                    # Reject flow to protect SLAs
                    return {
                        "out_port": None,
                        "install_flow": False,
                        "class_name": flow_class,
                        "queue_id": queue_id,
                        "path": path,
                        "decision": "reject",
                        "reason": admission_reason,
                    }
                elif admission_decision == "downgrade":
                    # Downgrade to lower rate/queue
                    queue_id = 0

            # Attach OpenFlow 1.3 Meter to Bulk transfers or rogue flooders
            if flow_class == "bulk" or flow_tuple.dst_port == 5201:
                meter_id = 2  # bulk rate limiter
            elif flow_tuple.dst_port in (5005, 9999):
                meter_id = 1  # rogue flooder drop meter

            # QoS Routing path calculation
            path, cost, rerouted = self.router.compute_path("s1", "s4", flow_class=flow_class)

        return {
            "out_port": out_port,
            "install_flow": should_install,
            "class_name": flow_class,
            "queue_id": queue_id,
            "path": path,
            "decision": admission_decision,
            "reason": admission_reason,
            "meter_id": meter_id,
        }


if HAS_RYU:

    class QoSBoostRyuApp(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.core = QoSBoostControllerCore()
            self.datapaths = {}
            # Register WSGI REST endpoint for FastAPI Backend integration
            wsgi = kwargs.get("wsgi")
            if wsgi:
                wsgi.register(QoSBoostRestController, {"qosboost_app": self})
                logger.info("Registered QoSBoost WSGI REST Controller")
            self.monitor_thread = hub.spawn(self._monitor_loop)
            logger.info("QoSBoost RyuApp loaded successfully for OpenFlow 1.3")

        @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
        def _state_change_handler(self, ev):
            datapath = ev.datapath
            if ev.state == MAIN_DISPATCHER:
                if datapath.id not in self.datapaths:
                    self.datapaths[datapath.id] = datapath
                    logger.info("Switch connected: DPID %016x", datapath.id)
            elif ev.state == DEAD_DISPATCHER:
                if datapath.id in self.datapaths:
                    del self.datapaths[datapath.id]
                    logger.info("Switch disconnected: DPID %016x", datapath.id)

        @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
        def switch_features_handler(self, ev):
            datapath = ev.msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            # Install table-miss flow entry
            match = parser.OFPMatch()
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=match, instructions=inst)
            datapath.send_msg(mod)
            logger.info("Installed table-miss flow rule on DPID %016x", datapath.id)

        @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
        def _packet_in_handler(self, ev):
            """OpenFlow 1.3 PacketIn handler: parses packet, classifies, and installs set_queue flow."""
            msg = ev.msg
            datapath = msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            in_port = msg.match["in_port"]

            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocols(ethernet.ethernet)[0]

            if eth.ethertype == 0x88CC:
                # LLDP packet; ignore
                return

            src_mac = eth.src
            dst_mac = eth.dst
            dpid_str = f"{datapath.id:016x}"

            ip_proto = None
            src_ip = None
            dst_ip = None
            src_port = None
            dst_port = None
            dscp = None

            # Parse IPv4 and transport protocols
            ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
            if ipv4_pkt:
                src_ip = ipv4_pkt.src
                dst_ip = ipv4_pkt.dst
                dscp = (ipv4_pkt.tos >> 2) & 0x3F

                tcp_pkt = pkt.get_protocol(tcp.tcp)
                udp_pkt = pkt.get_protocol(udp.udp)
                if tcp_pkt:
                    ip_proto = "tcp"
                    src_port = tcp_pkt.src_port
                    dst_port = tcp_pkt.dst_port
                elif udp_pkt:
                    ip_proto = "udp"
                    src_port = udp_pkt.src_port
                    dst_port = udp_pkt.dst_port

            res = self.core.handle_packet_in(
                dpid=dpid_str,
                in_port=in_port,
                src_mac=src_mac,
                dst_mac=dst_mac,
                ip_proto=ip_proto,
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                dscp=dscp,
                packet_size=len(msg.data),
            )

            out_port = res.get("out_port")
            if out_port is None:
                # Dropped by Admission Control or unknown port
                return

            # Build Actions with set_queue
            actions = []
            queue_id = res.get("queue_id", 0)
            if queue_id is not None:
                actions.append(parser.OFPActionSetQueue(queue_id))
            actions.append(parser.OFPActionOutput(out_port))

            instructions = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

            # Apply OpenFlow 1.3 Meter instruction if present
            meter_id = res.get("meter_id")
            if meter_id:
                instructions.append(parser.OFPInstructionMeter(meter_id=meter_id))

            # Install flow rule if learned
            if res.get("install_flow") and ip_proto and src_ip and dst_ip:
                match_kwargs = {
                    "eth_type": 0x0800,
                    "ipv4_src": src_ip,
                    "ipv4_dst": dst_ip,
                    "ip_proto": 6 if ip_proto == "tcp" else 17,
                }
                if ip_proto == "tcp" and src_port and dst_port:
                    match_kwargs["tcp_src"] = src_port
                    match_kwargs["tcp_dst"] = dst_port
                elif ip_proto == "udp" and src_port and dst_port:
                    match_kwargs["udp_src"] = src_port
                    match_kwargs["udp_dst"] = dst_port

                match = parser.OFPMatch(**match_kwargs)
                mod = parser.OFPFlowMod(
                    datapath=datapath,
                    priority=100,
                    match=match,
                    instructions=instructions,
                    idle_timeout=30,
                    hard_timeout=120,
                )
                datapath.send_msg(mod)

            # Send PacketOut
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

        @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
        def _port_stats_reply_handler(self, ev):
            """Tracks port throughput, drops, and link utilization."""
            body = ev.msg.body
            dpid_str = f"{ev.msg.datapath.id:016x}"
            for stat in body:
                port_no = stat.port_no
                if port_no != ev.msg.datapath.ofproto.OFPP_LOCAL:
                    key = f"{dpid_str}:{port_no}"
                    self.core.port_stats_cache[key] = {
                        "rx_packets": stat.rx_packets,
                        "tx_packets": stat.tx_packets,
                        "rx_bytes": stat.rx_bytes,
                        "tx_bytes": stat.tx_bytes,
                        "rx_dropped": stat.rx_dropped,
                        "tx_dropped": stat.tx_dropped,
                    }

        @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
        def _flow_stats_reply_handler(self, ev):
            """Aggregates flow byte counters and active flow durations."""
            body = ev.msg.body
            dpid_str = f"{ev.msg.datapath.id:016x}"
            self.core.active_flow_stats[dpid_str] = [
                {
                    "byte_count": stat.byte_count,
                    "packet_count": stat.packet_count,
                    "duration_sec": stat.duration_sec,
                }
                for stat in body
            ]

        def _monitor_loop(self):
            """1-second periodic port, flow, and meter stats request loop."""
            while True:
                for dp in self.datapaths.values():
                    self._request_stats(dp)
                hub.sleep(1.0)

        def _request_stats(self, datapath):
            parser = datapath.ofproto_parser
            req_port = parser.OFPPortStatsRequest(datapath, 0, datapath.ofproto.OFPP_ANY)
            datapath.send_msg(req_port)
            req_flow = parser.OFPFlowStatsRequest(datapath)
            datapath.send_msg(req_flow)

    class QoSBoostRestController(ControllerBase):
        """Ryu WSGI REST endpoints for QoSBoost actions."""

        def __init__(self, req, link, data, **config):
            super().__init__(req, link, data, **config)
            self.qosboost_app = data["qosboost_app"]

        @route("qosboost", "/qosboost/status", methods=["GET"])
        def get_status(self, req, **kwargs):
            import json

            body = json.dumps(
                {
                    "status": "online",
                    "openflow_version": "1.3",
                    "switches_count": len(self.qosboost_app.datapaths),
                }
            )
            return Response(content_type="application/json", body=body)

        @route("qosboost", "/qosboost/queues", methods=["GET"])
        def get_queues(self, req, **kwargs):
            import json

            queues = self.qosboost_app.core.queue_mgr.get_queue_info()
            return Response(content_type="application/json", body=json.dumps(queues))

        @route("qosboost", "/qosboost/meters", methods=["GET"])
        def get_meters(self, req, **kwargs):
            import json

            meters = self.qosboost_app.core.meter_mgr.get_meter_stats()
            return Response(content_type="application/json", body=json.dumps(meters))

        @route("qosboost", "/qosboost/classifier", methods=["GET"])
        def get_classifier(self, req, **kwargs):
            import json

            info = self.qosboost_app.core.classifier.get_ml_info()
            return Response(content_type="application/json", body=json.dumps(info))

        @route("qosboost", "/qosboost/policy", methods=["POST"])
        def update_policy(self, req, **kwargs):
            import json

            try:
                _ = json.loads(req.body)
                # Re-apply policy to queues
                self.qosboost_app.core.classifier.load_rules()
                return Response(
                    content_type="application/json", body=json.dumps({"status": "applied"})
                )
            except Exception as e:
                return Response(status=500, body=str(e))
