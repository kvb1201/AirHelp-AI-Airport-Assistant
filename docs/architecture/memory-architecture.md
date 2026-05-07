# Memory Architecture

## Overview

AirHelp implements a sophisticated **3-layer memory architecture** that separates persistent user data from ephemeral session state, solving critical state management challenges in conversational AI systems.

## The Problem: State Contamination

### Before: Single-Layer Storage

Traditional approaches store all state in one place, causing contamination:

```
User: "I want food"
System: [Returns food recommendations]
        [Saves to user profile - FOREVER]

User: "Show me shops"  
System: [Still shows food because it's in profile]
        ❌ CONTAMINATION!
```

**Root Cause**: Mixing persistent and transient state in the same storage layer.

### After: Multi-Layer Architecture

Our solution separates state by lifetime and purpose:

```
User: "I want food"
System: [Returns food recommendations]
        [Saves in ephemeral cache with 5-min TTL]

User: "Show me shops"
System: [Food cache expired or intent changed]
        [Returns shop recommendations]
        ✅ CLEAN STATE!
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY ARCHITECTURE                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         LAYER 1: PERSISTENT USER PROFILE               │ │
│  │                                                        │ │
│  │  Storage: users.json (SQLite in production)           │ │
│  │  Lifetime: Permanent (until user deletes)             │ │
│  │                                                        │ │
│  │  Contains:                                             │ │
│  │  ├─ user_id                                            │ │
│  │  ├─ flight_number                                      │ │
│  │  ├─ boarding_time                                      │ │
│  │  ├─ departure_time                                     │ │
│  │  ├─ gate                                               │ │
│  │  ├─ preferences (language, accessibility, dietary)    │ │
│  │  └─ created_at, updated_at                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         LAYER 2: EPHEMERAL SESSION STATE               │ │
│  │                                                        │ │
│  │  Storage: In-memory cache (Redis in production)       │ │
│  │  Lifetime: TTL-based (5-15 minutes)                   │ │
│  │                                                        │ │
│  │  Contains:                                             │ │
│  │  ├─ last_recommendations (TTL: 5 min)                 │ │
│  │  ├─ active_navigation (TTL: 15 min)                   │ │
│  │  ├─ last_intent                                        │ │
│  │  ├─ last_query                                         │ │
│  │  └─ cached_results (TTL: varies)                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         LAYER 3: TURN STATE (REQUEST CONTEXT)          │ │
│  │                                                        │ │
│  │  Storage: Request object (not persisted)              │ │
│  │  Lifetime: Single request/response cycle              │ │
│  │                                                        │ │
│  │  Contains:                                             │ │
│  │  ├─ current_query                                      │ │
│  │  ├─ current_location                                   │ │
│  │  ├─ input_mode (text/voice)                            │ │
│  │  ├─ detected_intent                                    │ │
│  │  └─ pipeline_results                                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Persistent User Profile

### Purpose
Store long-term user information that should persist across sessions and app restarts.

### Storage
- **Development**: `backend/app/data/users.json`
- **Production**: SQLite or PostgreSQL database

### Data Structure

```python
class UserProfile:
    user_id: str
    flight_number: Optional[str]
    boarding_time: Optional[datetime]
    departure_time: Optional[datetime]
    gate: Optional[str]
    preferences: dict  # language, accessibility, dietary
    created_at: datetime
    updated_at: datetime
```

### Example

```json
{
  "user_123": {
    "user_id": "user_123",
    "flight_number": "AI123",
    "boarding_time": "2026-05-07T14:30:00",
    "departure_time": "2026-05-07T15:00:00",
    "gate": "B12",
    "preferences": {
      "language": "en",
      "accessibility": ["wheelchair"],
      "dietary": ["vegetarian"]
    },
    "created_at": "2026-05-07T10:00:00",
    "updated_at": "2026-05-07T12:00:00"
  }
}
```

### What Belongs Here

✅ **Include**:
- Flight information (changes rarely)
- User preferences (language, accessibility)
- Profile data (name, contact)
- Long-term settings

❌ **Exclude**:
- Recommendations (expire quickly)
- Navigation state (temporary)
- Search results (transient)
- Conversation history (session-based)

### Lifetime
- **Permanent** until user explicitly deletes
- Survives app restarts and browser refreshes
- Updated only when user provides new information

### Implementation

```python
# backend/app/services/context_persistence.py

def save_user_profile(user_id: str, data: dict):
    """Save persistent user profile."""
    users = load_users_json()
    
    if user_id not in users:
        users[user_id] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
    
    # Update only persistent fields
    if 'flight_number' in data:
        users[user_id]['flight_number'] = data['flight_number']
    if 'boarding_time' in data:
        users[user_id]['boarding_time'] = data['boarding_time']
    if 'preferences' in data:
        users[user_id]['preferences'] = data['preferences']
    
    users[user_id]['updated_at'] = datetime.now().isoformat()
    
    save_users_json(users)

def load_user_profile(user_id: str) -> dict:
    """Load persistent user profile."""
    users = load_users_json()
    return users.get(user_id, {})
```

---

## Layer 2: Ephemeral Session State

### Purpose
Store temporary state that should expire automatically to prevent contamination.

### Storage
- **Development**: In-memory Python dictionary
- **Production**: Redis with TTL support

### Data Structure

```python
class SessionState:
    user_id: str
    last_recommendations: Optional[List[dict]]  # TTL: 5 min
    active_navigation: Optional[dict]  # TTL: 15 min
    last_intent: Optional[str]  # TTL: 5 min
    last_query: Optional[str]  # TTL: 5 min
    cached_results: dict  # TTL: varies
    expires_at: datetime
```

### TTL Strategy

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Recommendations | 5 min | User likely to follow up quickly |
| Navigation | 15 min | Walking takes time |
| Search Results | 5 min | Context changes quickly |
| Last Intent | 5 min | Conversation flow |
| Cached Queries | 60 min | Performance optimization |

### Implementation

```python
# backend/app/core/session/session_store.py

import time
from typing import Optional, Dict, Any

class EphemeralSessionStore:
    """TTL-based session storage."""
    
    def __init__(self):
        self.store: Dict[str, Dict[str, Any]] = {}
        self.ttls = {
            'recommendations': 300,  # 5 min
            'navigation': 900,       # 15 min
            'intent': 300,           # 5 min
            'query_cache': 3600      # 60 min
        }
    
    def set(self, key: str, value: Any, ttl: int):
        """Store with TTL expiry."""
        self.store[key] = {
            'value': value,
            'expires_at': time.time() + ttl
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get if not expired."""
        if key in self.store:
            if time.time() < self.store[key]['expires_at']:
                return self.store[key]['value']
            else:
                del self.store[key]  # Expired
        return None
    
    def delete(self, key: str):
        """Manually delete entry."""
        if key in self.store:
            del self.store[key]
    
    def cleanup_expired(self):
        """Remove all expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, data in self.store.items()
            if current_time >= data['expires_at']
        ]
        for key in expired_keys:
            del self.store[key]
    
    # Convenience methods
    def set_recommendations(self, user_id: str, data: dict):
        """Store recommendations with TTL."""
        self.set(
            f"recommendations:{user_id}",
            data,
            ttl=self.ttls['recommendations']
        )
    
    def get_recommendations(self, user_id: str) -> Optional[dict]:
        """Get recommendations if not expired."""
        return self.get(f"recommendations:{user_id}")
    
    def clear_recommendations(self, user_id: str):
        """Manually clear recommendations."""
        self.delete(f"recommendations:{user_id}")
    
    def set_navigation(self, user_id: str, data: dict):
        """Store navigation state with TTL."""
        self.set(
            f"navigation:{user_id}",
            data,
            ttl=self.ttls['navigation']
        )
    
    def get_navigation(self, user_id: str) -> Optional[dict]:
        """Get navigation state if not expired."""
        return self.get(f"navigation:{user_id}")
    
    def set_intent(self, user_id: str, intent: str):
        """Store last intent with TTL."""
        self.set(
            f"intent:{user_id}",
            intent,
            ttl=self.ttls['intent']
        )
    
    def get_intent(self, user_id: str) -> Optional[str]:
        """Get last intent if not expired."""
        return self.get(f"intent:{user_id}")

# Global instance
session_store = EphemeralSessionStore()
```

### Usage Examples

**Storing Recommendations**:
```python
# After RAG search
results = rag_pipeline.search(query="food", category="food")

session_store.set_recommendations("user_123", {
    'category': 'food',
    'results': results,
    'timestamp': datetime.now().isoformat()
})
```

**Retrieving Recommendations**:
```python
# On follow-up query
recommendations = session_store.get_recommendations("user_123")

if recommendations:
    # Still valid, use cached results
    return recommendations['results']
else:
    # Expired, perform new search
    return rag_pipeline.search(query)
```

**Storing Navigation**:
```python
# After route calculation
route = navigation_engine.find_route(start, end)

session_store.set_navigation("user_123", {
    'route': route,
    'destination': end,
    'started_at': datetime.now().isoformat()
})
```

---

## Layer 3: Turn State (Request Context)

### Purpose
Store information for a single request/response cycle only.

### Storage
- Request object (not persisted)
- Created fresh for each request
- Destroyed after response sent

### Data Structure

```python
class TurnContext:
    """Context for a single conversation turn."""
    
    user_id: str
    query: str
    current_location: Optional[str]
    input_mode: str  # 'text' or 'voice'
    whisper_lang: Optional[str]
    detected_intent: Optional[str]
    pipeline_results: Optional[dict]
    timestamp: datetime
```

### Implementation

```python
# Created per request
def process_chat_request(request: ChatRequest) -> ChatResponse:
    # Create turn context
    turn = TurnContext(
        user_id=request.user_id,
        query=request.message,
        current_location=request.location,
        input_mode=request.input_mode,
        whisper_lang=request.whisper_lang,
        timestamp=datetime.now()
    )
    
    # Process query
    turn.detected_intent = detect_intent(turn.query)
    turn.pipeline_results = execute_pipeline(turn)
    
    # Generate response
    response = generate_response(turn)
    
    # Turn context destroyed here (out of scope)
    return response
```

### What Belongs Here

✅ **Include**:
- Current query text
- Current location (for this request)
- Input mode (text/voice)
- Detected intent
- Pipeline execution results
- Temporary processing data

❌ **Exclude**:
- Anything that needs to persist
- Previous queries
- User preferences
- Cached results

### Lifetime
- **Single request** only
- Created at request start
- Destroyed after response sent
- Never persisted to disk

---

## Complete Flow Example

### Scenario: User asks for food, then shops

#### Request 1: "I want food"

```python
# 1. Load persistent profile
user_profile = load_user_profile("user_123")
# Result: {flight_number: "AI123", preferences: {...}}

# 2. Load ephemeral session
session = {
    'recommendations': session_store.get_recommendations("user_123"),
    'navigation': session_store.get_navigation("user_123"),
    'last_intent': session_store.get_intent("user_123")
}
# Result: All None (first query)

# 3. Create turn context
turn = TurnContext(
    user_id="user_123",
    query="I want food",
    current_location="entrance",
    input_mode="text"
)

# 4. Process query
turn.detected_intent = detect_intent("I want food")  # 'discovery'
results = rag_pipeline.search(
    query="food",
    category="food",
    location=turn.current_location
)
turn.pipeline_results = results

# 5. Save to ephemeral cache
session_store.set_recommendations("user_123", {
    'category': 'food',
    'results': results,
    'query': turn.query,
    'timestamp': datetime.now().isoformat()
})

session_store.set_intent("user_123", 'discovery')

# 6. Generate and return response
response = {
    'type': 'recommendations',
    'intent': 'discovery',
    'message': format_recommendations(results),
    'data': {'recommendations': results},
    'context': {
        'last_intent': 'discovery',
        'last_recommendations': True
    }
}

# Turn context destroyed here
return response
```

#### Request 2: "Show me shops" (2 minutes later)

```python
# 1. Load persistent profile
user_profile = load_user_profile("user_123")
# Result: {flight_number: "AI123", preferences: {...}}

# 2. Load ephemeral session
last_recommendations = session_store.get_recommendations("user_123")
# Result: {category: 'food', results: [...], timestamp: '...'}
# Still exists (only 2 min passed, TTL is 5 min)

last_intent = session_store.get_intent("user_123")
# Result: 'discovery'

# 3. Create turn context
turn = TurnContext(
    user_id="user_123",
    query="Show me shops",
    current_location="entrance",
    input_mode="text"
)

# 4. Detect intent change
turn.detected_intent = detect_intent("Show me shops")  # 'discovery'
# Same intent, but different category!

# 5. Check if category changed
old_category = last_recommendations.get('category') if last_recommendations else None
new_category = extract_category("Show me shops")  # 'shopping'

if old_category != new_category:
    # Clear old recommendations
    session_store.clear_recommendations("user_123")

# 6. Process new query
results = rag_pipeline.search(
    query="shops",
    category="shopping",
    location=turn.current_location
)
turn.pipeline_results = results

# 7. Save new recommendations
session_store.set_recommendations("user_123", {
    'category': 'shopping',
    'results': results,
    'query': turn.query,
    'timestamp': datetime.now().isoformat()
})

# 8. Generate and return response
response = {
    'type': 'recommendations',
    'intent': 'discovery',
    'message': format_recommendations(results),
    'data': {'recommendations': results},  # SHOPS, not food!
    'context': {
        'last_intent': 'discovery',
        'last_recommendations': True
    }
}

# Turn context destroyed here
return response
```

---

## Context Management

### Loading Context

```python
def load_context(user_id: str) -> dict:
    """Load context from all layers."""
    
    context = {}
    
    # Layer 1: Persistent profile
    profile = load_user_profile(user_id)
    context.update({
        'user_id': user_id,
        'flight_info': {
            'flight_number': profile.get('flight_number'),
            'boarding_time': profile.get('boarding_time'),
            'departure_time': profile.get('departure_time'),
            'gate': profile.get('gate')
        },
        'preferences': profile.get('preferences', {})
    })
    
    # Layer 2: Ephemeral session
    recommendations = session_store.get_recommendations(user_id)
    navigation = session_store.get_navigation(user_id)
    last_intent = session_store.get_intent(user_id)
    
    context.update({
        'last_recommendations': recommendations,
        'active_navigation': navigation,
        'last_intent': last_intent
    })
    
    # Layer 3: Turn state (created per request, not loaded)
    
    return context
```

### Saving Context

```python
def save_context(user_id: str, context: dict):
    """Save context to appropriate layers."""
    
    # Layer 1: Persistent profile
    persistent_fields = {}
    if 'flight_number' in context:
        persistent_fields['flight_number'] = context['flight_number']
    if 'boarding_time' in context:
        persistent_fields['boarding_time'] = context['boarding_time']
    if 'departure_time' in context:
        persistent_fields['departure_time'] = context['departure_time']
    if 'preferences' in context:
        persistent_fields['preferences'] = context['preferences']
    
    if persistent_fields:
        save_user_profile(user_id, persistent_fields)
    
    # Layer 2: Ephemeral session
    if 'recommendations' in context:
        session_store.set_recommendations(user_id, context['recommendations'])
    
    if 'navigation' in context:
        session_store.set_navigation(user_id, context['navigation'])
    
    if 'intent' in context:
        session_store.set_intent(user_id, context['intent'])
    
    # Layer 3: Turn state (not persisted)
```

---

## Key Design Decisions

### 1. Why Separate Layers?

**Problem**: Mixing persistent and transient state causes contamination.

**Solution**: Clear separation with different storage mechanisms and lifetimes.

**Benefits**:
- No contamination between queries
- Clear data ownership
- Easy to debug and maintain

### 2. Why TTL-Based Expiry?

**Problem**: Manual cache invalidation is error-prone and complex.

**Solution**: Automatic expiry based on time.

**Benefits**:
- Automatic cleanup
- No memory leaks
- Predictable behavior

### 3. Why Different TTLs?

**Problem**: Not all data has the same relevance window.

**Solution**: Tune TTL based on use case.

**Examples**:
- Recommendations: 5 min (quick follow-ups expected)
- Navigation: 15 min (walking takes time)
- Query cache: 60 min (performance optimization)

### 4. Why Not Just Clear on Intent Change?

**Problem**: Intent might be the same but category different.

**Example**: 
- "I want food" → intent: discovery, category: food
- "I want coffee" → intent: discovery, category: food (still food!)
- "I want shops" → intent: discovery, category: shopping (different!)

**Solution**: Combine TTL + intent tracking + category detection.

---

## Benefits

### 1. No Contamination
- Recommendations expire automatically
- Intent changes clear old state
- Clean slate for new queries
- No stale data

### 2. Performance
- Cached results for quick follow-ups
- No redundant searches
- Fast context loading
- Efficient memory usage

### 3. User Experience
- Remembers important info (flight)
- Forgets irrelevant info (old recommendations)
- Natural conversation flow
- Context-aware responses

### 4. Maintainability
- Clear separation of concerns
- Easy to debug (check each layer)
- Simple to extend
- Well-defined interfaces

### 5. Scalability
- In-memory cache for speed
- Can move to Redis for distributed systems
- TTL prevents memory leaks
- Horizontal scaling ready

---

## Production Considerations

### Redis Integration

For production, replace in-memory cache with Redis:

```python
import redis

class RedisSessionStore:
    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
    
    def set(self, key: str, value: Any, ttl: int):
        """Store with TTL in Redis."""
        self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get from Redis."""
        value = self.redis.get(key)
        return json.loads(value) if value else None
    
    def delete(self, key: str):
        """Delete from Redis."""
        self.redis.delete(key)
```

### Database Migration

For persistent storage, migrate from JSON to database:

```python
# SQLAlchemy model
class UserProfile(Base):
    __tablename__ = 'user_profiles'
    
    user_id = Column(String, primary_key=True)
    flight_number = Column(String, nullable=True)
    boarding_time = Column(DateTime, nullable=True)
    departure_time = Column(DateTime, nullable=True)
    gate = Column(String, nullable=True)
    preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
```

### Monitoring

Track memory usage and cache performance:

```python
def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        'total_keys': len(session_store.store),
        'expired_keys': count_expired_keys(),
        'memory_usage': get_memory_usage(),
        'hit_rate': calculate_hit_rate(),
        'avg_ttl': calculate_avg_ttl()
    }
```

---

## Future Enhancements

### 1. Smart TTL
Adjust TTL based on user behavior:
- Frequent users: Longer TTL
- Infrequent users: Shorter TTL
- Active navigation: Extended TTL

### 2. Predictive Caching
Pre-cache likely next queries:
- If user asks for food, pre-cache nearby restaurants
- If user navigates to gate, pre-cache gate facilities

### 3. Session Analytics
Track session patterns:
- Common query sequences
- Average session duration
- Cache hit rates
- Optimization opportunities

### 4. Multi-Device Sync
Sync session across devices:
- User starts on phone, continues on kiosk
- Shared session state via Redis
- Conflict resolution

### 5. Personalization Engine
Learn user preferences over time:
- Favorite food types
- Preferred shops
- Accessibility needs
- Language preferences

---

## Conclusion

The 3-layer memory architecture is a key innovation that enables AirHelp to provide a clean, fast, and reliable conversational experience. By separating persistent user data from ephemeral session state, we solve the contamination problem while maintaining performance and user experience.

**Key Takeaways**:
- **Layer 1**: Persistent profile (permanent)
- **Layer 2**: Ephemeral session (TTL-based)
- **Layer 3**: Turn state (request-only)
- **Result**: Clean, fast, reliable conversations

---

**Related Documentation**:
- [Context Engine](context-engine.md)
- [Orchestrator](orchestrator.md)
- [Session Management](../backend/session-management.md)
