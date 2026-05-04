# Orchestrator

## Routing Logic
The Orchestrator acts as the central router for the backend. It guarantees that specialized queries are handled by the appropriate engine rather than being blindly passed to the LLM.

## How Requests are Handled
1.  **Receive Payload:** The Orchestrator ingests the user message, session ID, and current location.
2.  **Context Pre-Processing:** It invokes the Context Engine to resolve missing entities (e.g., converting "How far is it?" to "How far is the Starbucks?").
3.  **Intent Classification:** It determines the primary action required.
4.  **Subsystem Invocation:** It executes the necessary service (Navigation, RAG, or Knowledge).
5.  **LLM Formatting:** It wraps the subsystem output in a strict prompt template and generates the final response text.

## Decision Hierarchy
The Orchestrator evaluates intents sequentially based on priority and deterministic safety:
1.  **Navigation (Highest Priority):** If the user says "take me to...", the orchestrator bypasses RAG and immediately invokes the Navigation Engine to calculate graph paths.
2.  **Knowledge Lookup:** If the query is factual (e.g., "Is Starbucks open?"), it queries the structured catalog.
3.  **RAG/Information:** If the query is policy-based (e.g., "Can I bring liquids?"), it queries the vector database.
4.  **Fallback (Lowest Priority):** Standard LLM response generation for generic chit-chat or unrecognized intents.
