# Frontend Design

## Chat Interface
Built with React, the primary interface is a contextual chat window. It supports Markdown rendering and dynamic message updates. The interface adapts responsively, rendering as a side-panel on desktop and a full-screen view on mobile.

## Navigation UI
The frontend integrates a visual `TerminalMapView`. When the backend returns a `navigation` payload (containing a list of nodes/coordinates), the frontend automatically overlays the route onto the terminal map. The user sees both the visual path and the LLM's conversational instructions simultaneously.

## Backend Integration
*   **Payload Structure:** The frontend sends POST requests to `/api/chat` containing both the `message` and the user's implicit `location` state.
*   **Response Handling:** The API returns a structured JSON payload containing the `text` response and optional metadata tags (e.g., `intent`, `start`, `end`).
*   **State Hydration:** If a `start` and `end` node are present in the response, the frontend triggers the map component to re-render, creating a seamless transition from text query to visual guidance.
