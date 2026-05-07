# Architectural Decisions

## Overview

This document explains the key architectural decisions made during the design and implementation of AirHelp, including the rationale, alternatives considered, and trade-offs.

---

## Decision 1: Local-First Architecture

### Decision
Run all AI processing locally using Ollama + Gemma instead of cloud APIs (OpenAI, Anthropic, etc.).

### Rationale

**Advantages**:
- **Privacy**: User data never leaves the device
- **Offline Capability**: Works without internet connection
- **Cost**: No API costs, unlimited usage
- **Latency**: No network round-trip for LLM calls
- **Control**: Full control over model behavior

**Disadvantages**:
- **Hardware Requirements**: Needs capable CPU/GPU
- **Model Quality**: Smaller models (2B params) vs cloud (175B+ params)
- **Maintenance**: Need to manage model updates locally

### Alternatives Considered

1. **Cloud APIs (OpenAI GPT-4)**
   - Rejected: Privacy concerns, cost, internet dependency
   
2. **Hybrid Approach** (local for simple, cloud for complex)
   - Rejected: Complexity, inconsistent experience

3. **Edge Deployment** (model on airport servers)
   - Future consideration: Scalability benefits

### Trade-offs

- **Quality vs Privacy**: Accepted slightly lower quality for complete privacy
- **Speed vs Accuracy**: Optimized for speed with smaller model
- **Flexibility vs Simplicity**: Chose simplicity with single local model

---

## Decision 2: RAG Over Fine-Tuning

### Decision
Use Retrieval-Augmented Generation (RAG) instead of fine-tuning the LLM on airport data.

### Rationale

**Advantages**:
- **Dynamic Updates**: Airport data changes frequently (shops, gates, hours)
- **Transparency**: Can inspect retrieved documents
- **Accuracy**: Grounded in actual data, reduces hallucinations
- **Cost**: No expensive fine-tuning process
- **Flexibility**: Easy to add new airports

**Disadvantages**:
- **Latency**: Additional retrieval step (~100-200ms)
- **Complexity**: More components (vector DB, embeddings)
- **Context Limits**: Limited by LLM context window

### Alternatives Considered

1. **Fine-Tuning Gemma**
   - Rejected: Expensive, inflexible, hard to update
   
2. **Prompt Engineering Only**
   - Rejected: Can't fit all airport data in prompt
   
3. **Knowledge Graphs Only**
   - Rejected: Poor semantic understanding

### Trade-offs

- **Latency vs Accuracy**: Accepted 100-200ms latency for better accuracy
- **Complexity vs Flexibility**: Accepted complexity for easy updates
- **Storage vs Speed**: Stored embeddings (500MB) for fast retrieval

---

## Decision 3: Graph-Based Navigation

### Decision
Use NetworkX graph with A* algorithm for navigation instead of vector-based or rule-based routing.

### Rationale

**Advantages**:
- **Accuracy**: Exact distances and paths
- **Flexibility**: Easy to add nodes, edges, weights
- **Performance**: A* is fast and optimal
- **Extensibility**: Can add accessibility, congestion, etc.
- **Deterministic**: Same input always gives same output

**Disadvantages**:
- **Manual Setup**: Need to manually create graph
- **Maintenance**: Updates require graph modifications
- **Scalability**: Large airports need large graphs

### Alternatives Considered

1. **Vector-Based Routing** (embeddings + similarity)
   - Rejected: Inaccurate, no exact distances
   
2. **Rule-Based Routing** (if-then rules)
   - Rejected: Inflexible, hard to maintain
   
3. **ML-Based Routing** (learned from data)
   - Future consideration: Could learn optimal routes

### Trade-offs

- **Setup Time vs Accuracy**: Accepted manual setup for exact routing
- **Flexibility vs Performance**: Graph structure allows both
- **Simplicity vs Features**: Chose feature-rich graph approach

---

## Decision 4: Ephemeral Session Management

### Decision
Implement TTL-based ephemeral cache for recommendations and navigation state, separate from persistent user profile.

### Rationale

**Problem**: Recommendations from previous queries contaminated subsequent queries.

**Example**:
```
User: "I want food"
System: [Caches food recommendations]

User: "Show me shops"
System: [Still shows food due to cache]  ❌
```

**Solution**: Separate persistent and ephemeral state with TTL expiry.

**Advantages**:
- **Clean State**: Recommendations expire automatically
- **Context Preservation**: User profile persists
- **Performance**: Cached results for quick follow-ups
- **Flexibility**: Different TTLs for different data types

**Disadvantages**:
- **Complexity**: Two-layer memory system
- **Tuning**: Need to tune TTL values
- **Edge Cases**: Expiry during conversation

### Alternatives Considered

1. **No Caching**
   - Rejected: Poor performance, no follow-up support
   
2. **Manual Cache Invalidation**
   - Rejected: Complex logic, error-prone
   
3. **Session-Based Only** (clear on new session)
   - Rejected: Doesn't handle intent changes within session

### Trade-offs

- **Complexity vs Correctness**: Accepted complexity for correct behavior
- **Memory vs Performance**: Used memory for better UX
- **Automatic vs Manual**: Chose automatic TTL over manual invalidation

---

## Decision 5: Keyword-Based Intent Detection

### Decision
Use deterministic keyword matching for intent detection instead of ML-based classification.

### Rationale

**Advantages**:
- **Deterministic**: Same query always gives same intent
- **Fast**: <1ms latency
- **Transparent**: Easy to debug and understand
- **No Training**: No need for labeled data
- **Reliable**: No model drift or failures

**Disadvantages**:
- **Limited**: Can't handle complex or ambiguous queries
- **Maintenance**: Need to update keyword lists
- **Accuracy**: May misclassify edge cases

### Alternatives Considered

1. **ML-Based Classification** (BERT, etc.)
   - Future consideration: Better accuracy for complex queries
   
2. **LLM-Based Classification** (ask LLM for intent)
   - Rejected: Too slow (~1-2s), unreliable
   
3. **Hybrid Approach** (keywords + ML fallback)
   - Future consideration: Best of both worlds

### Trade-offs

- **Accuracy vs Speed**: Chose speed for better UX
- **Flexibility vs Reliability**: Chose reliability for production
- **Simplicity vs Power**: Chose simplicity for maintainability

---

## Decision 6: Whisper for Speech-to-Text

### Decision
Use faster-whisper (local) instead of cloud STT APIs (Google, Azure, etc.).

### Rationale

**Advantages**:
- **Privacy**: Audio never leaves device
- **Offline**: Works without internet
- **Cost**: No API costs
- **Quality**: Whisper is state-of-the-art
- **Multi-Language**: Supports 99 languages

**Disadvantages**:
- **Latency**: 1-2s processing time
- **Hardware**: Requires CPU/GPU resources
- **Model Size**: 74MB (base model)

### Alternatives Considered

1. **Cloud STT APIs**
   - Rejected: Privacy, cost, internet dependency
   
2. **Browser Web Speech API**
   - Rejected: Limited language support, quality varies
   
3. **Vosk (lightweight STT)**
   - Rejected: Lower quality than Whisper

### Trade-offs

- **Latency vs Privacy**: Accepted 1-2s latency for privacy
- **Quality vs Size**: Chose base model (74MB) for balance
- **Flexibility vs Simplicity**: Whisper supports many languages

---

## Decision 7: React + Vite for Frontend

### Decision
Use React 18 with Vite instead of Next.js, Vue, or other frameworks.

### Rationale

**Advantages**:
- **Performance**: Vite is extremely fast
- **Simplicity**: No server-side rendering complexity
- **Ecosystem**: Large React ecosystem
- **Developer Experience**: Hot reload, fast builds
- **Flexibility**: Easy to customize

**Disadvantages**:
- **SEO**: No SSR (not needed for airport app)
- **Bundle Size**: React is larger than alternatives

### Alternatives Considered

1. **Next.js**
   - Rejected: Overkill for SPA, SSR not needed
   
2. **Vue.js**
   - Rejected: Team familiarity with React
   
3. **Svelte**
   - Rejected: Smaller ecosystem, less mature

### Trade-offs

- **Bundle Size vs Ecosystem**: Accepted larger bundle for ecosystem
- **Complexity vs Features**: Chose simplicity (SPA) over SSR
- **Performance vs DX**: Vite provides both

---

## Decision 8: FastAPI for Backend

### Decision
Use FastAPI instead of Flask, Django, or Node.js.

### Rationale

**Advantages**:
- **Performance**: Async support, fast
- **Type Safety**: Pydantic models, automatic validation
- **Documentation**: Auto-generated OpenAPI docs
- **Modern**: Built for async Python
- **Developer Experience**: Great error messages

**Disadvantages**:
- **Maturity**: Newer than Flask/Django
- **Ecosystem**: Smaller than Flask

### Alternatives Considered

1. **Flask**
   - Rejected: No async support, less type safety
   
2. **Django**
   - Rejected: Too heavy, ORM not needed
   
3. **Node.js (Express)**
   - Rejected: Python ecosystem better for AI/ML

### Trade-offs

- **Maturity vs Features**: Chose modern features over maturity
- **Simplicity vs Power**: FastAPI provides both
- **Ecosystem vs Performance**: Accepted smaller ecosystem for performance

---

## Decision 9: ChromaDB for Vector Storage

### Decision
Use ChromaDB instead of Pinecone, Weaviate, or FAISS.

### Rationale

**Advantages**:
- **Local**: No cloud dependency
- **Simple**: Easy to set up and use
- **Persistent**: Data stored on disk
- **Metadata Filtering**: Built-in support
- **Python-Native**: Great Python integration

**Disadvantages**:
- **Scalability**: Not designed for massive scale
- **Features**: Fewer features than enterprise solutions

### Alternatives Considered

1. **Pinecone**
   - Rejected: Cloud-only, cost
   
2. **Weaviate**
   - Rejected: More complex setup
   
3. **FAISS**
   - Considered: Used as secondary index for performance

### Trade-offs

- **Scalability vs Simplicity**: Chose simplicity for hackathon
- **Features vs Setup**: Chose easy setup over advanced features
- **Cloud vs Local**: Chose local for privacy

---

## Decision 10: Ollama for LLM Serving

### Decision
Use Ollama instead of llama.cpp, vLLM, or custom serving.

### Rationale

**Advantages**:
- **Simple**: One-command setup
- **Cross-Platform**: Works on macOS, Linux, Windows
- **Model Management**: Easy model downloads
- **API**: REST API compatible with OpenAI
- **Performance**: Optimized inference

**Disadvantages**:
- **Flexibility**: Less control than custom serving
- **Features**: Fewer features than vLLM

### Alternatives Considered

1. **llama.cpp**
   - Rejected: More complex to use
   
2. **vLLM**
   - Rejected: Overkill for single-user app
   
3. **Custom Serving**
   - Rejected: Too much work

### Trade-offs

- **Control vs Simplicity**: Chose simplicity for faster development
- **Performance vs Ease**: Ollama provides both
- **Features vs Setup**: Chose easy setup

---

## Future Architectural Decisions

### Under Consideration

1. **Multi-Airport Support**
   - Challenge: Scaling graph and vector DB
   - Solution: Separate databases per airport
   
2. **Real-Time Flight Integration**
   - Challenge: API reliability and cost
   - Solution: Hybrid (cached + live updates)
   
3. **Mobile App**
   - Challenge: React Native vs Flutter
   - Leaning: React Native (code reuse)
   
4. **GPU Acceleration**
   - Challenge: Hardware availability
   - Solution: Optional GPU support, CPU fallback
   
5. **Multi-Modal Input**
   - Challenge: Image processing complexity
   - Solution: OCR for boarding passes (implemented)

---

## Lessons Learned

### What Worked Well

1. **Local-First**: Privacy and offline capability were huge wins
2. **RAG**: Flexible and accurate, easy to update data
3. **Graph Navigation**: Exact routing, no approximations
4. **Ephemeral Sessions**: Solved contamination problem elegantly
5. **FastAPI**: Great developer experience, fast development

### What We'd Do Differently

1. **Intent Detection**: Would use ML-based classification for better accuracy
2. **Testing**: Would add more automated tests earlier
3. **Documentation**: Would document as we build, not after
4. **Performance**: Would profile earlier to identify bottlenecks
5. **Error Handling**: Would implement comprehensive error handling from start

### Key Takeaways

1. **Simplicity Wins**: Simple solutions are easier to debug and maintain
2. **Privacy Matters**: Users care about data privacy
3. **Performance is UX**: Fast responses are critical for good UX
4. **Determinism is Valuable**: Predictable behavior builds trust
5. **Iterate Quickly**: Build, test, learn, repeat

---

## Conclusion

These architectural decisions reflect a balance between:
- **Privacy and Performance**
- **Simplicity and Features**
- **Speed and Accuracy**
- **Flexibility and Reliability**

The result is a production-grade system that prioritizes user experience, privacy, and maintainability while delivering powerful AI capabilities.

---

**Related Documentation**:
- [System Overview](../architecture/system-overview.md)
- [Problem Statement](problem-statement.md)
- [Future Scope](future-scope.md)
