# backend/app/services/rag_service.py

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

# 🔕 Disable Chroma telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "false"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"

from app.core.rag.pipeline import AirportRAGPipeline

_pipeline = None


# -----------------------------------------------
# 🔹 Resolve absolute data path
# -----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "core" / "rag" / "airport_data.json"


# -----------------------------------------------
# 🔹 Category allow-lists
# -----------------------------------------------
_CATEGORY_MAP: Dict[str, set] = {
    "recommendation": {
        "food_court", "restaurant", "cafe",
        "quick_bites", "coffee_shop"
    },
    "explore": {
        "food_court", "restaurant", "cafe",
        "quick_bites", "coffee_shop",
        "shop", "service", "facility"
    },
}

_NON_ACTIONABLE = {
    "terminal",
    "gate",
    "check_in_counter",
    "baggage_belt",
    "navigation_nodes",
}

_TERMINAL_ALIASES = {
    "1": ["terminal 1", "terminal1", "t1"],
    "2": ["terminal 2", "terminal2", "t2"],
    "3": ["terminal 3", "terminal3", "t3"],
}


# -----------------------------------------------
# 🔥 Intent normalization (CRITICAL FIX)
# -----------------------------------------------
def _normalize_intent_for_rag(intent: str) -> Optional[str]:
    if not intent:
        return None

    intent = intent.lower()

    if intent in [
        "food", "coffee", "restaurant", "eat",
        "lounge", "atm", "wifi", "shop"
    ]:
        return "recommendation"

    if intent == "explore":
        return "explore"

    return intent


# -----------------------------------------------
# 🔥 Actionable Check
# -----------------------------------------------
def _is_actionable(item: Dict) -> bool:
    cat = item.get("category")

    if not cat:
        return False

    if cat in _NON_ACTIONABLE:
        return False

    return True


# -----------------------------------------------
# 🔥 Deduplication
# -----------------------------------------------
def _deduplicate(results: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []

    for r in results:
        name = (r.get("name") or "").lower().strip()

        if name and name not in seen:
            seen.add(name)
            unique.append(r)

    return unique


# -------------------------------
# 🔹 Initialize
# -------------------------------
def init_rag():
    global _pipeline

    if _pipeline is None:
        print("🔄 Initializing RAG pipeline...")
        print(f"[RAG] Loading data from: {DATA_PATH}")

        if not DATA_PATH.exists():
            raise FileNotFoundError(f"RAG data file not found at: {DATA_PATH}")

        _pipeline = AirportRAGPipeline(
            json_path=str(DATA_PATH)
        )

        _pipeline.load_and_index()

        print("✅ RAG pipeline ready")


# -----------------------------------------------
# 🔹 Entity Query Detection
# -----------------------------------------------
def _is_entity_query(query: str) -> bool:
    q = query.lower()

    return any([
        "where is" in q,
        "locate " in q,
        "find " in q and "near" not in q,
    ])


# -----------------------------------------------
# 🔹 Terminal Extraction
# -----------------------------------------------
def _extract_terminal_number(location: str) -> Optional[str]:
    if not location:
        return None

    loc = location.lower().strip()

    m = re.search(r"terminal[_\s]*([1-3])", loc)
    if m:
        return m.group(1)

    m = re.match(r"^t([1-3])(?:[_\s]|$)", loc)
    if m:
        return m.group(1)

    return None


def _item_matches_terminal(item_location: str, terminal_num: str) -> bool:
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

        if not name:
            m = re.search(r"'([^']+)'", text)
            if m:
                name = m.group(1)

        return {
            "id": meta.get("id") or "",
            "name": name or "Unknown",
            "category": category,
            "location": meta.get("location", ""),
            "terminal": meta.get("terminal", ""),
            "description": text,
            "score": r.get("score", 0),
        }

    return {
        "id": "",
        "name": str(r),
        "category": "",
        "location": "",
        "terminal": "",
        "description": "",
        "score": 0,
    }


# -------------------------------
# 🔹 Validate
# -------------------------------
def _is_valid(x: Dict[str, Any]) -> bool:
    return x and x.get("name") not in ["", "Unknown", None]


# -------------------------------
# 🔥 Category Filter (FINAL FIX)
# -------------------------------
def _filter_by_category(results: List[Dict], intent: Optional[str]):

    intent = _normalize_intent_for_rag(intent)
    allowed = _CATEGORY_MAP.get(intent)

    if allowed:
        filtered = [r for r in results if r.get("category") in allowed]

        print(f"[RAG] Category Filter → {len(filtered)} / {len(results)}")

        # 🔥 REMOVE facilities for recommendation (food)
        if intent == "recommendation":
            filtered = [r for r in filtered if r.get("category") != "facility"]

        if filtered:
            return filtered

    return [r for r in results if _is_actionable(r)]


# -----------------------------------------------
# 🔹 Location Filter
# -----------------------------------------------
def _filter_by_location(results: List[Dict], location: Optional[str]) -> List[Dict]:
    if not location:
        return results

    terminal_num = _extract_terminal_number(location)

    if not terminal_num:
        return results

    filtered = [
        r for r in results
        if _item_matches_terminal(r.get("location", ""), terminal_num)
    ]

    print(f"[RAG] Location Filter → {len(filtered)} / {len(results)}")

    return filtered if filtered else results


# -----------------------------------------------
# 🔥 Ranking
# -----------------------------------------------
def _rank(results, location, intent, signals=None):

    terminal_num = _extract_terminal_number(location)
    intent = _normalize_intent_for_rag(intent)
    allowed = _CATEGORY_MAP.get(intent, set())

    behavior = (signals or {}).get("behavior")

    def score(x):
        if x.get("category") in _NON_ACTIONABLE:
            return -9999

        sem = float(x.get("score", 0))
        desc = (x.get("description") or "").lower()
        item_loc = x.get("location", "")

        loc_bonus = 0.5 if terminal_num and _item_matches_terminal(item_loc, terminal_num) else 0
        cat_bonus = 0.2 if x.get("category") in allowed else 0

        behavior_bonus = 0

        if behavior == "quick":
            if any(k in desc for k in ["fast", "quick", "grab", "takeaway", "snack", "express", "kiosk"]):
                behavior_bonus += 0.6

        elif behavior == "relaxed":
            if any(k in desc for k in ["lounge", "premium", "relax"]):
                behavior_bonus += 0.6

        return sem + loc_bonus + cat_bonus + behavior_bonus

    ranked = sorted(results, key=score, reverse=True)

    print("[RAG] Top Ranked (clean):")
    for r in ranked[:5]:
        print("   ", r["name"], "|", r["category"])

    return ranked


# -----------------------------------------------
# 🔹 MAIN SEARCH
# -----------------------------------------------
def search(query, location=None, top_k=5, intent=None, signals=None):

    global _pipeline

    if _pipeline is None:
        print("[RAG] Auto-initializing...")
        init_rag()

    try:
        raw = _pipeline._retriever.retrieve(query, top_k=max(top_k * 3, 15))

        parsed = [_parse_result(r) for r in raw]
        parsed = [p for p in parsed if _is_valid(p)]

        parsed = _filter_by_category(parsed, intent)
        filtered = _filter_by_location(parsed, location)

        ranked = _rank(filtered, location, intent, signals)

        ranked = [r for r in ranked if _is_actionable(r)]
        ranked = _deduplicate(ranked)

        return ranked[:top_k]

    except Exception as e:
        print("[RAG ERROR]", e)
        return []