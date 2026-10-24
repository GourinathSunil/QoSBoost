r"""
QoSBoost Scenario Runner.

Executes reproducible before/after scenarios:
- Baseline run (QoS OFF): Collects voice latency, jitter, loss, and throughput under congestion.
- Prioritized run (QoS ON): Collects identical metrics with HTB queues, OF1.3 meters, and dynamic allocation.
- Computes percentage improvements and saves baseline comparison report.
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from network.traffic import SimulatedScenarioEngine

DEFAULT_BASELINE_PATH = os.path.join(os.path.dirname(__file__), "scenarios", "baseline_no_qos.json")


def run_scenario(qos_enabled: bool = False, duration_seconds: int = 60, step_interval: float = 1.0) -> Dict[str, Any]:
    """Runs a complete scripted scenario of specified duration and returns the time-series trajectory."""
    engine = SimulatedScenarioEngine(qos_enabled=qos_enabled)
    engine.start()
    
    trajectory: List[Dict[str, Any]] = []
    
    # We step through the duration
    for step in range(duration_seconds + 1):
        snapshot = engine.tick(elapsed=float(step))
        trajectory.append(snapshot)

    # Compute summary statistics
    # Congestion period is from t=15 to t=60
    congestion_steps = [s for s in trajectory if 15.0 <= s["timestamp"] <= 60.0]
    
    avg_voice_lat = sum(s["voice"]["latency_ms"] for s in congestion_steps) / max(1, len(congestion_steps))
    max_voice_lat = max(s["voice"]["latency_ms"] for s in congestion_steps)
    avg_voice_jit = sum(s["voice"]["jitter_ms"] for s in congestion_steps) / max(1, len(congestion_steps))
    max_voice_loss = max(s["voice"]["loss_percent"] for s in congestion_steps)
    avg_voice_loss = sum(s["voice"]["loss_percent"] for s in congestion_steps) / max(1, len(congestion_steps))

    summary = {
        "qos_enabled": qos_enabled,
        "duration_seconds": duration_seconds,
        "congestion_period_seconds": "15-60s",
        "avg_voice_latency_ms": round(avg_voice_lat, 2),
        "max_voice_latency_ms": round(max_voice_lat, 2),
        "avg_voice_jitter_ms": round(avg_voice_jit, 2),
        "avg_voice_loss_percent": round(avg_voice_loss, 2),
        "max_voice_loss_percent": round(max_voice_loss, 2),
    }

    return {
        "summary": summary,
        "trajectory": trajectory
    }


def save_baseline_run(output_file: str = DEFAULT_BASELINE_PATH) -> str:
    """Executes a baseline scenario (QoS OFF) and persists the result."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    result = run_scenario(qos_enabled=False, duration_seconds=65)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QoSBoost Scenario Runner")
    parser.add_argument("--baseline", action="store_true", help="Run and save baseline (QoS OFF) run")
    parser.add_argument("--qos", action="store_true", help="Run scenario with QoS ON")
    parser.add_argument("--output", default=DEFAULT_BASELINE_PATH, help="Output path for baseline JSON")
    args = parser.parse_args()

    if args.baseline or not args.qos:
        out = save_baseline_run(args.output)
        print(f"Successfully executed baseline run (QoS OFF) and saved to {out}")
    else:
        res = run_scenario(qos_enabled=True, duration_seconds=65)
        print("Summary with QoS ON:")
        print(json.dumps(res["summary"], indent=2))
