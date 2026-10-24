r"""
QoSBoost QoS-Aware Routing Engine.

Utilizes NetworkX to model the multi-switch network graph and computes optimal forwarding
paths using a multi-metric cost function balancing propagation delay and link utilization.

Cost Function:
  Cost(link) = (alpha * delay_ms) + beta * (utilization / (1.0 - utilization + epsilon))

When the primary bottleneck link (s1 -> s2) experiences severe congestion (utilization > 80%),
the asymptotic queuing penalty triggers a dynamic reroute for real-time traffic to the alternate
path (s1 -> s3 -> s4), while bulk transfers remain on the primary path.
"""

import logging
from typing import Any, Dict, List, Tuple

import networkx as nx

logger = logging.getLogger("qosboost.controller.qos_router")


class QoSRouter:
    """NetworkX-based QoS Routing Engine."""

    def __init__(self, alpha: float = 1.0, beta: float = 8.0):
        self.alpha = alpha  # Weight on propagation delay
        self.beta = beta  # Weight on queuing congestion penalty
        self.graph = nx.DiGraph()
        self._build_topology_graph()

    def _build_topology_graph(self):
        """Initializes switches and links in NetworkX DiGraph."""
        # 4 Switches: s1 (Ingress), s2 (Core Bottleneck), s3 (Core Alternate), s4 (Egress)
        switches = ["s1", "s2", "s3", "s4"]
        for sw in switches:
            self.graph.add_node(sw)

        # Links definition: (u, v, base_delay_ms, capacity_mbps)
        links = [
            ("s1", "s2", 2.0, 10.0),  # Primary Bottleneck Path (10 Mbps, 2ms)
            ("s2", "s1", 2.0, 10.0),
            ("s1", "s3", 15.0, 20.0),  # Alternate Path (20 Mbps, 15ms base delay)
            ("s3", "s1", 15.0, 20.0),
            ("s2", "s4", 1.0, 100.0),  # Egress links (100 Mbps, 1ms)
            ("s4", "s2", 1.0, 100.0),
            ("s3", "s4", 1.0, 100.0),
            ("s4", "s3", 1.0, 100.0),
        ]

        for u, v, delay, bw in links:
            self.graph.add_edge(
                u,
                v,
                delay_ms=delay,
                bw_mbps=bw,
                utilization=0.0,
                cost=delay,  # Initial cost equals propagation delay
            )

    def update_link_utilization(self, u: str, v: str, utilization_ratio: float):
        """Updates utilization on link (u, v) and re-evaluates cost."""
        if not self.graph.has_edge(u, v):
            return

        u_clamped = max(0.0, min(0.99, utilization_ratio))
        edge = self.graph[u][v]
        edge["utilization"] = u_clamped

        # Asymptotic queuing penalty
        delay = edge["delay_ms"]
        congestion_penalty = self.beta * (u_clamped / (1.0 - u_clamped + 0.05))
        cost = (self.alpha * delay) + congestion_penalty
        edge["cost"] = round(cost, 3)

    def compute_path(
        self, src: str, dst: str, flow_class: str = "voice"
    ) -> Tuple[List[str], float, bool]:
        """
        Computes the optimal path for the given flow class.

        Returns:
            (path, total_cost, is_rerouted)
            where is_rerouted indicates if the alternate path was chosen over primary.
        """
        # Bulk traffic always takes the default primary path
        if flow_class in ("bulk", "web"):
            default_path = ["s1", "s2", "s4"]
            total_cost = sum(
                self.graph[u][v]["cost"] for u, v in zip(default_path[:-1], default_path[1:])
            )
            return default_path, total_cost, False

        # Real-time traffic uses Dijkstra with dynamic link costs
        try:
            path = nx.shortest_path(self.graph, source=src, target=dst, weight="cost")
            total_cost = sum(self.graph[u][v]["cost"] for u, v in zip(path[:-1], path[1:]))
            is_rerouted = "s3" in path
            return path, total_cost, is_rerouted
        except nx.NetworkXNoPath:
            # Fallback to default
            return ["s1", "s2", "s4"], 999.0, False

    def get_link_metrics(self) -> List[Dict[str, Any]]:
        """Returns the current state and cost of all links."""
        res = []
        for u, v in self.graph.edges:
            data = self.graph[u][v]
            res.append(
                {
                    "source": u,
                    "target": v,
                    "delay_ms": data["delay_ms"],
                    "bw_mbps": data["bw_mbps"],
                    "utilization": round(data["utilization"] * 100, 1),
                    "cost": data["cost"],
                }
            )
        return res
