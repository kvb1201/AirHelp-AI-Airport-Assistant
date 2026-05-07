# RAG Pipeline Architecture

## Purpose

The Retrieval-Augmented Generation (RAG) pipeline enables semantic search over airport facilities, shops, and services, combining vector similarity search with metadata filtering and LLM-based response synthesis to provide accurate, contextual recommendations.

## Why RAG?

Traditional keyword search fails in conversational contexts:

- **Semantic Gap**: "I'm hungry" ≠ "food" (keyword match fails)
- **Context Loss**: "Something quick" requires understanding urgency
- **Ambiguity**: "Electronics" could mean shops, charging stations, or repair services
- **Personalization**: Recommendations should consider user preferences and location

**RAG Solution**: Semantic understanding + structured data + LLM synthesis = Contextual, accurate responses

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG PIPELINE                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         1. QUERY PREPROCESSING                         │ │
│  │                                                        │ │
│  │  User Query → Normalization → Entity Extraction       │ │
│  │                                                        │ │
│  │  Steps:                                               │ │
│  │  ├─ Lowercase, trim                                   │ │
│  │  ├─ Slang normalization ("wanna eat" → "want food")  │ │
│  │  ├─ Entity extraction (category, location, price)    │ │
│  │  └─ Query expansion (synonyms, related terms)        │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         2. EMBEDDING GENERATION                        │ │
│  │                                                        │ │
│  │  Query → Sentence Transformer → 384-dim Vector        │ │
│  │                                                        │ │
│  │  Model: all-MiniLM-L6-v2                              │ │
│  │  ├─ Fast inference (~50ms)                            │ │
│  │  ├─ Good semantic understanding                       │ │
│  │  └─ Offline-capable                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         3. VECTOR SEARCH                               │ │
│  │                                                        │ │
│  │  Query Vector → ChromaDB → Top-K Results              │ │
│  │                                                        │ │
│  │  Search Parameters:                                   │ │
│  │  ├─ Similarity: Cosine                                │ │
│  │  ├─ Top-K: 20 (before filtering)                      │ │
│  │  ├─ Metadata Filters: category, location, price      │ │
│  │  └─ Distance Threshold: 0.3                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         4. METADATA FILTERING                          │ │
│  │                                                        │ │
│  │  Results → Filter by Context → Filtered Results       │ │
│  │                                                        │ │
│  │  Filters:                                             │ │
│  │  ├─ Category (food, shopping, facilities)            │ │
│  │  ├─ Location (terminal, level, zone)                 │ │
│  │  ├─ Price Range (budget, mid, premium)               │ │
│  │  ├─ Operating Hours (open now)                       │ │
│  │  └─ Accessibility (wheelchair, family)               │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         5. RERANKING                                   │ │
│  │                                                        │ │
│  │  Filtered Results → Rerank by Relevance → Top-5       │ │
│  │                                                        │ │
│  │  Reranking Factors:                                   │ │
│  │  ├─ Semantic similarity (primary)                     │ │
│  │  ├─ Distance from user (secondary)                    │ │
│  │  ├─ Rating/popularity (tertiary)                      │ │
│  │  └─ Recency (for time-sensitive queries)             │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         6. LLM SYNTHESIS                               │ │
│  │                                                        │ │
│  │  Top Results + Context → LLM → Natural Response       │ │
│  │                                                        │ │
│  │  Prompt Structure:                                    │ │
│  │  ├─ System: Role definition                           │ │
│  │  ├─ Context: User location, preferences               │ │
│  │  ├─ Data: Retrieved results                           │ │
│  │  ├─ Query: User question                              │ │
│  │  └─ Instructions: Format, tone, constraints          │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         7. RESPONSE VALIDATION                         │ │
│  │                                                        │ │
│  │  LLM Output → Hallucination Check → Final Response    │ │
│  │                                                        │ │
│  │  Validation:                                          │ │
│  │  ├─ Fact checking (names, locations match data)      │ │
│  │  ├─ Completeness (all requested info included)       │ │
│  │  ├─ Consistency (no contradictions)                  │ │
│  │  └─ Formatting (proper structure)                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Query Preprocessing

**Slang Normalization**:
```python
SLANG_MAP = {
    'wanna': 'want to',
    'gonna': 'going to',
    'gotta': 'got to',
    'lemme': 'let me',
    'gimme': 'give me',
    'dunno': "don't know",
    'kinda': 'kind of',
    'sorta': 'sort of'
}

def normalize_slang(query: str) -> str:
    """Normalize colloquial language."""
    for slang, formal in SLANG_MAP.items():
        query = query.replace(slang, formal)
    return query
```

**Entity Extraction**:
```python
def extract_entities(query: str) -> dict:
    """Extract structured entities from query."""
    
    entities = {
        'category': None,
        'location': None,
        'price_range': None,
        'urgency': None
    }
    
    # Category detection
    if any(word in query for word in ['food', 'eat', 'hungry', 'restaurant']):
        entities['category'] = 'food'
    elif any(word in query for word in ['shop', 'buy', 'store', 'shopping']):
        entities['category'] = 'shopping'
    elif any(word in query for word in ['lounge', 'relax', 'wait']):
        entities['category'] = 'lounge'
    
    # Urgency detection
    if any(word in query for word in ['quick', 'fast', 'hurry', 'urgent']):
        entities['urgency'] = 'high'
    
    # Price range detection
    if any(word in query for word in ['cheap', 'budget', 'affordable']):
        entities['price_range'] = 'budget'
    elif any(word in query for word in ['expensive', 'premium', 'luxury']):
        entities['price_range'] = 'premium'
    
    return entities
```

### 2. Embedding Generation

**Model**: `sentence-transformers/all-MiniLM-L6-v2`

**Characteristics**:
- Dimension: 384
- Speed: ~50ms per query
- Quality: Good for short texts
- Size: 80MB (lightweight)

**Implementation**:
```python
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for query."""
        return self.model.encode(query, convert_to_numpy=True).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return self.model.encode(texts, convert_to_numpy=True).tolist()
```

### 3. Vector Search

**ChromaDB Configuration**:
```python
import chromadb

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="airport_facilities",
            metadata={"hnsw:space": "cosine"}
        )
    
    def search(
        self,
        query_embedding: List[float],
        filters: dict = None,
        top_k: int = 20
    ) -> List[dict]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            filters: Metadata filters (category, location, etc.)
            top_k: Number of results to return
        
        Returns:
            List of matching documents with metadata
        """
        
        where_clause = {}
        if filters:
            if filters.get('category'):
                where_clause['category'] = filters['category']
            if filters.get('location'):
                where_clause['location'] = filters['location']
            if filters.get('price_range'):
                where_clause['price_range'] = filters['price_range']
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            where=where_clause if where_clause else None,
            n_results=top_k
        )
        
        return self._format_results(results)
```

### 4. Metadata Filtering

**Filter Schema**:
```python
class MetadataFilters:
    category: Optional[str]  # food, shopping, facilities, lounge
    location: Optional[str]  # terminal_2, level_2, zone_a
    price_range: Optional[str]  # budget, mid, premium
    operating_hours: Optional[bool]  # open_now
    accessibility: Optional[List[str]]  # wheelchair, family, quiet
    distance_max: Optional[int]  # meters from user location
```

**Filtering Logic**:
```python
def apply_filters(results: List[dict], filters: MetadataFilters, user_location: str) -> List[dict]:
    """Apply post-retrieval filters."""
    
    filtered = results
    
    # Distance filter
    if filters.distance_max and user_location:
        filtered = [
            r for r in filtered
            if calculate_distance(user_location, r['location']) <= filters.distance_max
        ]
    
    # Operating hours filter
    if filters.operating_hours:
        current_time = datetime.now().time()
        filtered = [
            r for r in filtered
            if is_open(r['hours'], current_time)
        ]
    
    # Accessibility filter
    if filters.accessibility:
        filtered = [
            r for r in filtered
            if all(feature in r.get('accessibility', []) for feature in filters.accessibility)
        ]
    
    return filtered
```

### 5. Reranking

**Reranking Algorithm**:
```python
def rerank_results(
    results: List[dict],
    query: str,
    user_location: str,
    weights: dict = None
) -> List[dict]:
    """
    Rerank results by multiple factors.
    
    Default weights:
    - Semantic similarity: 0.5
    - Distance: 0.3
    - Rating: 0.2
    """
    
    if weights is None:
        weights = {'similarity': 0.5, 'distance': 0.3, 'rating': 0.2}
    
    for result in results:
        # Normalize scores to [0, 1]
        similarity_score = result['similarity']  # Already 0-1
        distance_score = 1 - (result['distance'] / 1000)  # Normalize by max distance
        rating_score = result.get('rating', 3.0) / 5.0  # Normalize by max rating
        
        # Weighted combination
        result['final_score'] = (
            weights['similarity'] * similarity_score +
            weights['distance'] * distance_score +
            weights['rating'] * rating_score
        )
    
    # Sort by final score
    return sorted(results, key=lambda x: x['final_score'], reverse=True)
```

### 6. LLM Synthesis

**Prompt Template**:
```python
RECOMMENDATION_PROMPT = """You are an AI assistant helping passengers at Mumbai Airport Terminal 2.

User Context:
- Current Location: {user_location}
- Flight Info: {flight_info}
- Preferences: {preferences}

User Query: {query}

Retrieved Information:
{retrieved_data}

Instructions:
1. Provide a natural, conversational response
2. Recommend the top 3-5 options from the retrieved data
3. Include key details: name, location, distance, special features
4. Be concise but helpful
5. Use the exact names and locations from the data (no hallucinations)
6. If the user asked for something specific (e.g., "quick food"), prioritize accordingly

Response:"""

def generate_response(query: str, results: List[dict], context: dict) -> str:
    """Generate LLM response."""
    
    # Format retrieved data
    retrieved_data = "\n".join([
        f"- {r['name']}: {r['description']} (Location: {r['location']}, Distance: {r['distance']}m)"
        for r in results[:5]
    ])
    
    # Build prompt
    prompt = RECOMMENDATION_PROMPT.format(
        user_location=context.get('current_location', 'Unknown'),
        flight_info=context.get('flight_info', 'Not provided'),
        preferences=context.get('preferences', 'None'),
        query=query,
        retrieved_data=retrieved_data
    )
    
    # Call LLM
    response = llm_service.generate(prompt, max_tokens=300)
    
    return response
```

### 7. Response Validation

**Hallucination Detection**:
```python
def validate_response(response: str, retrieved_data: List[dict]) -> tuple[bool, str]:
    """
    Check if LLM response contains hallucinations.
    
    Returns:
        (is_valid, error_message)
    """
    
    # Extract mentioned names from response
    mentioned_names = extract_entity_names(response)
    
    # Check if all mentioned names exist in retrieved data
    valid_names = {r['name'] for r in retrieved_data}
    
    for name in mentioned_names:
        if name not in valid_names:
            return False, f"Hallucinated entity: {name}"
    
    # Check for contradictions
    for result in retrieved_data:
        if result['name'] in response:
            # Verify location matches
            if result['location'] not in response:
                return False, f"Incorrect location for {result['name']}"
    
    return True, ""
```

## Data Schema

### Document Structure

```python
class FacilityDocument:
    id: str  # Unique identifier
    name: str  # Facility name
    category: str  # food, shopping, facilities, lounge
    subcategory: str  # cafe, restaurant, electronics, etc.
    description: str  # Detailed description
    location: str  # terminal_2_level_2_zone_a
    coordinates: dict  # {x: float, y: float}
    price_range: str  # budget, mid, premium
    rating: float  # 1.0 - 5.0
    hours: dict  # {open: "06:00", close: "23:00"}
    accessibility: List[str]  # wheelchair, family, quiet
    amenities: List[str]  # wifi, charging, seating
    tags: List[str]  # quick, healthy, vegetarian, etc.
    embedding: List[float]  # 384-dim vector
```

### Example Document

```json
{
  "id": "starbucks_t2_l2",
  "name": "Starbucks",
  "category": "food",
  "subcategory": "cafe",
  "description": "International coffee chain offering hot and cold beverages, pastries, and sandwiches",
  "location": "terminal_2_level_2_zone_a",
  "coordinates": {"x": 150.5, "y": 200.3},
  "price_range": "mid",
  "rating": 4.5,
  "hours": {"open": "05:00", "close": "23:00"},
  "accessibility": ["wheelchair", "family"],
  "amenities": ["wifi", "charging", "seating"],
  "tags": ["quick", "coffee", "breakfast", "snacks"],
  "embedding": [0.123, -0.456, ...]
}
```

## Performance Optimization

### Caching Strategy

```python
class RAGCache:
    def __init__(self):
        self.query_cache = {}  # Query → Results
        self.embedding_cache = {}  # Text → Embedding
    
    def get_cached_results(self, query: str, ttl: int = 300) -> Optional[List[dict]]:
        """Get cached results if available and fresh."""
        if query in self.query_cache:
            cached = self.query_cache[query]
            if time.time() - cached['timestamp'] < ttl:
                return cached['results']
        return None
    
    def cache_results(self, query: str, results: List[dict]):
        """Cache query results."""
        self.query_cache[query] = {
            'results': results,
            'timestamp': time.time()
        }
```

### Batch Processing

```python
async def process_batch_queries(queries: List[str]) -> List[List[dict]]:
    """Process multiple queries in parallel."""
    
    # Generate embeddings in batch
    embeddings = embedding_service.embed_batch(queries)
    
    # Search in parallel
    tasks = [
        vector_store.search(emb, top_k=20)
        for emb in embeddings
    ]
    results = await asyncio.gather(*tasks)
    
    return results
```

## Challenges & Solutions

### Challenge 1: Category Contamination

**Problem**: Recommendations from previous queries persist in subsequent queries.

**Example**:
```
User: "I want food"
System: [Returns food recommendations, caches them]

User: "Show me shops"
System: [Still shows food recommendations due to cache]
```

**Solution**: Ephemeral cache with TTL + intent-based cache invalidation.

```python
def get_recommendations(query: str, user_id: str) -> List[dict]:
    # Check if intent changed
    current_intent = detect_intent(query)
    last_intent = cache.get(f"intent:{user_id}")
    
    if current_intent != last_intent:
        # Clear cache on intent change
        cache.delete(f"recommendations:{user_id}")
    
    # Update intent
    cache.set(f"intent:{user_id}", current_intent, ttl=300)
    
    # Proceed with search
    ...
```

### Challenge 2: Hallucinations

**Problem**: LLM invents facility names or locations not in the data.

**Solution**: Strict validation + constrained generation.

```python
def generate_with_validation(query: str, results: List[dict]) -> str:
    response = llm_service.generate(prompt)
    
    is_valid, error = validate_response(response, results)
    
    if not is_valid:
        # Fallback to template-based response
        return generate_template_response(results)
    
    return response
```

### Challenge 3: Semantic Ambiguity

**Problem**: "Electronics" could mean shops, charging stations, or repair services.

**Solution**: Context-aware disambiguation.

```python
def disambiguate_query(query: str, context: dict) -> str:
    if 'electronics' in query:
        if 'buy' in query or 'shop' in query:
            return query + " shopping"
        elif 'charge' in query or 'power' in query:
            return query + " charging station"
        elif 'fix' in query or 'repair' in query:
            return query + " repair service"
    return query
```

## Monitoring & Metrics

### Key Metrics

- **Retrieval Precision**: % of relevant results in top-K
- **Retrieval Recall**: % of relevant documents retrieved
- **Response Latency**: Time from query to response
- **Cache Hit Rate**: % of queries served from cache
- **Hallucination Rate**: % of responses with hallucinations
- **User Satisfaction**: Feedback on recommendations

### Logging

```python
logger.info("RAG query processed", extra={
    'query': query,
    'results_count': len(results),
    'reranked_count': len(reranked),
    'latency_ms': latency,
    'cache_hit': cache_hit,
    'hallucination_detected': hallucination_detected
})
```

## Future Improvements

1. **Hybrid Search**: Combine vector search with keyword search (BM25)
2. **Query Expansion**: Use LLM to expand queries with synonyms
3. **Personalization**: Learn user preferences over time
4. **Multi-Modal**: Support image-based queries (e.g., "Find this shop")
5. **Real-Time Updates**: Integrate live data (wait times, availability)

---

**Related Documentation**:
- [Embedding Models](../ai/embedding-models.md)
- [LLM Orchestration](../ai/llm-orchestration.md)
- [Reranking](../ai/reranking.md)
