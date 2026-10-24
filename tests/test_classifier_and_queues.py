"""
Unit tests for Phase 4: Classification and Queue Management.
"""

from controller.classifier import Flow5Tuple, TrafficClassifier
from controller.queue_manager import QueueManager


def test_rule_based_classification():
    classifier = TrafficClassifier()

    # 1. VoIP SIP (5060)
    flow_sip = Flow5Tuple(
        proto="udp", src_ip="10.0.0.1", src_port=5060, dst_ip="10.0.0.6", dst_port=5060
    )
    assert classifier.classify(flow_sip) == "voice"

    # 2. VoIP Direct Media (5004)
    flow_voice = Flow5Tuple(
        proto="udp", src_ip="10.0.0.1", src_port=49152, dst_ip="10.0.0.6", dst_port=5004
    )
    assert classifier.classify(flow_voice) == "voice"

    # 3. Video stream (5002)
    flow_video = Flow5Tuple(
        proto="udp", src_ip="10.0.0.2", src_port=52345, dst_ip="10.0.0.6", dst_port=5002
    )
    assert classifier.classify(flow_video) == "video"

    # 4. Web HTTP (80) & HTTPS (443)
    flow_http = Flow5Tuple(
        proto="tcp", src_ip="10.0.0.3", src_port=38210, dst_ip="10.0.0.6", dst_port=80
    )
    assert classifier.classify(flow_http) == "web"

    flow_https = Flow5Tuple(
        proto="tcp", src_ip="10.0.0.3", src_port=38212, dst_ip="10.0.0.6", dst_port=443
    )
    assert classifier.classify(flow_https) == "web"

    # 5. Bulk iperf3 (5201)
    flow_bulk = Flow5Tuple(
        proto="tcp", src_ip="10.0.0.4", src_port=41000, dst_ip="10.0.0.6", dst_port=5201
    )
    assert classifier.classify(flow_bulk) == "bulk"


def test_dscp_classification():
    classifier = TrafficClassifier()

    # Arbitrary port with DSCP 46 (Expedited Forwarding) -> voice
    flow_custom = Flow5Tuple(
        proto="udp", src_ip="10.0.0.1", src_port=9999, dst_ip="10.0.0.6", dst_port=9999
    )
    assert classifier.classify(flow_custom, dscp=46) == "voice"

    # Arbitrary port with DSCP 34 (AF41) -> video
    flow_video_dscp = Flow5Tuple(
        proto="udp", src_ip="10.0.0.2", src_port=8888, dst_ip="10.0.0.6", dst_port=8888
    )
    assert classifier.classify(flow_video_dscp, dscp=34) == "video"


def test_classifier_cache():
    classifier = TrafficClassifier()
    flow = Flow5Tuple(
        proto="udp", src_ip="10.0.0.1", src_port=5004, dst_ip="10.0.0.6", dst_port=5004
    )

    # Initial classification
    result1 = classifier.classify(flow)
    assert result1 == "voice"
    assert classifier.get_cache_size() >= 1

    # Second classification should hit cache
    result2 = classifier.classify(flow)
    assert result2 == "voice"


def test_queue_manager_rates():
    qm = QueueManager()
    info = qm.get_queue_info()

    # Check default queues exist
    assert 0 in info
    assert 1 in info
    assert 2 in info
    assert 3 in info

    assert info[1]["class"] == "voice"
    assert info[2]["class"] == "video"
    assert info[3]["class"] == "bulk"

    # Update queue rate
    qm.update_queue_rate(queue_id=3, min_rate_kbps=300, max_rate_kbps=4000)
    updated_info = qm.get_queue_info()
    assert updated_info[3]["min_rate_kbps"] == 300
    assert updated_info[3]["max_rate_kbps"] == 4000
