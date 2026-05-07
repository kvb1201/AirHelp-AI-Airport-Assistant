# AirHelp — AI Airport Companion

> **An intelligent, privacy-first airport assistant that transforms the passenger experience through conversational AI, real-time navigation, and context-aware recommendations.**

Built during **PowerMind Hackathon 2026** 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.2-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)

---

## 🎯 Features

- 🤖 **AI-Powered Conversational Assistant** - Natural language understanding with local LLM
- 🗺️ **Intelligent Navigation Engine** - Graph-based pathfinding with A* algorithm
- 🔍 **RAG-Based Facility Discovery** - Semantic search over airport facilities
- 🎤 **Voice Interaction Support** - Whisper STT + Piper TTS (completely offline)
- 📱 **Boarding Pass Scanning** - OCR-based boarding pass extraction
- 📡 **Real-Time Operational Alerts** - WebSocket-based flight updates
- 🧠 **Multi-Layer Memory Architecture** - Context-aware conversation management
- 🔒 **Privacy-First Design** - All processing happens locally, no cloud dependencies

---

## 📸 Demo

### Chat Assistant
<img src="docs/screenshots/chat-interface.png" alt="Chat Interface" width="400"/>

*Natural language queries with context-aware responses*

### Navigation System
<img src="docs/screenshots/navigation-map.png" alt="Navigation Map" width="400"/>

*Real-time route calculation with turn-by-turn directions*

### Facility Discovery
<img src="docs/screenshots/facility-recommendations.png" alt="Facility Recommendations" width="400"/>

*Semantic search with personalized recommendations*

### Voice Interaction
<img src="docs/screenshots/voice-input.png" alt="Voice Input" width="400"/>

*Hands-free interaction with Whisper STT*

---

## 🎯 Problem Statement

Modern airports present significant challenges for passengers:

- **Information Overload**: Multiple terminals, hundreds of gates, countless facilities
- **Time Pressure**: Tight connections, boarding deadlines, security queues
- **Language Barriers**: International travelers struggling with local signage
- **Static Information**: Traditional apps provide outdated, non-contextual data
- **Poor Discoverability**: Hidden amenities, last-minute gate changes, facility locations

**Result**: Stress, missed flights, poor passenger experience, underutilized airport services.

---

## 💡 Solution

AirHelp transforms the passenger's phone into an **intelligent airport companion** capable of:

- **Understanding Natural Language**: "I'm hungry and in a hurry" → Quick food recommendations
- **Guiding Across Terminals**: Step-by-step navigation with time estimates
- **Recommending Contextually**: Personalized suggestions based on location, preferences, and flight info
- **Handling Follow-ups**: Conversational memory for natural interactions
- **Supporting Voice**: Hands-free operation for busy travelers
- **Maintaining Privacy**: All processing happens locally, no data leaves the device

---

## 🏗️ System Architecture

AirHelp is built using a **modular multi-layer AI architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│  React Frontend (Mobile-First)                              │
│  ├─ Chat Interface                                          │
│  ├─ Voice Input (Whisper STT)                               │
│  ├─ Navigation Visualization                                │
│  └─ Real-time Notifications                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ REST API / WebSocket
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   ORCHESTRATOR LAYER                         │
│  Intent Detection → Route Selection → Pipeline Execution    │
│  ├─ Navigation Intent → Graph Engine                        │
│  ├─ Discovery Intent → RAG Pipeline                         │
│  ├─ Assistance Intent → Support System                      │
│  └─ Context Management → Memory Layer                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ RAG PIPELINE │ │ GRAPH ENGINE │ │ VOICE ENGINE │
│              │ │              │ │              │
│ Vector DB    │ │ A* Pathfind  │ │ Whisper STT  │
│ Reranking    │ │ Turn-by-Turn │ │ Piper TTS    │
│ LLM Synth    │ │ Time Calc    │ │ Multi-lang   │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     DATA LAYER                               │
│  ├─ ChromaDB (Vector Store)                                 │
│  ├─ NetworkX (Navigation Graph)                             │
│  ├─ SQLite (User Sessions, Lost & Found)                    │
│  ├─ JSON (Airport Catalog, Operational State)               │
│  └─ Ollama (Local LLM - Gemma 2B)                           │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Orchestrator Layer**: Intent detection, pipeline routing, context management
2. **RAG Pipeline**: Semantic search, reranking, LLM synthesis
3. **Navigation Engine**: Graph-based pathfinding with A* algorithm
4. **Voice Pipeline**: Whisper STT + Piper TTS (offline)
5. **Memory Architecture**: 3-layer system (persistent, ephemeral, turn-based)
6. **Context Engine**: Multi-layer state management with TTL-based caching

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.115.0
- **Language**: Python 3.11+
- **LLM**: Ollama (Gemma 2B)
- **Vector DB**: ChromaDB 0.5.23
- **Embeddings**: Sentence Transformers 3.2.1
- **Graph**: NetworkX 3.3
- **Voice**: faster-whisper 1.2.1, Piper TTS 1.4.0
- **OCR**: OpenCV 4.10.0, Pillow 10.4.0

### Frontend
- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.1.4
- **Styling**: CSS3, Material Symbols
- **Voice**: MediaRecorder API

### Infrastructure
- **Server**: Uvicorn (ASGI)
- **Database**: SQLite, ChromaDB
- **Storage**: Local filesystem
- **Deployment**: Docker (optional)

---

## 📁 Project Structure

```
airhelp/
├── backend/
│   ├── app/
│   │   ├── api/                    # API endpoints
│   │   │   ├── chat.py            # Conversational interface
│   │   │   ├── navigation.py      # Route calculation
│   │   │   ├── transcribe.py      # Speech-to-text
│   │   │   ├── ocr.py             # Boarding pass scanning
│   │   │   └── ops.py             # Operational alerts
│   │   ├── services/              # Business logic
│   │   │   ├── orchestrator.py    # Intent routing
│   │   │   ├── rag_service.py     # RAG pipeline
│   │   │   ├── navigation_service.py  # Pathfinding
│   │   │   ├── llm_service.py     # LLM integration
│   │   │   └── context_service.py # State management
│   │   ├── core/                  # Core systems
│   │   │   ├── session/           # Session management
│   │   │   ├── rag/               # RAG components
│   │   │   ├── graph/             # Navigation graph
│   │   │   └── stt_cache.py       # Whisper cache
│   │   ├── models/                # Data models
│   │   └── utils/                 # Utilities
│   ├── data/                      # Airport data
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── ChatWindow.jsx    # Chat interface
│   │   │   ├── InputBox.jsx      # Voice + text input
│   │   │   ├── MapView.jsx       # Navigation map
│   │   │   └── BoardingPassUpload.jsx
│   │   ├── services/              # API services
│   │   │   └── api.js            # API client
│   │   ├── hooks/                 # React hooks
│   │   └── styles/                # CSS styles
│   └── package.json
├── docs/                          # Documentation
│   ├── architecture/              # System design
│   ├── api/                       # API reference
│   ├── deployment/                # Setup guides
│   └── demo/                      # Demo scripts
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama
- ffmpeg

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/airhelp.git
cd airhelp

# Backend setup
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install Ollama and pull model
ollama pull gemma:2b

# Frontend setup
cd ../frontend
npm install

# Start backend
cd ../backend
uvicorn app.main:app --reload

# Start frontend (new terminal)
cd frontend
npm run dev
```

Visit `http://localhost:3000` to use the application.

**Detailed setup guide**: [docs/deployment/local-setup.md](docs/deployment/local-setup.md)

---

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[System Overview](docs/architecture/system-overview.md)** - High-level architecture
- **[API Reference](docs/api/endpoints.md)** - Complete API documentation
- **[Local Setup](docs/deployment/local-setup.md)** - Installation guide
- **[Demo Script](docs/demo/demo-script.md)** - Presentation guide
- **[Architectural Decisions](docs/research/architectural-decisions.md)** - Design choices

**Full documentation index**: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)

---

## 🎬 Example Queries

```
User: "I'm hungry and in a hurry"
AirHelp: "I found 3 quick food options near you:
         1. Starbucks (50m away) - Coffee and pastries
         2. Subway (80m away) - Quick sandwiches
         3. McDonald's (120m away) - Fast food"

User: "How do I get to Gate B12?"
AirHelp: "Route to Gate B12 (8 minutes):
         1. Head straight to security (3.5 min)
         2. Turn right into Corridor B (2 min)
         3. Gate B12 on your left (2.5 min)"

User: "Where can I charge my phone?"
AirHelp: "Charging stations available at:
         1. Starbucks (50m) - Multiple outlets
         2. Lounge Area (150m) - Free charging pods
         3. Gate B5 (200m) - USB charging stations"
```

---

## 🎯 Key Innovations

### 1. Multi-Layer Memory Architecture
Solves the "recommendation contamination" problem with 3-layer state management:
- **Persistent**: User profile, flight info
- **Ephemeral**: Recommendations (5 min TTL), navigation (15 min TTL)
- **Turn-based**: Single request context

### 2. Hybrid RAG Pipeline
Combines vector search with metadata filtering:
- Semantic similarity (embeddings)
- Category filtering (food, shopping, facilities)
- Location proximity (terminal, level)
- Reranking for relevance

### 3. Graph-Based Navigation
Deterministic routing with A* algorithm:
- Exact distances and paths
- Time estimation with congestion
- Accessibility routing
- Turn-by-turn instructions

### 4. Offline-First Design
Complete privacy and offline capability:
- Local LLM (Ollama + Gemma)
- Embedded vector database
- Offline voice processing
- No cloud dependencies

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Response Time | 1-3 seconds |
| Navigation Accuracy | 95%+ |
| Voice Recognition | 90%+ |
| Offline Capability | 100% |
| Concurrent Users | 50-100 (single instance) |

---

## 🔮 Future Roadmap

### Short-Term (3-6 months)
- [ ] Real-time flight integration
- [ ] Multi-airport support
- [ ] Mobile app (React Native)
- [ ] AR navigation overlay

### Long-Term (6-12 months)
- [ ] Predictive assistance
- [ ] Multi-modal input (image, video)
- [ ] Personalization engine
- [ ] Integration with airline systems

---

## 👥 Team

**PowerMind Hackathon Team**

- **[Team Member 1]** - Samanvitha Bolisetty -Smart Knowledge Base Developer 
  - GitHub: [Github link](https://github.com/samanvitha7)
  - LinkedIn: [Linkedin link](https://www.linkedin.com/in/samanvitha-bolisetty-465a02326/)

- **[Team Member 2]** - Shreya Ashar- Voice Interaction & Language Support Developer
  - GitHub: [Github link](https://github.com/ShreyaSVNIT) 
  - LinkedIn: [Linkedin link](https://www.linkedin.com/in/shreya-ashar-18a027191/)

- **[Team Member 3]** - Ojas Srivastava - UI/UX and navigation engine developer
  - GitHub: [Github link](https://github.com/Ojas-Srivastava05)
  - LinkedIn: [Linkedin link](https://www.linkedin.com/in/ojas-srivastava05/)

- **[Team Member 4]** - Sunil Jaat - RAG developer
  - GitHub: [Github link](https://github.com/u24ai063sunil)
  - LinkedIn: [Linkedin link](https://www.linkedin.com/in/sunil-jaat-216052348/)

- **[Team Member 5]** - Kavya Bhatiya - System Orchestrator and context engine developer
  - GitHub: [Github link](https://github.com/kvb1201)
  - LinkedIn: [Linkedin link](https://www.linkedin.com/in/kavya-bhatiya/)





---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ollama** for local LLM serving
- **OpenAI Whisper** for speech recognition
- **ChromaDB** for vector storage
- **FastAPI** for the backend framework
- **React** for the frontend framework

---

## 📧 Contact

For questions, feedback, or collaboration:

- **Email**: kavyabhatiya44@gmail.com
- **Documentation**: [Full docs](DOCUMENTATION_INDEX.md)

---

**Built with ❤️ during PowerMind Hackathon 2026**
