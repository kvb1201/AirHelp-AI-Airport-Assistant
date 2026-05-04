# RAG Service (Retrieval-Augmented Generation)

## Retrieval Pipeline
The RAG service utilizes ChromaDB to handle unstructured data (e.g., terminal guidelines, security FAQs).
1.  **Ingestion:** Documents are chunked and embedded using an embedding model during initialization.
2.  **Query Embedding:** The user's query is converted into a vector representation.
3.  **Vector Search:** ChromaDB returns the top-K chunks based on cosine similarity.
4.  **Context Injection:** The retrieved text is injected into the LLM prompt.

## Filtering (Category + Location)
To prevent semantic bleeding (e.g., returning gate information when asked about food), the retrieval pipeline leverages metadata filtering. 
When the Orchestrator passes category constraints, the RAG engine applies strict `WHERE` clauses (e.g., `metadata.category == 'food'`) during the vector search, guaranteeing domain relevance.

## Ranking Logic
Results are ranked primarily by vector similarity score. However, for localized queries ("near me"), spatial data (distance from the user's current node) can be used as a secondary re-ranking mechanism to surface the closest relevant unstructured data.

## Limitations
*   **Procedural Workflows:** RAG retrieves static paragraphs. It cannot execute multi-step logic (e.g., a conditional check-in process).
*   **Exact Match Failures:** Highly specific factual queries (e.g., "What time does store X close?") are sometimes missed if the exact phrasing isn't semantically close to the chunk. (This is mitigated by the Knowledge Service).
