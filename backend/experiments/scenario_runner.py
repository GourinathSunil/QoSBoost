"""
QoSBoost Scenario Runner and Evaluation Orchestrator.
Exposes benchmark executions for both live Mininet and simulated scenarios.
"""

from typing import Any, Dict
from network.scenario import (
    run_scenario,
    save_baseline_run,
    build_comparison_report,
    export_charts,
)


def execute_evaluation_experiment(duration_seconds: int = 65) -> Dict[str, Any]:
    """
    Executes a complete comparative experiment (QoS OFF vs QoS ON)
    and returns metrics, trajectories, and percentage improvements.
    """
    return build_comparison_report(duration_seconds=duration_seconds)
