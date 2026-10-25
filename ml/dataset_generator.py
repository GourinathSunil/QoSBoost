r"""
QoSBoost ML Dataset Generator.

Generates realistic network flow statistical feature datasets for the four QoSBoost traffic classes:
- voice: VoIP RTP streams (small uniform packets ~160-220B, tight ~20ms inter-arrival times, low bandwidth ~80-120 kbps)
- video: HD video streams (large packets ~1100-1400B, high packet rate ~3ms inter-arrival, ~2.5-4.5 Mbps)
- web: Interactive HTTP/HTTPS (variable packet size ~400-900B, bursty inter-arrival ~50-300ms, short durations)
- bulk: Saturating bulk TCP transfers (maximum MTU packets ~1440-1500B, sub-millisecond inter-arrival ~0.8ms, high throughput)

Features extracted per flow:
1. mean_packet_size (bytes)
2. std_packet_size (bytes)
3. mean_inter_arrival_time (seconds)
4. std_inter_arrival_time (seconds)
5. flow_duration (seconds)
6. bytes_per_sec (bytes/sec)
"""

import os
import random
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

DEFAULT_DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.csv")


def generate_flow_samples(class_name: str, count: int, random_seed: int = 42) -> List[Dict[str, float]]:
    """Generates synthetic flow summary records based on real Mininet traffic distributions."""
    np.random.seed(random_seed)
    random.seed(random_seed)
    samples = []

    for _ in range(count):
        if class_name == "voice":
            # G.711 / Opus VoIP stream: ~20ms packet intervals, 160-220B payloads
            mean_pkt = float(np.random.normal(180.0, 15.0))
            std_pkt = float(max(2.0, np.random.normal(12.0, 4.0)))
            mean_iat = float(max(0.015, np.random.normal(0.020, 0.002)))  # ~20ms
            std_iat = float(max(0.0005, np.random.normal(0.002, 0.0008)))
            duration = float(np.random.uniform(20.0, 120.0))
            bytes_sec = float(max(6000.0, np.random.normal(12500.0, 1500.0)))  # ~100 kbps

        elif class_name == "video":
            # 1080p / 720p H.264 video feed: ~1200B packets, ~3ms intervals, 3-4 Mbps
            mean_pkt = float(np.random.normal(1280.0, 70.0))
            std_pkt = float(max(20.0, np.random.normal(180.0, 30.0)))
            mean_iat = float(max(0.001, np.random.normal(0.0035, 0.0008)))  # ~3.5ms
            std_iat = float(max(0.0004, np.random.normal(0.0015, 0.0005)))
            duration = float(np.random.uniform(25.0, 180.0))
            bytes_sec = float(max(150000.0, np.random.normal(400000.0, 50000.0)))  # ~3.2 Mbps

        elif class_name == "web":
            # HTTP/HTTPS requests & responses: variable sizes, bursty intervals
            mean_pkt = float(np.random.normal(680.0, 160.0))
            std_pkt = float(max(50.0, np.random.normal(380.0, 60.0)))
            mean_iat = float(max(0.02, np.random.exponential(0.12)))  # bursty ~120ms
            std_iat = float(max(0.01, np.random.normal(0.08, 0.03)))
            duration = float(max(0.5, np.random.exponential(4.0)))  # short-lived
            bytes_sec = float(max(2000.0, np.random.normal(55000.0, 20000.0)))

        elif class_name == "bulk":
            # iperf3 TCP bulk downloads: full MTU ~1460-1500B, sub-ms TCP bursts
            mean_pkt = float(np.random.normal(1440.0, 35.0))
            std_pkt = float(max(5.0, np.random.normal(45.0, 15.0)))
            mean_iat = float(max(0.0002, np.random.normal(0.0009, 0.0002)))  # < 1ms
            std_iat = float(max(0.0001, np.random.normal(0.0005, 0.0001)))
            duration = float(np.random.uniform(15.0, 90.0))
            bytes_sec = float(max(500000.0, np.random.normal(1100000.0, 150000.0)))  # ~8.8 Mbps

        else:
            raise ValueError(f"Unknown traffic class: {class_name}")

        samples.append({
            "mean_packet_size": round(mean_pkt, 2),
            "std_packet_size": round(std_pkt, 2),
            "mean_inter_arrival_time": round(mean_iat, 6),
            "std_inter_arrival_time": round(std_iat, 6),
            "flow_duration": round(duration, 2),
            "bytes_per_sec": round(bytes_sec, 2),
            "traffic_class": class_name,
        })

    return samples


def generate_full_dataset(samples_per_class: int = 500, output_path: str = DEFAULT_DATASET_PATH) -> str:
    """Generates a balanced dataset across voice, video, web, bulk and saves to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    classes = ["voice", "video", "web", "bulk"]
    all_rows = []

    for idx, c in enumerate(classes):
        rows = generate_flow_samples(c, count=samples_per_class, random_seed=100 + idx * 37)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    # Shuffle
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    out = generate_full_dataset(samples_per_class=600)
    print(f"Generated ML flow dataset at {out} with 2400 samples.")
