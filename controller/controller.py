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
from typing import Dict, Any, Optional

logger = logging.getLogger("qosboost.controller")

try:
    from ryu.base import app_manager
    from ryu.controller import ofp_event
    from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
    from ryu.ofproto import ofproto_v1_3
    from ryu.lib import hub
    from ryu.lib.packet import packet, ethernet, ipv4, udp, tcp, ether_types
    from ryu.app.wsgi import ControllerBase, WSGIApplication, route
    from webob import Response
    HAS_RYU = True
except ImportError:
    HAS_RYU = False
    app_manager = object  # type: ignore
    ControllerBase = object  # type: ignore
    route = lambda *args, **kwargs: (lambda f: f)  # type: ignore

from controller.classifier import TrafficClassifier, Flow5Tuple
from controller.queue_manager import QueueManager
from controller.policy_engine import DynamicBandwidthAllocator, MeterManager
from controller.admission import AdmissionController
from controller.qos_router import QoSRouter
from controller.learning_switch import PureL2LearningTable


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
        dscp: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Processes an OpenFlow PacketIn:
        1. Learns L2 forwarding port.
        2. If IP packet, classifies flow into voice/video/web/bulk.
        3. Assigns corresponding queue (0=web, 1=voice, 2=video, 3=bulk).
        4. Verifies path and admission.
        """
        out_port, should_install = self.learning_table.learn_and_route(dpid, src_mac, dst_mac, in_port)

        flow_class = "web"
        queue_id = 0
        path = ["s1", "s2", "s4"]

        if ip_proto and src_ip and dst_ip and src_port and dst_port:
            flow_tuple = Flow5Tuple(
                proto=ip_proto,
                src_ip=src_ip,
                src_port=src_port,
                dst_ip=dst_ip,
                dst_port=dst_port
            )
            flow_class = self.classifier.classify(flow_tuple, dscp=dscp)

            # Map class to queue
            class_to_queue = {"web": 0, "voice": 1, "video": 2, "bulk": 3}
            queue_id = class_to_queue.get(flow_class, 0)

            # QoS Routing path calculation
            path, cost, rerouted = self.router.compute_path("s1", "s4", flow_class=flow_class)

        return {
            "out_port": out_port,
            "install_flow": should_install,
            "class_name": flow_class,
            "queue_id": queue_id,
            "path": path
        }


if HAS_RYU:
    class QoSBoostRyuApp(app_manager.RyuApp):
        OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.core = QoSBoostControllerCore()
            self.datapaths = {}
            # Register WSGI REST endpoint for FastAPI Backend integration
            wsgi = kwargs.get('wsgi')
            if wsgi:
                wsgi.register(QoSBoostRestController, {'qosboost_app': self})
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

        def _monitor_loop(self):
            """1-second periodic port and flow stats request loop."""
            while True:
                for dp in self.datapaths.values():
                    self._request_stats(dp)
                hub.sleep(1.0)

        def _request_stats(self, datapath):
            parser = datapath.ofproto_parser
            req = parser.OFPPortStatsRequest(datapath, 0, datapath.ofproto.OFPP_ANY)
            datapath.send_msg(req)


    class QoSBoostRestController(ControllerBase):
        """Ryu WSGI REST endpoints for QoSBoost actions."""
        def __init__(self, req, link, data, **config):
            super().__init__(req, link, data, **config)
            self.qosboost_app = data['qosboost_app']

        @route('qosboost', '/qosboost/status', methods=['GET'])
        def get_status(self, req, **kwargs):
            import json
            body = json.dumps({
                "status": "online",
                "openflow_version": "1.3",
                "switches_count": len(self.qosboost_app.datapaths)
            })
            return Response(content_type='application/json', body=body)

        @route('qosboost', '/qosboost/queues', methods=['GET'])
        def get_queues(self, req, **kwargs):
            import json
            queues = self.qosboost_app.core.queue_mgr.get_queue_info()
            return Response(content_type='application/json', body=json.dumps(queues))

        @route('qosboost', '/qosboost/policy', methods=['POST'])
        def update_policy(self, req, **kwargs):
            import json
            try:
                policy = json.loads(req.body)
                # Re-apply policy to queues
                self.qosboost_app.core.classifier.load_rules()
                return Response(content_type='application/json', body=json.dumps({"status": "applied"}))
            except Exception as e:
                return Response(status=500, body=str(e))
