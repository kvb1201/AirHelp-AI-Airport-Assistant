# backend/app/services/location_decision_engine.py

from typing import Dict, Any, List


# -------------------------------
# 🔹 Helper
# -------------------------------
def _format_options(results: List[Dict]) -> str:
    names = [r.get("name", "Unknown") for r in results[:3]]
    return ", ".join(names)


# -------------------------------
# 🔹 MAIN DECISION FUNCTION
# -------------------------------
def decide_location_output(
    query: str,
    layer1_output: Dict[str, Any],
    semantic_output: List[Dict[str, Any]],
    mapping_output: Dict[str, Any],
) -> Dict[str, Any]:

    source_candidates = layer1_output.get("source_candidates", [])
    confidence = layer1_output.get("confidence", 0)

    results = mapping_output.get("results", [])
    source = mapping_output.get("final_source")

    # -------------------------------
    # CASE 1: Strong match
    # -------------------------------
    if source and results:
        return {
            "final_source": source,
            "results": results,
            "needs_clarification": False,
            "clarification_message": None,
            "confidence": confidence,
        }

    # -------------------------------
    # CASE 2: No source (ask once)
    # -------------------------------
    if not source and results:
        return {
            "final_source": None,
            "results": results,
            "needs_clarification": True,
            "clarification_message": "Which terminal are you at? (Terminal 1, 2, or 3)",
            "confidence": confidence,
        }

    # -------------------------------
    # CASE 3: Multiple ambiguous results
    # -------------------------------
    if len(results) > 1:
        options = _format_options(results)

        return {
            "final_source": source,
            "results": results[:3],
            "needs_clarification": False,
            "clarification_message": f"I found multiple options: {options}",
            "confidence": confidence,
        }

    # -------------------------------
    # CASE 4: No results
    # -------------------------------
    return {
        "final_source": None,
        "results": [],
        "needs_clarification": True,
        "clarification_message": "I couldn't find that. Are you looking for food, lounge, ATM, or something else?",
        "confidence": 0.0,
    }