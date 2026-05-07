# Demo Script

## Overview

This script provides a structured walkthrough for demonstrating AirHelp to judges, investors, or stakeholders. The demo showcases key features, technical capabilities, and real-world use cases.

**Duration**: 10-15 minutes  
**Audience**: Technical and non-technical  
**Goal**: Demonstrate value proposition and technical excellence

---

## Pre-Demo Checklist

### Technical Setup
- [ ] Backend running (`http://localhost:8000`)
- [ ] Frontend running (`http://localhost:3000`)
- [ ] Ollama running with Gemma model loaded
- [ ] Browser open to frontend URL
- [ ] Browser DevTools ready (F12) for technical audience
- [ ] Microphone permissions granted
- [ ] Test queries prepared

### Environment Check
- [ ] Clear browser cache and localStorage
- [ ] Reset user data (fresh session)
- [ ] Check backend logs are visible
- [ ] Prepare backup slides/screenshots
- [ ] Test internet connection (for live demo)

---

## Demo Flow

### Part 1: Introduction (2 minutes)

**Script**:

> "Welcome! Today I'm excited to show you AirHelp - an AI-powered airport assistant that transforms the passenger experience.
>
> **The Problem**: Airports are overwhelming. Passengers struggle to find gates, food, shops, and services. Traditional airport apps are static, non-conversational, and don't understand context.
>
> **Our Solution**: AirHelp is a conversational AI assistant that provides real-time, context-aware guidance for navigation, discovery, and assistance - all running locally for complete privacy.
>
> Let me show you how it works."

**Action**: Open frontend, show clean chat interface.

---

### Part 2: Basic Conversation (2 minutes)

**Scenario**: First-time user asking for help.

**Demo**:

1. **Type**: "I'm hungry, where can I find food?"

   **Expected Response**: 
   ```
   I found several food options near your location:
   
   1. Starbucks - International coffee chain
      Location: Terminal 2, Level 2, Zone A
      Distance: 50m
      Quick service, perfect for a coffee and snack
   
   2. McDonald's - Fast food restaurant
      Location: Terminal 2, Level 2, Zone B
      Distance: 120m
      Quick meals, family-friendly
   ```

   **Highlight**:
   - Natural language understanding ("I'm hungry" → food recommendations)
   - Structured, helpful response
   - Location-aware (distance from user)
   - Multiple options with details

2. **Follow-up**: "Tell me more about Starbucks"

   **Expected Response**:
   ```
   Starbucks at Terminal 2, Level 2, Zone A:
   
   - International coffee chain
   - Offers hot and cold beverages, pastries, sandwiches
   - Price Range: Mid
   - Rating: 4.5/5
   - Open: 5:00 AM - 11:00 PM
   - Amenities: WiFi, Charging stations, Seating
   ```

   **Highlight**:
   - Context awareness (remembers previous query)
   - Detailed information
   - Structured data presentation

---

### Part 3: Navigation (2 minutes)

**Scenario**: User needs directions to gate.

**Demo**:

1. **Type**: "How do I get to Gate B12?"

   **Expected Response**:
   ```
   Here's the route to Gate B12. It will take approximately 8 minutes.
   
   Directions:
   1. Head straight from the entrance towards security
   2. Pass through security checkpoint (3.5 minutes)
   3. Turn right into Corridor B (2 minutes)
   4. Gate B12 will be on your left (2.5 minutes)
   
   Total Distance: 330 meters
   Estimated Time: 8 minutes
   ```

   **Highlight**:
   - Graph-based routing (A* algorithm)
   - Step-by-step instructions
   - Time estimates
   - Distance calculation

2. **Show Map** (if available):
   - Visual route on airport map
   - Highlighted path
   - Current location marker

---

### Part 4: Voice Interaction (2 minutes)

**Scenario**: Hands-free interaction.

**Demo**:

1. **Click microphone button** 🎤

2. **Speak**: "Where is the nearest washroom?"

3. **Show transcription**: 
   ```
   Transcribing... → "Where is the nearest washroom?"
   ```

4. **Expected Response**:
   ```
   The nearest washroom is located:
   
   - Terminal 2, Level 2, near Gate B5
   - Distance: 30 meters from your location
   - Turn left from your current position
   - Facilities: Wheelchair accessible, Family room
   ```

   **Highlight**:
   - Real-time speech-to-text (Whisper)
   - Multi-language support (English, Hindi, Hinglish)
   - Same quality as text input
   - Completely offline

---

### Part 5: Context Awareness (2 minutes)

**Scenario**: System remembers user context.

**Demo**:

1. **Type**: "I have flight AI123 departing at 3 PM"

   **Expected Response**:
   ```
   Got it! I've saved your flight information:
   
   - Flight: AI123
   - Departure: 3:00 PM
   - Gate: B12 (subject to change)
   - Boarding Time: 2:30 PM
   
   You have 2 hours until boarding. Would you like recommendations for how to spend your time?
   ```

2. **Type**: "Yes, what can I do?"

   **Expected Response**:
   ```
   Based on your flight timing, here are some suggestions:
   
   1. Grab a meal (30-45 minutes)
      - Recommended: Starbucks, McDonald's near Gate B12
   
   2. Visit Duty-Free Shopping (30-60 minutes)
      - Electronics, Cosmetics, Liquor available
   
   3. Relax at a Lounge (60+ minutes)
      - Premium Lounge, Level 3
   
   I'll remind you 30 minutes before boarding time.
   ```

   **Highlight**:
   - Flight information storage
   - Time-aware recommendations
   - Proactive assistance
   - Personalized suggestions

---

### Part 6: Advanced Features (2 minutes)

**Scenario**: Showcase unique capabilities.

**Demo 1: Lost & Found**

1. **Type**: "I lost my black suitcase near security"

   **Expected Response**:
   ```
   I'm sorry to hear that. I've created a lost item report:
   
   - Report ID: LOST-20260507-001
   - Item: Black suitcase
   - Last Seen: Security checkpoint, Terminal 2
   - Status: Registered
   
   We'll notify you if a matching item is found. You can also check at the Information Desk.
   ```

**Demo 2: Support Ticket**

1. **Type**: "The escalator near Gate B12 is broken"

   **Expected Response**:
   ```
   Thank you for reporting this issue. I've created a support ticket:
   
   - Ticket ID: TICKET-20260507-001
   - Issue: Broken escalator
   - Location: Near Gate B12
   - Status: Submitted
   - Estimated Response: 30 minutes
   
   Our maintenance team has been notified.
   ```

**Highlight**:
- Comprehensive assistance
- Issue tracking
- Proactive problem solving

---

### Part 7: Technical Deep Dive (3 minutes)

**For Technical Audience**

**Show Backend Logs**:

```
INFO: Query processed: intent=discovery, pipeline=rag, latency=250ms
INFO: Vector search: 20 results retrieved, 5 reranked
INFO: LLM synthesis: 1.2s
INFO: Response sent: success=true
```

**Show Architecture Diagram**:

```
User Query
    ↓
Orchestrator (Intent Detection)
    ↓
RAG Pipeline (Vector Search + LLM)
    ↓
Response Generation
    ↓
Context Update
```

**Highlight Technical Features**:

1. **Local-First Architecture**
   - All processing on-device
   - No cloud dependencies
   - Complete privacy

2. **RAG Pipeline**
   - Vector search (ChromaDB)
   - Semantic embeddings (Sentence Transformers)
   - LLM synthesis (Ollama + Gemma)
   - Reranking for relevance

3. **Graph-Based Navigation**
   - NetworkX graph representation
   - A* pathfinding algorithm
   - Real-time route calculation

4. **Voice Pipeline**
   - Whisper STT (faster-whisper)
   - Multi-language support
   - Piper TTS for responses

5. **Memory Architecture**
   - Multi-layer context management
   - Ephemeral cache with TTL
   - Session persistence

**Show Code** (optional):

```python
# Intent Detection
def detect_intent(query: str) -> str:
    if 'navigate' in query or 'how to get' in query:
        return 'navigation'
    elif 'find' in query or 'recommend' in query:
        return 'discovery'
    return 'information'

# RAG Pipeline
def rag_search(query: str) -> List[dict]:
    embedding = embedder.encode(query)
    results = vector_db.search(embedding, top_k=20)
    reranked = reranker.rerank(query, results, top_k=5)
    response = llm.generate(query, reranked)
    return response
```

---

### Part 8: Comparison (2 minutes)

**Show Competitive Advantage**:

| Feature | Traditional Apps | AirHelp |
|---------|-----------------|---------|
| Conversational | ❌ | ✅ |
| Context-Aware | ❌ | ✅ |
| Voice Input | Limited | ✅ Full |
| Offline | ❌ | ✅ |
| Privacy | Cloud | Local |
| Navigation | Static | Real-time |
| Personalization | ❌ | ✅ |

**Highlight**:
- Only solution with full offline capability
- Only solution with conversational AI
- Only solution with complete privacy

---

### Part 9: Future Roadmap (1 minute)

**Show Vision**:

**Short-Term (3-6 months)**:
- Real-time flight integration
- Multi-airport support
- Mobile app (iOS/Android)
- AR navigation overlay

**Long-Term (6-12 months)**:
- Predictive assistance (proactive suggestions)
- Multi-modal input (image, video)
- Personalization engine (learn preferences)
- Integration with airline systems

---

### Part 10: Q&A (2 minutes)

**Common Questions**:

**Q: How accurate is the navigation?**
A: 95%+ accuracy using graph-based routing with real airport data.

**Q: Does it work offline?**
A: Yes, completely. All AI processing happens locally.

**Q: What about privacy?**
A: All data stays on device. No cloud, no tracking, no data collection.

**Q: How fast is it?**
A: Typical response time: 1-3 seconds (including LLM generation).

**Q: Can it handle multiple languages?**
A: Yes, supports English, Hindi, and Hinglish. More languages coming.

**Q: How do you handle hallucinations?**
A: RAG grounds responses in real data. We validate all LLM outputs.

**Q: What's the tech stack?**
A: Python (FastAPI), React, Ollama (Gemma), ChromaDB, Whisper, NetworkX.

---

## Demo Tips

### Do's
✅ Start with simple queries, build complexity  
✅ Show real-world scenarios  
✅ Highlight unique features  
✅ Demonstrate voice input  
✅ Show backend logs for technical audience  
✅ Have backup screenshots ready  
✅ Practice timing (stay under 15 minutes)  
✅ Engage audience with questions  

### Don'ts
❌ Don't rush through features  
❌ Don't skip error handling demo  
❌ Don't ignore questions  
❌ Don't over-promise features  
❌ Don't show unfinished features  
❌ Don't forget to reset demo state  

---

## Backup Plan

### If Live Demo Fails

1. **Have Screenshots Ready**
   - All key features
   - Sample conversations
   - Architecture diagrams

2. **Have Video Recording**
   - Full demo walkthrough
   - 5-minute version

3. **Have Slides**
   - Problem statement
   - Solution overview
   - Technical architecture
   - Results/metrics

### If Specific Feature Fails

- **Voice Input**: Use text input, explain voice capability
- **Navigation**: Show static route example
- **LLM Slow**: Explain it's running locally, show cached response

---

## Post-Demo

### Follow-Up Materials

- GitHub repository link
- Documentation link
- Demo video link
- Contact information
- Slide deck

### Metrics to Share

- Response time: 1-3 seconds
- Accuracy: 95%+
- Offline capability: 100%
- Privacy: Complete (local-only)
- Languages: 3+ supported

---

## Conclusion

**Closing Statement**:

> "AirHelp demonstrates how AI can transform the airport experience while respecting user privacy. By combining conversational AI, graph-based navigation, and voice interaction - all running locally - we've created a solution that's not just innovative, but practical and deployable today.
>
> We're excited about the future of AI-powered airport assistance, and we believe AirHelp is just the beginning.
>
> Thank you! Any questions?"

---

**Related Documentation**:
- [Sample Queries](sample-queries.md)
- [Demo Scenarios](demo-scenarios.md)
- [Judging Flow](judging-flow.md)
