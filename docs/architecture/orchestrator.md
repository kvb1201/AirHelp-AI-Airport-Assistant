# Orchestrator Architecture

## Purpose

The Orchestrator is the central intelligence layer that routes user queries to appropriate AI pipelines, manages context, and coordinates response generation. It acts as the "brain" of the system, making deterministic decisions about how to process each request.

## Responsibilities

1. **Intent Detection**: Classify user queries into actionable intents
2. **Pipeline Selection**: Route requests to RAG, Navigation, or Assistance systems
3. **Context Management**: Inject and update user/session state
4. **Response Coordination**: Aggregate results from multiple pipelines
5. **Error Handling**: Graceful degradation and fallback mechanisms
6. **State Persistence**: Save conversation history and user preferences

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR CORE                         │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              1. INTENT DETECTION                       │ │
│  │                                                        │ │
│  │  User Query → Keyword Matching → Intent Classification│ │
│  │                                                        │ │
│  │  Intents:                                             │ │
│  │  ├─ navigation (where, how to get, directions)       │ │
│  │  ├─ discovery (find, recommend, show me)             │ │
│  │  ├─ information (what, when, tell me about)          │ │
│  │  ├─ assistance (help, issue, problem)                │ │
│  │  └─ follow_up (context-dependent)                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              2. CONTEXT INJECTION                      │ │
│  │                                                        │ │
│  │  Load User Context:                                   │ │
│  │  ├─ User Profile (flight info, preferences)          │ │
│  │  ├─ Session State (conversation history)             │ │
│  │  ├─ Location State (current position)                │ │
│  │  └─ Cached Results (previous recommendations)        │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              3. PIPELINE ROUTING                       │ │
│  │                                                        │ │
│  │  Intent → Pipeline Mapping:                           │ │
│  │  ├─ navigation → Navigation Engine                    │ │
│  │  ├─ discovery → RAG Pipeline                          │ │
│  │  ├─ information → RAG Pipeline                        │ │
│  │  ├─ assistance → Support System                       │ │
│  │  └─ follow_up → Context-based routing                │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              4. RESPONSE GENERATION                    │ │
│  │                                                        │ │
│  │  Pipeline Results → LLM Synthesis → Formatted Response│ │
│  │                                                        │ │
│  │  Response Types:                                      │ │
│  │  ├─ navigation (route, steps, time)                  │ │
│  │  ├─ recommendations (list, details, options)         │ │
│  │  ├─ information (answer, explanation)                │ │
│  │  └─ error (fallback, clarification)                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              5. STATE UPDATE                           │ │
│  │                                                        │ │
│  │  Update Context:                                      │ │
│  │  ├─ Save conversation turn                            │ │
│  │  ├─ Update session state                              │ │
│  │  ├─ Cache recommendations (with TTL)                  │ │
│  │  └─ Persist user preferences                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Intent Detection Algorithm

### Keyword-Based Classification

```python
def detect_intent(query: str, context: dict) -> str:
    """
    Deterministic intent detection using keyword matching.
    
    Priority Order:
    1. Navigation keywords (highest priority)
    2. Discovery keywords
    3. Information keywords
    4. Assistance keywords
    5. Follow-up (context-dependent)
    """
    
    query_lower = query.lower()
    
    # Navigation Intent
    navigation_keywords = [
        'navigate', 'direction', 'how to get', 'where is',
        'take me to', 'route', 'path', 'way to'
    ]
    if any(kw in query_lower for kw in navigation_keywords):
        return 'navigation'
    
    # Discovery Intent
    discovery_keywords = [
        'find', 'recommend', 'suggest', 'show me',
        'looking for', 'want', 'need', 'search'
    ]
    if any(kw in query_lower for kw in discovery_keywords):
        return 'discovery'
    
    # Assistance Intent
    assistance_keywords = [
        'help', 'issue', 'problem', 'complaint',
        'lost', 'found', 'report'
    ]
    if any(kw in query_lower for kw in assistance_keywords):
        return 'assistance'
    
    # Follow-up Intent (context-dependent)
    if context.get('last_intent') and is_follow_up(query):
        return 'follow_up'
    
    # Default: Information Intent
    return 'information'
```

### Context-Aware Refinement

```python
def refine_intent(intent: str, query: str, context: dict) -> str:
    """
    Refine intent based on conversation context.
    """
    
    # If user has active navigation, prioritize navigation updates
    if context.get('active_navigation'):
        if 'stop' in query or 'cancel' in query:
            return 'cancel_navigation'
        if 'where am i' in query or 'lost' in query:
            return 'relocalize'
    
    # If user has cached recommendations, handle follow-ups
    if context.get('last_recommendations'):
        if 'more' in query or 'other' in query:
            return 'more_recommendations'
        if 'details' in query or 'tell me about' in query:
            return 'recommendation_details'
    
    return intent
```

## Pipeline Routing

### Navigation Pipeline

**Trigger**: `navigation`, `relocalize`, `cancel_navigation`

**Flow**:
```
1. Extract location entities (start, destination)
2. Validate locations against graph nodes
3. Call Navigation Engine (A* pathfinding)
4. Generate turn-by-turn instructions
5. Calculate time estimates
6. Format response with route visualization
```

**Example**:
```python
if intent == 'navigation':
    start = extract_location(query, context.get('current_location'))
    destination = extract_location(query)
    
    route = navigation_engine.find_route(start, destination)
    instructions = generate_turn_by_turn(route)
    time_estimate = calculate_walking_time(route)
    
    response = {
        'type': 'navigation',
        'route': route,
        'instructions': instructions,
        'time': time_estimate
    }
```

### RAG Pipeline

**Trigger**: `discovery`, `information`, `recommendation_details`

**Flow**:
```
1. Extract query intent and entities
2. Perform vector search in ChromaDB
3. Apply metadata filters (category, location)
4. Rerank results by relevance
5. Synthesize response with LLM
6. Cache results with TTL
```

**Example**:
```python
if intent == 'discovery':
    category = extract_category(query)  # food, shopping, facilities
    location = context.get('current_location')
    
    # Vector search
    results = vector_db.search(
        query=query,
        filters={'category': category, 'location': location},
        top_k=10
    )
    
    # Rerank
    reranked = reranker.rerank(query, results, top_k=5)
    
    # LLM synthesis
    response = llm.generate_response(query, reranked, context)
    
    # Cache
    cache.set(f"recommendations:{user_id}", reranked, ttl=300)
```

### Assistance Pipeline

**Trigger**: `assistance`, `lost`, `found`, `report`

**Flow**:
```
1. Classify assistance type (lost & found, complaint, help)
2. Create support ticket
3. Provide immediate guidance
4. Notify staff (if applicable)
```

## Context Management

### Context Structure

```python
class UserContext:
    # Persistent (stored in database)
    user_id: str
    flight_number: Optional[str]
    boarding_time: Optional[datetime]
    departure_time: Optional[datetime]
    gate: Optional[str]
    preferences: dict  # language, accessibility, dietary
    
    # Session (stored in memory/cache)
    session_id: str
    current_location: Optional[str]
    conversation_history: List[dict]
    last_intent: Optional[str]
    last_query: Optional[str]
    
    # Ephemeral (TTL-based cache)
    last_recommendations: Optional[List[dict]]  # TTL: 5 min
    active_navigation: Optional[dict]  # TTL: 15 min
    cached_results: dict  # TTL: varies
```

### Context Injection

```python
def inject_context(query: str, user_id: str) -> dict:
    """
    Load and inject relevant context for query processing.
    """
    
    # Load persistent context
    user_profile = db.get_user_profile(user_id)
    
    # Load session context
    session = session_store.get(user_id)
    
    # Load ephemeral context
    recommendations = cache.get(f"recommendations:{user_id}")
    navigation = cache.get(f"navigation:{user_id}")
    
    return {
        'user_id': user_id,
        'flight_info': user_profile.get('flight_info'),
        'preferences': user_profile.get('preferences'),
        'current_location': session.get('current_location'),
        'conversation_history': session.get('history', [])[-5:],  # Last 5 turns
        'last_intent': session.get('last_intent'),
        'last_recommendations': recommendations,
        'active_navigation': navigation
    }
```

### Context Update

```python
def update_context(user_id: str, intent: str, query: str, response: dict):
    """
    Update context after processing query.
    """
    
    # Update session state
    session_store.update(user_id, {
        'last_intent': intent,
        'last_query': query,
        'last_response': response,
        'timestamp': datetime.now()
    })
    
    # Update ephemeral cache
    if intent == 'discovery':
        cache.set(
            f"recommendations:{user_id}",
            response.get('data', {}).get('recommendations'),
            ttl=300  # 5 minutes
        )
    
    if intent == 'navigation':
        cache.set(
            f"navigation:{user_id}",
            response.get('data', {}).get('route'),
            ttl=900  # 15 minutes
        )
    
    # Update conversation history
    session_store.append_history(user_id, {
        'query': query,
        'intent': intent,
        'response': response,
        'timestamp': datetime.now()
    })
```

## Response Formatting

### Response Schema

```python
class OrchestratorResponse:
    type: str  # navigation, recommendations, information, error
    intent: str  # detected intent
    message: str  # user-facing message
    data: dict  # structured data (route, recommendations, etc.)
    context: dict  # updated context for frontend
    metadata: dict  # processing info (latency, confidence, etc.)
```

### Response Examples

**Navigation Response**:
```json
{
  "type": "navigation",
  "intent": "navigation",
  "message": "Here's the route to Gate B12. It will take approximately 8 minutes.",
  "data": {
    "route": {
      "start": "entrance_t2",
      "end": "gate_b12",
      "path": ["entrance_t2", "security_t2", "corridor_b", "gate_b12"],
      "distance": 450,
      "time": 8
    },
    "instructions": [
      "Head straight from the entrance",
      "Pass through security checkpoint",
      "Turn right into Corridor B",
      "Gate B12 will be on your left"
    ]
  },
  "context": {
    "active_navigation": true,
    "destination": "gate_b12"
  }
}
```

**Discovery Response**:
```json
{
  "type": "recommendations",
  "intent": "discovery",
  "message": "I found 5 food options near your location.",
  "data": {
    "recommendations": [
      {
        "name": "Starbucks",
        "category": "cafe",
        "location": "Terminal 2, Level 2",
        "distance": 50,
        "rating": 4.5
      }
    ]
  },
  "context": {
    "last_recommendations": true,
    "category": "food"
  }
}
```

## Error Handling

### Failure Scenarios

1. **Intent Detection Failure**
   - Fallback: Default to `information` intent
   - Response: Ask for clarification

2. **Pipeline Execution Failure**
   - Fallback: Return cached results or generic response
   - Log error for debugging

3. **Context Load Failure**
   - Fallback: Use minimal context (user_id only)
   - Continue processing

4. **LLM Generation Failure**
   - Fallback: Return structured data without synthesis
   - Use template-based response

### Error Response

```python
def handle_error(error: Exception, query: str, context: dict) -> dict:
    """
    Generate graceful error response.
    """
    
    logger.error(f"Orchestrator error: {error}", exc_info=True)
    
    return {
        'type': 'error',
        'intent': 'error',
        'message': 'I encountered an issue processing your request. Please try again.',
        'data': {},
        'context': context,
        'metadata': {
            'error': str(error),
            'query': query
        }
    }
```

## Performance Optimization

### Caching Strategy

- **Intent Detection**: Cache common query patterns
- **Context Loading**: Cache user profiles (5 min TTL)
- **Pipeline Results**: Cache recommendations (5 min TTL)
- **LLM Responses**: Cache for identical queries (1 hour TTL)

### Async Processing

```python
async def process_query(query: str, user_id: str) -> dict:
    """
    Async query processing for better performance.
    """
    
    # Parallel context loading
    context, user_profile = await asyncio.gather(
        load_session_context(user_id),
        load_user_profile(user_id)
    )
    
    # Intent detection (fast, synchronous)
    intent = detect_intent(query, context)
    
    # Pipeline execution (async)
    response = await execute_pipeline(intent, query, context)
    
    # Context update (async, non-blocking)
    asyncio.create_task(update_context(user_id, intent, query, response))
    
    return response
```

## Monitoring & Logging

### Metrics

- Intent detection accuracy
- Pipeline selection accuracy
- Response latency (p50, p95, p99)
- Error rate by intent type
- Cache hit rate

### Logging

```python
logger.info(f"Query processed", extra={
    'user_id': user_id,
    'intent': intent,
    'pipeline': pipeline,
    'latency_ms': latency,
    'cache_hit': cache_hit
})
```

## Future Improvements

1. **ML-Based Intent Detection**: Replace keyword matching with trained classifier
2. **Multi-Intent Handling**: Process queries with multiple intents
3. **Confidence Scoring**: Add confidence scores to intent detection
4. **A/B Testing**: Test different routing strategies
5. **Personalization**: Learn user preferences over time

---

**Related Documentation**:
- [RAG Pipeline](rag-pipeline.md)
- [Navigation Engine](navigation-engine.md)
- [Context Engine](context-engine.md)
