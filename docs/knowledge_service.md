# Knowledge Service

## Query Parsing
The Knowledge Service bridges the gap between natural language and structured JSON data (`airport_data.json`). It bypasses the vector database, parsing the query for exact category matches and specific POI IDs.

## Count / Locate / List Logic
The service performs explicit database-like operations:
*   **Count:** "How many food courts are in Terminal 2?" -> Filters by `category='food_court'` and returns `len()`.
*   **Locate:** "Where is Starbucks?" -> Looks up the exact coordinate/node ID for 'Starbucks'.
*   **List:** "Show me all lounges." -> Returns a structured array of all POIs matching the 'lounge' classification.

## When It Is Used
The Orchestrator routes to the Knowledge Service when the user query requires absolute deterministic facts rather than semantic guidelines. It is used for operational hours, facility exact locations, and aggregate queries (counting, listing) that vector search handles poorly.
