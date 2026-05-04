# Context Engine

## Context Structure
The Context Engine maintains a temporal state of the conversation. State is stored against a unique session ID and includes:
*   `current_location`: The physical Node ID of the user.
*   `last_referenced_entity`: The most recent POI or facility discussed.
*   `active_intent`: The ongoing multi-turn action (e.g., in the middle of a booking flow).

## Merge Logic
When a new query arrives, the Context Engine merges it with historical state. 
*   **Coreference Resolution:** If the user asks "Take me there," the engine replaces "there" with the `last_referenced_entity`.
*   **Location Persistence:** If the user does not specify a location, the engine automatically appends the `current_location` from the state.

## Signal Extraction
The engine scans incoming messages for explicit signals:
*   **Entities:** Specific locations ("Gate 12", "Starbucks").
*   **Categories:** Broad terms ("food", "bathroom").
*   **Procedural Flags:** Keywords indicating workflows ("check-in", "security").

## Decision Rules
1.  If a new entity is detected, update `last_referenced_entity`.
2.  If the input lacks entities but requires one (e.g., "navigate"), inject the `last_referenced_entity` into the orchestrator payload.
3.  If the session is idle for longer than the timeout period, clear the contextual history to prevent stale entity bleeding.
