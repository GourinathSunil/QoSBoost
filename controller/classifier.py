r"""
QoSBoost Traffic Classifier.

Classifies incoming network flows into one of four classes:
- voice: Ultra-low latency, VoIP RTP streams, SIP (port 5060, 5004, RTP range, DSCP 46 EF)
- video: High-bandwidth real-time video feeds (ports 554, 1935, 5002, WebRTC range, DSCP 34 AF41)
- web: Interactive HTTP/HTTPS (ports 80, 443, 8080, 8443)
- bulk: High-throughput background transfers (iperf 5201, FTP 20/21)

Classification features:
- Hot-reloadable YAML rule set (config/policies.yaml)
- 5-tuple caching for instantaneous O(1) flow lookup
- Extensible ML classifier hook (Random Forest) for encrypted/unknown traffic
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ml.classifier_model import MLFlowClassifier

logger = logging.getLogger("qosboost.controller.classifier")

DEFAULT_POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "policies.yaml")


class Flow5Tuple:
    """Represents an IP 5-tuple."""

    def __init__(self, proto: str, src_ip: str, src_port: int, dst_ip: str, dst_port: int):
        self.proto = proto.lower()
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.dst_port = dst_port

    def to_key(self) -> str:
        return f"{self.proto}:{self.src_ip}:{self.src_port}->{self.dst_ip}:{self.dst_port}"

    def __repr__(self) -> str:
        return self.to_key()

    def __eq__(self, other) -> bool:
        return isinstance(other, Flow5Tuple) and self.to_key() == other.to_key()

    def __hash__(self) -> int:
        return hash(self.to_key())


class TrafficClassifier:
    """
    Dual-mode traffic classifier:
    1. Rule-based classifier (primary): inspects protocol, port, and DSCP against YAML rules.
    2. ML classifier (stretch): Random Forest prediction on statistical flow metrics.
    """

    def __init__(self, config_path: str = DEFAULT_POLICY_PATH):
        self.config_path = config_path
        self.rules: List[Dict[str, Any]] = []
        self.flow_cache: Dict[str, str] = {}  # 5-tuple string -> class_name
        self.ml_mode = False
        self.ml_classifier = MLFlowClassifier()
        self.load_rules()

    def load_rules(self) -> bool:
        """Loads or hot-reloads classification rules from the YAML configuration."""
        if not os.path.exists(self.config_path):
            logger.warning(
                "Policy configuration file not found at %s. Using built-in defaults.",
                self.config_path,
            )
            self._load_fallback_rules()
            return False

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.rules = data.get("rules", [])
                logger.info(
                    "Loaded %d classification rules from %s", len(self.rules), self.config_path
                )
                # Clear flow cache on rule reload
                self.flow_cache.clear()
                return True
        except Exception as e:
            logger.error("Failed to load rules from %s: %s", self.config_path, e)
            self._load_fallback_rules()
            return False

    def _load_fallback_rules(self):
        self.rules = [
            {
                "id": "voip-direct",
                "class_name": "voice",
                "protocol": "udp",
                "dst_ports": [5004, 5060, 5061],
            },
            {
                "id": "video-direct",
                "class_name": "video",
                "protocol": "udp",
                "dst_ports": [5002, 554, 1935],
            },
            {"id": "web-direct", "class_name": "web", "protocol": "tcp", "dst_ports": [80, 443]},
            {
                "id": "bulk-direct",
                "class_name": "bulk",
                "protocol": "tcp",
                "dst_ports": [5201, 5202],
            },
        ]

    def set_ml_mode(self, enabled: bool):
        """Enables or disables ML-based classification mode."""
        self.ml_mode = enabled
        logger.info("Classifier ML mode set to %s", enabled)

    def classify(
        self,
        flow: Flow5Tuple,
        dscp: Optional[int] = None,
        packet_size: Optional[int] = None,
        inter_arrival_time: Optional[float] = None,
    ) -> str:
        """
        Classifies a flow into 'voice', 'video', 'web', or 'bulk'.
        Checks fast 5-tuple cache first; if cache miss:
        - If ML mode enabled: evaluates Random Forest ML model on flow stats.
        - If Rule mode (default): evaluates DSCP and port rules. If unknown/encrypted,
          falls back to ML classifier prediction.
        """
        key = flow.to_key()
        if key in self.flow_cache:
            return self.flow_cache[key]

        # 1. DSCP Precedence Check
        if dscp is not None:
            if dscp == 46:  # Expedited Forwarding (EF)
                self.flow_cache[key] = "voice"
                return "voice"
            elif dscp in (34, 36, 38):  # Assured Forwarding 4x (AF41)
                self.flow_cache[key] = "video"
                return "video"

        # 2. If explicit ML mode is on, run Random Forest prediction
        if self.ml_mode:
            mean_pkt = float(packet_size or (200 if flow.dst_port in (5004, 5060) else 1400))
            pred_class, _ = self.ml_classifier.predict(
                mean_packet_size=mean_pkt,
                std_packet_size=20.0,
                mean_inter_arrival_time=float(inter_arrival_time or 0.01),
                std_inter_arrival_time=0.002,
                flow_duration=10.0,
                bytes_per_sec=float(mean_pkt * 100),
            )
            self.flow_cache[key] = pred_class
            logger.debug("ML classified flow %s as '%s'", key, pred_class)
            return pred_class

        # 3. Rule evaluation
        matched_class = None
        for rule in self.rules:
            if rule.get("protocol") and rule["protocol"].lower() != flow.proto:
                continue

            # Exact destination port match
            if "dst_ports" in rule and flow.dst_port in rule["dst_ports"]:
                matched_class = rule["class_name"]
                break

            # Exact source port match
            if "src_ports" in rule and flow.src_port in rule["src_ports"]:
                matched_class = rule["class_name"]
                break

            # Port range match
            if "port_ranges" in rule:
                for r_start, r_end in rule["port_ranges"]:
                    if r_start <= flow.dst_port <= r_end or r_start <= flow.src_port <= r_end:
                        matched_class = rule["class_name"]
                        break
                if matched_class:
                    break

        # 4. Unknown / Encrypted flows: Use ML Random Forest prediction
        if not matched_class:
            logger.info("Flow %s did not match standard rules. Applying ML classifier...", key)
            mean_pkt = float(packet_size or (1440 if flow.proto == "tcp" else 600))
            pred_class, conf = self.ml_classifier.predict(
                mean_packet_size=mean_pkt,
                std_packet_size=50.0,
                mean_inter_arrival_time=float(inter_arrival_time or 0.02),
                std_inter_arrival_time=0.005,
                flow_duration=5.0,
                bytes_per_sec=float(mean_pkt * 80),
            )
            matched_class = pred_class

        self.flow_cache[key] = matched_class
        logger.debug("Classified flow %s as '%s'", key, matched_class)
        return matched_class

    def classify_with_ml(
        self,
        flow: Flow5Tuple,
        mean_packet_size: float,
        std_packet_size: float,
        mean_inter_arrival_time: float,
        std_inter_arrival_time: float,
        flow_duration: float,
        bytes_per_sec: float,
    ) -> Tuple[str, float]:
        """Direct invocation of Random Forest ML classifier with full statistical features."""
        pred_class, confidence = self.ml_classifier.predict(
            mean_packet_size=mean_packet_size,
            std_packet_size=std_packet_size,
            mean_inter_arrival_time=mean_inter_arrival_time,
            std_inter_arrival_time=std_inter_arrival_time,
            flow_duration=flow_duration,
            bytes_per_sec=bytes_per_sec,
        )
        self.flow_cache[flow.to_key()] = pred_class
        return pred_class, confidence

    def get_ml_info(self) -> Dict[str, Any]:
        """Returns the ML model accuracy, confusion matrix, and feature importances."""
        info = self.ml_classifier.get_model_info()
        info["ml_mode_active"] = self.ml_mode
        return info

    def get_cache_size(self) -> int:
        return len(self.flow_cache)

    def clear_cache(self):
        self.flow_cache.clear()
