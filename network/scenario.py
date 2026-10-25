r"""
QoSBoost Scenario Runner.

Executes reproducible before/after scenarios:
- Baseline run (QoS OFF): Collects voice latency, jitter, loss, and throughput under congestion.
- Prioritized run (QoS ON): Collects identical metrics with HTB queues, OF1.3 meters, and dynamic allocation.
- Computes percentage improvements and saves baseline comparison report.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from network.traffic import SimulatedScenarioEngine

DEFAULT_BASELINE_PATH = os.path.join(os.path.dirname(__file__), "scenarios", "baseline_no_qos.json")


def run_scenario(
    qos_enabled: bool = False, duration_seconds: int = 60, step_interval: float = 1.0
) -> Dict[str, Any]:
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

    avg_voice_lat = sum(s["voice"]["latency_ms"] for s in congestion_steps) / max(
        1, len(congestion_steps)
    )
    max_voice_lat = max(s["voice"]["latency_ms"] for s in congestion_steps)
    avg_voice_jit = sum(s["voice"]["jitter_ms"] for s in congestion_steps) / max(
        1, len(congestion_steps)
    )
    max_voice_loss = max(s["voice"]["loss_percent"] for s in congestion_steps)
    avg_voice_loss = sum(s["voice"]["loss_percent"] for s in congestion_steps) / max(
        1, len(congestion_steps)
    )

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

    return {"summary": summary, "trajectory": trajectory}


def save_baseline_run(output_file: str = DEFAULT_BASELINE_PATH) -> str:
    """Executes a baseline scenario (QoS OFF) and persists the result."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    result = run_scenario(qos_enabled=False, duration_seconds=65)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    return output_file


def build_comparison_report(duration_seconds: int = 65) -> Dict[str, Any]:
    """
    Executes scenario twice (once QoS OFF, once QoS ON), computes percentage improvements,
    and returns full comparative report payload.
    """
    baseline_data = None
    if os.path.exists(DEFAULT_BASELINE_PATH):
        try:
            with open(DEFAULT_BASELINE_PATH, "r", encoding="utf-8") as f:
                baseline_data = json.load(f)
        except Exception:
            pass

    if not baseline_data:
        baseline_data = run_scenario(qos_enabled=False, duration_seconds=duration_seconds)
        save_baseline_run()

    qos_on_data = run_scenario(qos_enabled=True, duration_seconds=duration_seconds)

    base_summary = baseline_data["summary"]
    qos_summary = qos_on_data["summary"]

    lat_imp = (
        (base_summary["avg_voice_latency_ms"] - qos_summary["avg_voice_latency_ms"])
        / max(0.1, base_summary["avg_voice_latency_ms"])
    ) * 100.0
    jit_imp = (
        (base_summary["avg_voice_jitter_ms"] - qos_summary["avg_voice_jitter_ms"])
        / max(0.1, base_summary["avg_voice_jitter_ms"])
    ) * 100.0
    loss_imp = (
        (base_summary["avg_voice_loss_percent"] - qos_summary["avg_voice_loss_percent"])
        / max(0.1, base_summary["avg_voice_loss_percent"])
    ) * 100.0

    return {
        "timestamp": round(sys.modules["time"].time(), 2) if "time" in sys.modules else 0.0,
        "baseline_off": base_summary,
        "qos_on": qos_summary,
        "improvement_percentages": {
            "latency_reduction_percent": round(lat_imp, 1),
            "jitter_reduction_percent": round(jit_imp, 1),
            "loss_elimination_percent": round(min(100.0, max(0.0, loss_imp)), 1),
        },
        "baseline_trajectory": baseline_data["trajectory"],
        "qos_on_trajectory": qos_on_data["trajectory"],
    }


def export_charts(
    report_data: Dict[str, Any],
    png_path: str = os.path.join(os.path.dirname(__file__), "scenarios", "evaluation_summary.png"),
    pdf_path: str = os.path.join(os.path.dirname(__file__), "scenarios", "evaluation_summary.pdf"),
) -> Tuple[str, str]:
    """
    Renders high-resolution comparative time-series overlay charts and exports
    to both PNG and PDF format.
    """
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive headless backend
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    os.makedirs(os.path.dirname(png_path), exist_ok=True)

    base_traj = report_data["baseline_trajectory"]
    qos_traj = report_data["qos_on_trajectory"]

    min_len = min(len(base_traj), len(qos_traj))
    base_traj = base_traj[:min_len]
    qos_traj = qos_traj[:min_len]

    times = [p["timestamp"] for p in base_traj]
    off_lat = [p["voice"]["latency_ms"] for p in base_traj]
    on_lat = [p["voice"]["latency_ms"] for p in qos_traj]

    off_jit = [p["voice"]["jitter_ms"] for p in base_traj]
    on_jit = [p["voice"]["jitter_ms"] for p in qos_traj]

    off_loss = [p["voice"]["loss_percent"] for p in base_traj]
    on_loss = [p["voice"]["loss_percent"] for p in qos_traj]

    fig, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
    plt.subplots_adjust(hspace=0.25)

    # 1. Voice Latency
    ax1 = axes[0]
    ax1.plot(times, off_lat, label="QoS OFF (FIFO Drop-tail)", color="#e5484d", linewidth=2.0)
    ax1.plot(times, on_lat, label="QoS ON (HTB Queues + OF1.3)", color="#22c55e", linewidth=2.5)
    ax1.axhline(30.0, color="#888888", linestyle="--", linewidth=1.2, label="SLA Target (30 ms)")
    ax1.set_ylabel("Latency (ms)", fontweight="bold")
    ax1.set_title("Voice Latency Comparison under 10 Mbps Bottleneck Congestion", fontsize=12, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left")

    # 2. Voice Jitter
    ax2 = axes[1]
    ax2.plot(times, off_jit, label="QoS OFF Jitter", color="#e5484d", linewidth=2.0)
    ax2.plot(times, on_jit, label="QoS ON Jitter", color="#22c55e", linewidth=2.5)
    ax2.axhline(10.0, color="#888888", linestyle="--", linewidth=1.2, label="Target Jitter (10 ms)")
    ax2.set_ylabel("Jitter (ms)", fontweight="bold")
    ax2.set_title("Voice Jitter Comparison", fontsize=12, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper left")

    # 3. Packet Loss
    ax3 = axes[2]
    ax3.plot(times, off_loss, label="QoS OFF Packet Loss", color="#e5484d", linewidth=2.0)
    ax3.plot(times, on_loss, label="QoS ON Packet Loss", color="#22c55e", linewidth=2.5)
    ax3.set_ylabel("Loss (%)", fontweight="bold")
    ax3.set_xlabel("Scenario Timeline (Seconds)", fontweight="bold")
    ax3.set_title("Voice Packet Loss Percentage", fontsize=12, fontweight="bold")
    ax3.grid(True, linestyle=":", alpha=0.6)
    ax3.legend(loc="upper left")

    # Annotations for congestion events
    for ax in axes:
        ax.axvspan(15, 60, color="#ffeedd", alpha=0.3)
        ax.text(37, ax.get_ylim()[1] * 0.9, "Congestion Period (Bulk + Flooder)",
                horizontalalignment="center", fontsize=9, color="#994400", style="italic")

    # Save PNG
    fig.savefig(png_path, dpi=300, bbox_inches="tight")

    # Save PDF
    with PdfPages(pdf_path) as pdf:
        pdf.savefig(fig, bbox_inches="tight")
        # Page 2: Summary metrics table
        fig_table = plt.figure(figsize=(8.5, 6))
        plt.axis("off")
        summary_text = (
            "QoSBoost Evaluation Report Summary\n"
            "===================================\n\n"
            f"Voice Latency: {report_data['baseline_off']['avg_voice_latency_ms']} ms (OFF) -> "
            f"{report_data['qos_on']['avg_voice_latency_ms']} ms (ON) | "
            f"Improvement: {report_data['improvement_percentages']['latency_reduction_percent']}%\n\n"
            f"Voice Jitter:  {report_data['baseline_off']['avg_voice_jitter_ms']} ms (OFF) -> "
            f"{report_data['qos_on']['avg_voice_jitter_ms']} ms (ON) | "
            f"Improvement: {report_data['improvement_percentages']['jitter_reduction_percent']}%\n\n"
            f"Packet Loss:   {report_data['baseline_off']['avg_voice_loss_percent']}% (OFF) -> "
            f"{report_data['qos_on']['avg_voice_loss_percent']}% (ON) | "
            f"Improvement: {report_data['improvement_percentages']['loss_elimination_percent']}%\n"
        )
        plt.text(0.1, 0.5, summary_text, fontsize=12, family="monospace")
        pdf.savefig(fig_table, bbox_inches="tight")
        plt.close(fig_table)

    plt.close(fig)
    return png_path, pdf_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QoSBoost Scenario Runner")
    parser.add_argument(
        "--baseline", action="store_true", help="Run and save baseline (QoS OFF) run"
    )
    parser.add_argument("--qos", action="store_true", help="Run scenario with QoS ON")
    parser.add_argument("--report", action="store_true", help="Generate full comparison report and export PNG/PDF")
    parser.add_argument(
        "--output", default=DEFAULT_BASELINE_PATH, help="Output path for baseline JSON"
    )
    args = parser.parse_args()

    if args.report:
        rep = build_comparison_report()
        png, pdf = export_charts(rep)
        print("Comparison report generated successfully:")
        print(f"  - PNG: {png}")
        print(f"  - PDF: {pdf}")
        print(json.dumps(rep["improvement_percentages"], indent=2))
    elif args.baseline or not args.qos:
        out = save_baseline_run(args.output)
        print(f"Successfully executed baseline run (QoS OFF) and saved to {out}")
    else:
        res = run_scenario(qos_enabled=True, duration_seconds=65)
        print("Summary with QoS ON:")
        print(json.dumps(res["summary"], indent=2))
