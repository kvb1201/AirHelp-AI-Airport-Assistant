# backend/app/services/rag_service.py

import os
import re
from typing import List, Dict, Any, Optional

# 🔕 Disable Chroma telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

from app.core.rag.pipeline import AirportRAGPipeline

_pipeline = None


# -----------------------------------------------
# Category allow-lists
# -----------------------------------------------
_CATEGORY_MAP: Dict[str, set] = {
    "recommendation": {"food_court"},
    "explore": {"food_court", "shop", "service", "facility"},
}

_NON_ACTIONABLE = {"terminal", "gate", "check_in_counter", "baggage_belt"}

# Terminal number → all equivalent strings in RAG location data
_TERMINAL_ALIASES = {
    "1": ["terminal 1", "terminal1", "t1"],
    "2": ["terminal 2", "terminal2", "t2"],
    "3": ["terminal 3", "terminal3", "t3"],
}


# -------------------------------
# 🔹 Initialize
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


# -----------------------------------------------
# 🔹 Entity Query Detection (NEW)
# -----------------------------------------------
def _is_entity_query(query: str) -> bool:
    """
    Detect queries asking about a SPECIFIC named entity.
    These should NOT be location-filtered — they should return
    wherever the entity is.

    Examples:
      "Where is SkyLounge Premium Lounge?" → True
      "find Café Aroma" → True
      "food near terminal 3" → False
    """
    q = query.lower()

    return any([
        "where is" in q,
        "locate " in q,
        "find " in q and "near" not in q,
    ])


# -----------------------------------------------
# 🔹 Terminal Extraction (NEW — CRITICAL)
# -----------------------------------------------
def _extract_terminal_number(location: str) -> Optional[str]:
    """
    Extract just the terminal number (1, 2, or 3) from any
    location format. Returns None if not a terminal-level location.

    Handles:
      "terminal_3"      → "3"
      "terminal 2"      → "2"
      "t2_entrance"     → "2"
      "entrance"        → None  (not a terminal!)
      "gate_B12"        → None  (not terminal-level)
    """
    if not location:
        return None

    loc = location.lower().strip()

    # "terminal_3", "terminal 3", "terminal3"
    m = re.search(r"terminal[_\s]*([1-3])", loc)
    if m:
        return m.group(1)

    # "t2_entrance", "t2", "t1"
    m = re.match(r"^t([1-3])(?:[_\s]|$)", loc)
    if m:
        return m.group(1)

    return None


def _item_matches_terminal(item_location: str, terminal_num: str) -> bool:
    """
    Check if a RAG item's location field belongs to the given terminal.
    RAG data uses formats like "Terminal 3, Level 1, C-concourse entrance".
    """
    if not item_location or not terminal_num:
        return False

    item_lower = item_location.lower()
    aliases = _TERMINAL_ALIASES.get(terminal_num, [])

    return any(alias in item_lower for alias in aliases)


# -------------------------------
# 🔹 Parse Result
# -------------------------------
def _parse_result(r: Any) -> Dict[str, Any]:
    if isinstance(r, dict) and "metadata" in r:
        meta = r.get("metadata", {})
        text = r.get("text", "")

        name = meta.get("name") or meta.get("id") or ""
        category = meta.get("category", "")

        # If name is still empty, extract from chunk text
        if not name:
            m = re.search(r"'([^']+)'", text)
            if m:
                name = m.group(1)

        return {
            "name": name or "Unknown",
            "category": category,
            "location": meta.get("location", ""),
            "description": text,
            "score": r.get("score", 0),
        }

    if isinstance(r, dict):
        return {
            "name": r.get("name") or r.get("title") or "Unknown",
            "category": r.get("category", ""),
            "location": r.get("location", ""),
            "description": r.get("description") or r.get("text", ""),
            "score": r.get("score", 0),
        }

    if isinstance(r, str):
        name_match = re.search(r"'([^']+)'", r)
        name = name_match.group(1) if name_match else r[:50]

        loc_match = re.search(r"Location:\s*(.*?)(?:\.|$)", r)
        location = loc_match.group(1).strip() if loc_match else ""

        return {
            "name": name,
            "category": "",
            "location": location,
            "description": r,
            "score": 0,
        }

    return {
        "name": str(r),
        "category": "",
        "location": "",
        "description": "",
        "score": 0,
    }


# -------------------------------
# 🔹 Validate
# -------------------------------
def _is_valid(x: Dict[str, Any]) -> bool:
    return x and x.get("name") not in ["", "Unknown", None]


# -------------------------------
# 🔹 Category Filter (SAFE)
# -------------------------------
def _filter_by_category(results: List[Dict], intent: Optional[str]):
    allowed = _CATEGORY_MAP.get(intent)

    if allowed:
        filtered = [r for r in results if r.get("category") in allowed]

        # ⚠️ fallback if too strict
        if filtered:
            return filtered

    # always remove non-actionable
    return [
        r for r in results
        if r.get("category") not in _NON_ACTIONABLE
    ]


# -----------------------------------------------
# 🔹 Location Filter (REWRITTEN — terminal-level)
# -----------------------------------------------
def _filter_by_location(
    results: List[Dict],
    location: Optional[str],
) -> List[Dict]:
    """
    Filter results by TERMINAL-LEVEL match only.

    - Only filters if the location maps to a terminal (1, 2, or 3).
    - Non-terminal locations (entrance, gate_B12) → no filtering.
    - Returns all results if no matches found (soft fallback).
    """
    if not location:
        return results

    terminal_num = _extract_terminal_number(location)

    if not terminal_num:
        # Non-terminal location → don't filter (would cause false positives)
        print(f"[RAG] Location '{location}' is not terminal-level → skipping location filter")
        return results

    filtered = [
        r for r in results
        if _item_matches_terminal(r.get("location", ""), terminal_num)
    ]

    print(f"[RAG] Location Filter (Terminal {terminal_num}) → {len(filtered)} / {len(results)} matched")

    # Soft fallback: if nothing matched, return all rather than empty
    return filtered if filtered else results


# -------------------------------
# 🔹 Ranking
# -------------------------------
def _rank(
    results: List[Dict],
    location: Optional[str],
    intent: Optional[str],
) -> List[Dict]:
    terminal_num = _extract_terminal_number(location)
    allowed = _CATEGORY_MAP.get(intent, set())

    def score(x):
        sem = float(x.get("score", 0))

        # Terminal match bonus
        item_loc = x.get("location", "")
        loc_bonus = 0.5 if terminal_num and _item_matches_terminal(item_loc, terminal_num) else 0

        # Category bonus
        cat_bonus = 0.2 if x.get("category") in allowed else 0

        # Penalty for non-actionable
        penalty = -0.5 if x.get("category") in _NON_ACTIONABLE else 0

        return sem + loc_bonus + cat_bonus + penalty

    ranked = sorted(results, key=score, reverse=True)

    print("[RAG] Top Ranked:")
    for r in ranked[:3]:
        print("   ", r["name"], "|", r["location"])

    return ranked


# -----------------------------------------------
# 🔹 MAIN SEARCH (FIXED)
# -----------------------------------------------
def search(
    query: str,
    location: str = None,
    top_k: int = 5,
    intent: str = None,
) -> List[Dict]:

    if _pipeline is None:
        print("[RAG WARNING] Not initialized")
        return []

    try:
        is_entity = _is_entity_query(query)

        # Query goes to retriever as-is.
        # Orchestrator already shaped it with _build_search_query().
        # NO double-injection of location here.
        final_query = query

        fetch_k = max(top_k * 3, 15)
        raw = _pipeline._retriever.retrieve(final_query, top_k=fetch_k)

        print(f"\n[RAG] QUERY: {final_query}")
        print(f"[RAG] Intent: {intent} | Entity: {is_entity}")
        print(f"[RAG] RAW COUNT: {len(raw)}")

        parsed = [_parse_result(r) for r in raw]
        parsed = [p for p in parsed if _is_valid(p)]

        print(f"[RAG] PARSED COUNT: {len(parsed)}")

        # Category filter (skip for entity queries — they ask about specific things)
        if not is_entity:
            parsed = _filter_by_category(parsed, intent)

        print(f"[RAG] AFTER CATEGORY: {len(parsed)}")

        # Location filter (skip for entity queries — "Where is X" should find X anywhere)
        if is_entity:
            print("[RAG] Entity query → skipping location filter")
            filtered = parsed
        else:
            filtered = _filter_by_location(parsed, location)

        # Rank
        ranked = _rank(filtered, location, intent)

        final = ranked[:top_k]

        print(f"[RAG] FINAL RESULTS: {len(final)}\n")

        return final

    except Exception as e:
        print("[RAG ERROR]", e)
        return []