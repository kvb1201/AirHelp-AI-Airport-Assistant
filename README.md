# AI Airport Companion
> Local LLM-powered personal assistant for stress-free airport navigation and discovery.

## Problem Statement
Airports can be overwhelming, especially for first-time travelers or international visitors. Passengers often struggle to find timely information about boarding gates, food courts, and duty-free shopping, leading to stress and delays. Existing airport apps are largely static and lack real-time, context-aware conversational assistance.

## Solution
A privacy-first, on-device AI assistant that helps travelers navigate and make informed decisions inside the airport. Operating entirely on a local LLM, it provides real-time guidance, navigation, and recommendations without relying on cloud APIs—perfect for environments with limited connectivity.

## Features
- **Conversational Chat Interface:** Ask natural language questions about airport facilities, food, and shopping.
- **Intelligent Navigation:** Get step-by-step directions and time-to-gate estimates.
- **RAG-based Recommendations:** Context-aware suggestions for food outlets, duty-free shopping, and exclusive offers.
- **Privacy-First & Offline Capable:** Runs purely on local inference, ensuring data privacy and offline reliability.

## System Architecture
The system replaces probabilistic components with deterministic, data-driven controls to ensure reliability:
1. **Frontend:** A modern, mobile-first React interface with a scrollable chat history and quick action pills.
2. **Orchestrator:** A robust Python backend that intercepts queries and determines the execution path (RAG vs. Navigation).
3. **Local Knowledge Base:** Vector storage containing structural airport POIs, retail SKUs, and facility details.
4. **Inference Engine:** A local LLM (Gemma) running via Ollama to process natural language and format responses.

## Tech Stack
- **Frontend:** React, Vite
- **Backend:** Python
- **AI/Inference:** Ollama, Gemma 2B
- **Data/RAG:** Local Knowledge Base / Vector Store

## How It Works
1. **User Input:** A passenger asks a question or requests directions via the chat interface.
2. **Intent Routing:** The backend orchestrator analyzes the input to determine if it is a routing request or a general inquiry.
3. **Context Retrieval:** For general inquiries, the RAG pipeline fetches relevant airport data (shops, food, facilities) from the local knowledge base.
4. **LLM Generation:** The local model synthesizes the retrieved data into a helpful, accurate response.
5. **Delivery:** The user receives a structured conversational answer or step-by-step navigation directions.

## API Endpoints

### `POST /api/chat`
Handles conversational queries and returns context-aware recommendations using RAG.
- **Input:** `{"message": "Where can I find electronics?"}`
- **Output:** JSON containing the LLM-generated response based on local airport data.

### `POST /api/navigate`
Returns step-by-step routing and time estimates between airport locations.
- **Input:** `{"destination": "Gate 12", "current_location": "Check-in A"}`
- **Output:** JSON containing step-by-step navigational nodes and estimated walking time.

## Project Structure
```text
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── orchestrator.py    # Request routing and pipeline control
│   │   │   └── llm_service.py     # Local LLM integration
│   │   └── config.py              # Application configuration
├── frontend/
│   ├── src/
│   │   └── App.jsx                # Main React chat interface
│   └── vite.config.js
└── README.md
```

## Example Queries
- *"Where is the nearest food court?"*
- *"How long does it take to walk from Check-in Counter A to Gate 12?"*
- *"Are there any duty-free shops selling electronics near Terminal 2?"*
- *"Navigate me to the nearest washroom."*

## Limitations
- **Hardware Dependent:** Response latency depends on the hardware running local inference.
- **Static Data:** Currently relies on static airport data; real-time flight updates require integration with live APIs.
- **Hallucinations:** While mitigated by deterministic routing and RAG, minor hallucinations may still occur.

## Future Improvements
- **Live Flight Integration:** Connect to live flight status and gate change APIs.
- **Multilingual Support:** Enable seamless interactions for international travelers.
- **Voice Interactions:** Add lightweight, on-device Speech-to-Text and Text-to-Speech capabilities.
- **Visual Mapping:** Implement turn-by-turn indoor map visualization in the UI.

## Author
Powermind Hackathon Team
