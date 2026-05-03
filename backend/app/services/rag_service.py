# backend/app/services/rag_service.py

def search(query: str):
    """
    Mock RAG retrieval.
    Later: replace with FAISS / semantic search.
    """

    if "coffee" in query.lower():
        return [
            {"name": "Cafe A", "distance": "2 min", "time_required": 5},
            {"name": "Coffee Express", "distance": "3 min", "time_required": 4}
        ]

    if "food" in query.lower():
        return [
            {"name": "Food Court", "distance": "5 min", "time_required": 10}
        ]

    return []