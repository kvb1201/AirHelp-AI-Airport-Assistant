# backend/app/services/rag_service.py

from typing import List, Dict
from app.core.rag.pipeline import AirportRAGPipeline

_pipeline = None


# -------------------------------
# 🔹 Initialize RAG (once at startup)
# -------------------------------
def init_rag():
    global _pipeline

    if _pipeline is None:
        print("🔄 Initializing RAG pipeline...")

        _pipeline = AirportRAGPipeline(
            json_path="app/core/rag/airport_data.json"
        )

        _pipeline.load_and_index()

        print("✅ RAG pipeline ready")


# -------------------------------
# 🔹 Search Function
# -------------------------------
def search(query: str, location: str = None, top_k: int = 5) -> List[Dict]:
    """
    Perform semantic search over airport data.

    Args:
        query: user query
        location: optional location bias (e.g., "near security")
        top_k: number of results

    Returns:
        list of normalized results
    """

    if _pipeline is None:
        print("[RAG WARNING] Pipeline not initialized")
        return []

    try:
        # 🔥 Inject location bias into query (simple but effective)
        final_query = query
        if location and location != "unknown":
            final_query = f"{query} near {location}"

        results = _pipeline.query(final_query, top_k=top_k)

        # 🔹 Normalize for LLM
        formatted = []
        for r in results:
            formatted.append({
                "name": r.get("name", ""),
                "category": r.get("category", ""),
                "location": r.get("location", ""),
                "description": r.get("description", ""),
            })

        return formatted

    except Exception as e:
        print("[RAG ERROR]", e)
        return []