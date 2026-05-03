# backend/app/services/context_engine.py

from typing import Dict, Optional
from app.services.context_signal_engine import extract_signals


# -------------------------------
# 🔹 Context Schema
# -------------------------------
def _default_context():
    return {
        "source": None,
        "destination": None,
        "intent": None,
        "behavior": None,
        "preference": None,
        "user_type": None,
        "missing": None,
    }


# -------------------------------
# 🔹 Merge Layer
# -------------------------------
def _merge_context(old: Dict, new: Dict) -> Dict:
    ctx = old.copy()

    # Source
    if new.get("source"):
        ctx["source"] = new["source"]

    # Destination
    if new.get("destination"):
        ctx["destination"] = new["destination"]

    # Intent from locating engine
    if new.get("intent"):
        if ctx.get("intent") and ctx["intent"] != new["intent"]:
            ctx["destination"] = None  # reset conflicting navigation

        ctx["intent"] = new["intent"]

    return ctx


# -------------------------------
# 🔹 Consistency Layer
# -------------------------------
def _apply_consistency(ctx: Dict) -> Dict:

    # Remove invalid source types
    if ctx.get("source") in ["wifi", "atm", "lounge", "shop"]:
        ctx["source"] = None

    return ctx


# -------------------------------
# 🔹 Signal Layer (FINAL FIXED)
# -------------------------------
def _apply_signal_extraction(ctx: Dict, message: str) -> Dict:

    signals = extract_signals(message)

    signal_intent = signals.get("intent")
    signal_behavior = signals.get("behavior")

    # -------------------------------
    # 🔥 Behavior FIRST (critical)
    # -------------------------------
    if signal_behavior:
        ctx["behavior"] = signal_behavior

    # -------------------------------
    # 🔥 Intent logic (improved)
    # -------------------------------
    if signal_intent:

        # Case 1: no intent yet
        if not ctx.get("intent"):
            ctx["intent"] = signal_intent

        # Case 2: override using behavior
        elif ctx.get("behavior") == "relaxed" and signal_intent == "lounge":
            ctx["intent"] = "lounge"

        elif ctx.get("behavior") == "quick" and signal_intent == "food":
            ctx["intent"] = "food"

    return ctx


# -------------------------------
# 🔹 Decision Layer
# -------------------------------
def _decision(ctx: Dict, prev_ctx: Dict) -> Dict:

    source = ctx.get("source")
    destination = ctx.get("destination")
    intent = ctx.get("intent")

    # -------------------------------
    # 🔥 HARD RULE: source required
    # -------------------------------
    if not source:

        prev_missing = prev_ctx.get("missing") if prev_ctx else None

        if prev_missing == "source":
            return {
                "context": ctx,
                "ready": False,
                "needs_clarification": False,
                "clarification_message": None,
                "fallback": True,
            }

        return {
            "context": ctx,
            "ready": False,
            "needs_clarification": True,
            "clarification_message": "Where are you currently? For example: Terminal 1, Gate A1.",
            "fallback": False,
        }

    # Navigation case
    if destination:
        return {
            "context": ctx,
            "ready": True,
            "needs_clarification": False,
            "clarification_message": None,
            "fallback": False,
        }

    # Recommendation case
    if intent:
        return {
            "context": ctx,
            "ready": True,
            "needs_clarification": False,
            "clarification_message": None,
            "fallback": False,
        }

    # Missing intent
    return {
        "context": ctx,
        "ready": False,
        "needs_clarification": True,
        "clarification_message": "What are you looking for? Food, lounge, shops?",
        "fallback": False,
    }


# -------------------------------
# 🔹 MAIN CONTEXT ENGINE
# -------------------------------
def update_context(
    prev_context: Optional[Dict],
    locating_output: Dict,
    message: str
) -> Dict:

    if not prev_context:
        prev_context = _default_context()

    # Step 1: Merge
    ctx = _merge_context(prev_context, locating_output)

    # Step 2: Consistency
    ctx = _apply_consistency(ctx)

    # Step 3: Signals
    ctx = _apply_signal_extraction(ctx, message)

    # Step 4: Decision
    decision = _decision(ctx, prev_context)

    return decision