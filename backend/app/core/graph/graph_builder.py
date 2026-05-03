import networkx as nx

from app.core.graph.airport_data import EDGES, NODES


def build_airport_graph() -> nx.Graph:
    g = nx.Graph()
    for node_id, meta in NODES.items():
        g.add_node(node_id, **meta)
    for a, b, minutes in EDGES:
        g.add_edge(a, b, minutes=minutes)
    return g
