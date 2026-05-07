# System Overview

## Vision

AirHelp is an intelligent, conversational AI assistant designed to transform the airport experience by providing real-time, context-aware guidance for navigation, facility discovery, and passenger assistance.

## Problem Statement

Modern airports present significant challenges for passengers:

- **Information Overload**: Multiple terminals, hundreds of gates, countless facilities
- **Time Pressure**: Tight connections, boarding deadlines, security queues
- **Language Barriers**: International travelers struggling with local signage
- **Static Information**: Traditional apps provide outdated, non-contextual data
- **Poor Discoverability**: Hidden amenities, last-minute gate changes, facility locations

**Result**: Stress, missed flights, poor passenger experience, underutilized airport services.

## Solution Architecture

AirHelp combines multiple AI systems into a unified conversational platform:

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│                                                              │
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
│                                                              │
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
│                                                              │
│  ├─ ChromaDB (Vector Store)                                 │
│  ├─ NetworkX (Navigation Graph)                             │
│  ├─ SQLite (User Sessions, Lost & Found)                    │
│  ├─ JSON (Airport Catalog, Operational State)               │
│  └─ Ollama (Local LLM - Gemma 2B)                           │
└─────────────────────────────────────────────────────────────┘
```

## Core Principles

### 1. **Privacy-First**
- All processing happens locally
- No cloud dependencies for core functionality
- User data never leaves the device
- Offline-capable design

### 2. **Context-Aware**
- Multi-layer memory system
- Session persistence
- Location tracking
- Flight information integration

### 3. **Deterministic Control**
- Intent-based routing (not probabilistic)
- Structured data retrieval
- Validated responses
- Fallback mechanisms

### 4. **Production-Grade**
- Error handling at every layer
- Comprehensive logging
- Performance monitoring
- Graceful degradation

## System Components

### Frontend Layer
**Technology**: React 18, Vite  
**Responsibility**: User interaction, voice capture, visualization

**Key Features**:
- Mobile-first responsive design
- Real-time chat interface
- Voice input with MediaRecorder API
- Navigation map visualization
- Notification system

### Orchestrator Layer
**Technology**: Python, FastAPI  
**Responsibility**: Request routing, pipeline coordination, context management

**Key Features**:
- Intent detection and classification
- Pipeline selection (RAG vs Navigation vs Assistance)
- Context injection and state management
- Response formatting and validation

### RAG Pipeline
**Technology**: ChromaDB, Sentence Transformers, Ollama  
**Responsibility**: Information retrieval and response generation

**Key Features**:
- Semantic search over airport facilities
- Metadata filtering (category, location, price)
- Reranking for relevance
- LLM-based response synthesis
- Hallucination detection

### Navigation Engine
**Technology**: NetworkX, A* Algorithm  
**Responsibility**: Pathfinding and route generation

**Key Features**:
- Graph-based airport representation
- Shortest path calculation
- Time estimation (walking speed, congestion)
- Turn-by-turn instructions
- Accessibility routing

### Voice Pipeline
**Technology**: faster-whisper, Piper TTS  
**Responsibility**: Speech processing

**Key Features**:
- Real-time speech-to-text (Whisper)
- Multi-language support (English, Hindi, Hinglish)
- Text-to-speech synthesis (Piper)
- Audio format handling
- Latency optimization

### Memory System
**Technology**: Python dictionaries, SQLite, JSON  
**Responsibility**: State management

**Layers**:
- **User Profile**: Persistent preferences, flight info
- **Session State**: Current conversation, navigation state
- **Turn State**: Single query context
- **Cache Layer**: Recommendations, search results (TTL-based)

## Data Flow

### Typical Query Flow

```
1. User Input
   ↓
2. Frontend Capture (text or voice)
   ↓
3. API Request to Backend
   ↓
4. Orchestrator: Intent Detection
   ↓
5. Context Injection (user profile, session state)
   ↓
6. Pipeline Selection
   ├─ Navigation → Graph Engine → Route
   ├─ Discovery → RAG Pipeline → Recommendations
   └─ Assistance → Support System → Ticket
   ↓
7. Response Generation
   ↓
8. Context Update (memory layer)
   ↓
9. API Response to Frontend
   ↓
10. UI Rendering (chat, map, voice)
```

## Key Innovations

### 1. **Hybrid Retrieval**
Combines vector search with metadata filtering for precise results:
- Semantic similarity (embeddings)
- Category filtering (food, shopping, facilities)
- Location proximity (terminal, level)
- Price range filtering

### 2. **Contamination Prevention**
Addresses the "recommendation persistence" problem:
- Ephemeral session store with TTL
- Separate persistent vs transient state
- Automatic cache expiry
- Clean state transitions

### 3. **Guided Navigation**
Real-time navigation with relocalization:
- Checkpoint-based guidance
- Visual cue verification
- Automatic rerouting
- Congestion awareness

### 4. **Offline-First**
Designed to work without internet:
- Local LLM (Ollama + Gemma)
- Embedded vector database
- Cached airport data
- Offline voice processing

## Performance Characteristics

| Component | Latency | Throughput | Resource Usage |
|-----------|---------|------------|----------------|
| Intent Detection | <50ms | 1000 req/s | Low CPU |
| RAG Retrieval | 100-200ms | 100 req/s | Medium CPU, High Memory |
| LLM Generation | 1-3s | 10 req/s | High CPU/GPU |
| Navigation | <100ms | 500 req/s | Low CPU |
| Voice (STT) | 1-2s | 20 req/s | High CPU |
| Voice (TTS) | 500ms-1s | 50 req/s | Medium CPU |

## Scalability

### Current Capacity
- **Concurrent Users**: 50-100 (single instance)
- **Requests/Second**: 100-200
- **Database Size**: 10MB (airport data), 500MB (embeddings)
- **Memory Footprint**: 2-4GB (with LLM loaded)

### Scaling Strategy
- **Horizontal**: Multiple backend instances with load balancer
- **Vertical**: GPU acceleration for LLM and embeddings
- **Caching**: Redis for session state and frequent queries
- **CDN**: Static assets and airport maps

## Security & Privacy

### Data Protection
- No external API calls for core functionality
- User data stored locally (SQLite)
- Session tokens for authentication
- HTTPS for all communications

### Privacy Features
- No user tracking
- No analytics collection
- Ephemeral session data
- User-controlled data deletion

## Technology Stack

### Backend
- **Framework**: FastAPI 0.115.0
- **Language**: Python 3.11+
- **LLM**: Ollama (Gemma 2B)
- **Vector DB**: ChromaDB 0.5.23
- **Embeddings**: Sentence Transformers 3.2.1
- **Graph**: NetworkX 3.3
- **Voice**: faster-whisper 1.2.1, Piper TTS 1.4.0

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

## Deployment Architecture

### Development
```
Laptop/Desktop
├─ Backend (localhost:8000)
├─ Frontend (localhost:3000)
├─ Ollama (localhost:11434)
└─ Data (local files)
```

### Production
```
Server/Cloud
├─ Backend (Uvicorn + Gunicorn)
├─ Frontend (Nginx static)
├─ Ollama (GPU instance)
└─ Data (persistent volumes)
```

## Future Enhancements

### Short-Term (3-6 months)
- Real-time flight integration
- Multi-airport support
- Enhanced voice UI
- Mobile app (React Native)

### Long-Term (6-12 months)
- AR navigation overlay
- Predictive assistance
- Personalization engine
- Multi-modal interactions (image, video)

## Success Metrics

### User Experience
- Query response time < 3 seconds
- Navigation accuracy > 95%
- Voice recognition accuracy > 90%
- User satisfaction > 4.5/5

### System Performance
- API uptime > 99.9%
- Error rate < 0.1%
- Cache hit rate > 80%
- Memory usage < 4GB

## Conclusion

AirHelp represents a production-grade AI system that combines multiple cutting-edge technologies into a cohesive, user-friendly platform. By prioritizing privacy, performance, and user experience, it addresses real pain points in the airport navigation domain while maintaining the flexibility to scale and evolve.

---

**Next Steps**:
- [Orchestrator Architecture](orchestrator.md)
- [RAG Pipeline Details](rag-pipeline.md)
- [Navigation Engine](navigation-engine.md)
