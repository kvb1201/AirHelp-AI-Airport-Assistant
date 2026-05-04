from itertools import islice
from typing import Any

import networkx as nx


class PathFinder:
    """Shortest path on the airport graph (by minutes)."""

    def __init__(self, graph: nx.Graph):
        self._g = graph

    def find_k_paths(self, start: str, end: str, k: int = 3) -> list[dict[str, Any]]:
        """Up to k different simple paths, shortest first (by total minutes)."""
        if start not in self._g or end not in self._g:
            return []
        if not nx.has_path(self._g, start, end):
            return []
        out: list[dict[str, Any]] = []
        gen = nx.shortest_simple_paths(self._g, start, end, weight="minutes")
        for node_path in islice(gen, k):
            total = 0.0
            for u, v in zip(node_path, node_path[1:]):
                data = self._g.get_edge_data(u, v) or {}
                total += float(data.get("minutes", 0))
            edges: list[dict[str, Any]] = []
            for u, v in zip(node_path, node_path[1:]):
                data = self._g.get_edge_data(u, v) or {}
                minutes = int(data.get("minutes", 0))
                edges.append({"from": u, "to": v, "minutes": minutes})
            out.append(
                {
                    "ok": True,
                    "node_ids": list(node_path),
                    "total_minutes": int(round(total)),
                    "edges": edges,
                }
            )
        return out

    def find_path(self, start: str, end: str) -> dict[str, Any]:
        if start not in self._g or end not in self._g:
            return {"ok": False, "error": "unknown_node", "start": start, "end": end}
        if not nx.has_path(self._g, start, end):
            return {"ok": False, "error": "no_path", "start": start, "end": end}

        node_path = nx.shortest_path(self._g, start, end, weight="minutes")
        total = nx.shortest_path_length(self._g, start, end, weight="minutes")

        edges: list[dict[str, Any]] = []
        for u, v in zip(node_path, node_path[1:]):
            data = self._g.get_edge_data(u, v) or {}
            minutes = int(data.get("minutes", 0))
            edges.append({"from": u, "to": v, "minutes": minutes})

        return {
            "ok": True,
            "node_ids": node_path,
            "total_minutes": int(round(total)),
            "edges": edges,
        }
