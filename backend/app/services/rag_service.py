# backend/app/services/rag_service.py

import os
import re
from typing import List, Dict, Any

# 🔕 Disable Chroma telemetry (must be before import)
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

from app.core.rag.pipeline import AirportRAGPipeline

_pipeline = None


# -------------------------------
# 🔹 Initialize RAG
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
# 🔹 Extract structured info from text
# -------------------------------
def _parse_text_chunk(text: str) -> Dict[str, str]:
    """
    Extract name + location from raw RAG text.
    """

    name = None
    location = None

    # 🔹 Extract name inside quotes
    name_match = re.search(r"'([^']+)'", text)
    if name_match:
        name = name_match.group(1)

    # 🔹 Extract location
    loc_match = re.search(r"Location:\s*(.*?)(?:\.|$)", text)
    if loc_match:
        location = loc_match.group(1).strip()

    # 🔹 Fallback: first meaningful phrase
    if not name:
        first_line = text.split(".")[0]
        name = first_line[:50].strip()

    return {
        "name": name,
        "category": "",
        "location": location or "",
        "description": text.strip(),
    }


# -------------------------------
# 🔹 Validate result quality
# -------------------------------
def _is_valid_result(item: Dict[str, Any]) -> bool:
    """
    Remove garbage / empty results.
    """
    if not item:
        return False

    if not item.get("name") and not item.get("description"):
        return False

    # Avoid meaningless outputs
    if item.get("name") in ["", "Unknown", None]:
        return False

    return True


# -------------------------------
# 🔹 Search (Retrieval ONLY)
# -------------------------------
def search(query: str, location: str = None, top_k: int = 5) -> List[Dict]:
    """
    Semantic retrieval over airport data.
    Returns clean structured results.
    """

    if _pipeline is None:
        print("[RAG WARNING] Pipeline not initialized")
        return []

    try:
        # 🔥 Add location bias
        final_query = query
        if location and location != "unknown":
            final_query = f"{query} near {location}"

        # 🔥 Use retriever directly (no LLM contamination)
        results = _pipeline._retriever.retrieve(final_query, top_k=top_k)

        print("RAW RETRIEVER RESULTS:", results)

        formatted: List[Dict[str, Any]] = []

        for r in results:

            # -----------------------
            # Case 1: Structured dict
            # -----------------------
            if isinstance(r, dict):
                item = {
                    "name": r.get("name") or r.get("title"),
                    "category": r.get("category", ""),
                    "location": r.get("location", ""),
                    "description": r.get("description") or r.get("text", ""),
                }

            # -----------------------
            # Case 2: Raw text chunk
            # -----------------------
            elif isinstance(r, str):
                item = _parse_text_chunk(r)

            # -----------------------
            # Case 3: Unknown type
            # -----------------------
            else:
                item = {
                    "name": None,
                    "category": "",
                    "location": "",
                    "description": str(r),
                }

            # 🔥 Filter garbage
            if _is_valid_result(item):
                formatted.append(item)

        return formatted[:top_k]

    except Exception as e:
        print("[RAG ERROR]", e)
        return []