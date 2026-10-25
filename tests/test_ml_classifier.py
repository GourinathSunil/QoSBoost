"""
Unit and integration tests for Traffic Classification and Random Forest ML Model (Section 3.1).
"""

import os
import pytest
from controller.classifier import Flow5Tuple, TrafficClassifier
from ml.classifier_model import MLFlowClassifier
from ml.dataset_generator import generate_flow_samples
from ml.train import train_and_evaluate


def test_rule_based_classification_and_dscp():
    classifier = TrafficClassifier()

    # Rule-based match: VoIP port 5004
    voip_flow = Flow5Tuple("udp", "10.0.0.1", 49152, "10.0.0.6", 5004)
    assert classifier.classify(voip_flow) == "voice"

    # DSCP 46 EF override
    custom_flow = Flow5Tuple("udp", "10.0.0.9", 33333, "10.0.0.6", 7777)
    assert classifier.classify(custom_flow, dscp=46) == "voice"

    # Rule-based match: Video port 5002
    video_flow = Flow5Tuple("udp", "10.0.0.2", 52345, "10.0.0.6", 5002)
    assert classifier.classify(video_flow) == "video"

    # Rule-based match: Bulk iperf3 5201
    bulk_flow = Flow5Tuple("tcp", "10.0.0.3", 41000, "10.0.0.6", 5201)
    assert classifier.classify(bulk_flow) == "bulk"


def test_5tuple_caching():
    classifier = TrafficClassifier()
    classifier.clear_cache()
    flow = Flow5Tuple("udp", "10.0.0.1", 50000, "10.0.0.6", 5004)

    assert classifier.get_cache_size() == 0
    res = classifier.classify(flow)
    assert res == "voice"
    assert classifier.get_cache_size() == 1

    # Second call returns cached result immediately
    assert classifier.classify(flow) == "voice"
    assert classifier.get_cache_size() == 1


def test_ml_dataset_generator():
    samples = generate_flow_samples("voice", count=20)
    assert len(samples) == 20
    assert samples[0]["traffic_class"] == "voice"
    assert samples[0]["mean_packet_size"] < 300.0


def test_ml_model_training_and_accuracy():
    report = train_and_evaluate()
    assert report["overall_accuracy"] >= 0.95
    assert len(report["confusion_matrix"]) == 4  # 4x4 matrix for voice, video, web, bulk
    assert "mean_packet_size" in report["feature_importances"]


def test_ml_inference_and_mode_toggle():
    classifier = TrafficClassifier()

    # Direct ML model inference
    pred_class, conf = classifier.classify_with_ml(
        Flow5Tuple("udp", "10.0.0.1", 1234, "10.0.0.2", 4321),
        mean_packet_size=180.0,
        std_packet_size=10.0,
        mean_inter_arrival_time=0.02,
        std_inter_arrival_time=0.001,
        flow_duration=60.0,
        bytes_per_sec=12000.0,
    )
    assert pred_class == "voice"
    assert conf > 0.80

    # ML Mode Toggle
    classifier.clear_cache()
    classifier.set_ml_mode(True)
    assert classifier.ml_mode is True

    # Unknown flow under ML mode should be classified by RF model
    unknown_flow = Flow5Tuple("udp", "10.0.0.7", 44444, "10.0.0.8", 55555)
    result = classifier.classify(unknown_flow, packet_size=1450)
    assert result in ("bulk", "video", "web", "voice")

    classifier.set_ml_mode(False)
    assert classifier.ml_mode is False
