# System Architecture

## High-Level System Overview
The AI Airport Assistant is a multi-layered, real-time conversational agent designed to handle deterministic navigation, unstructured knowledge retrieval, and structured factual queries. Rather than relying on a single monolithic LLM, the system routes tasks to specialized subsystems.

## End-to-End Data Flow
1. **User Input:** Raw text and the user's current spatial location (Node ID) are sent from the frontend.
2. **Context Enrichment:** The Context Engine retrieves the active session, merging current input with conversational history.
3. **Intent Normalization:** The input is classified (e.g., `navigation`, `information`, `procedure`) and key entities (categories, destinations) are extracted.
4. **Orchestration:** The Orchestrator routes the enriched query to:
   - **Navigation Engine:** If the intent requires pathfinding.
   - **Knowledge Service:** If the query is a strict factual lookup.
   - **RAG Service:** If the query requires searching unstructured terminal guidelines.
5. **Synthesis:** Subsystem results are passed to an LLM to generate a cohesive, grounded natural language response.
6. **Client Delivery:** The text response and any UI control payloads (e.g., map routes) are returned to the frontend.

## Component Breakdown
*   **Orchestrator (`orchestrator.py`):** The central traffic controller.
*   **Context Engine (`context_engine.py`):** Manages conversation state and entity coreferences.
*   **Navigation Engine (`navigation.py`):** Deterministic graph-based pathfinding.
*   **Knowledge Service (`knowledge.py`):** Structured JSON lookup for exact facts.
*   **RAG Service (`rag.py`):** Vector search over unstructured documents using ChromaDB.

## Why Hybrid Architecture is Used
LLMs are probabilistic, making them excellent at parsing natural language but poor at spatial reasoning and strict deterministic logic. A hybrid architecture mitigates this by:
*   Using strict graph algorithms (A*) for navigation instead of asking the LLM to invent routes.
*   Using rule-based intent parsing for explicit commands to ensure zero-latency accuracy.
*   Using RAG purely for unstructured data, preventing the LLM from hallucinating terminal rules.
