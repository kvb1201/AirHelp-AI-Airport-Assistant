# Navigation Engine

## Graph-Based Routing
The Navigation Engine operates entirely independently of the LLMs. It uses deterministic graph algorithms (A* or Dijkstra) to calculate the shortest path through the terminal. This ensures physical accuracy and prevents LLM-generated hallucinations regarding spatial layout.

## Node Mapping
The physical terminal is modeled as a directed/undirected graph:
*   **Nodes:** Specific, physical coordinates (e.g., `t2_entrance`, `gate_12`, `starbucks_01`).
*   **Edges:** Walkable paths connecting nodes, weighted by physical distance or walking time.

## Route Generation
1.  **Resolution:** The Orchestrator provides a start node (user's current location) and an end node (resolved destination).
2.  **Pathfinding:** The engine calculates the optimal path.
3.  **Output:** It generates a structural payload containing the node sequence (`[node_A, node_B, node_C]`) for the frontend map UI, alongside turn-by-turn text instructions (e.g., "Walk 50m north to Gate 12").
