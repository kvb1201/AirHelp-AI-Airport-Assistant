import networkx as nx

from app.core.graph.airport_data import EDGES, NODES


def _edge_touches_security(a: str, b: str) -> bool:
    ka = NODES.get(a, {}).get("kind")
    kb = NODES.get(b, {}).get("kind")
    return ka == "security" or kb == "security"


def build_airport_graph(security_queue_minutes: float = 0.0) -> nx.Graph:
    """
    Walking graph for routing. `security_queue_minutes` is added to every edge incident to a
    `security` node (same extra on each such edge for this query — see congestion service).
    """
    g = nx.Graph()
    for node_id, meta in NODES.items():
        g.add_node(node_id, **meta)
    extra = float(security_queue_minutes)
    for a, b, minutes in EDGES:
        m = float(minutes)
        if extra > 0 and _edge_touches_security(a, b):
            m += extra
        g.add_edge(a, b, minutes=m)
    return g
