from typing import Dict, Optional

from app.services.context_signal_engine import extract_signals
from app.services.locating_engine import SERVICE_LABELS


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
# 🔥 NEW: Intent Reset Logic
# -------------------------------
def _should_reset_intent(message: str) -> bool:
    msg = message.lower().strip()

    # greetings / irrelevant inputs
    return msg in [
        "hi", "hello", "hey",
        "ok", "okay",
        "thanks", "thank you",
    ]


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

    # Intent
    if new.get("intent"):
        if ctx.get("intent") and ctx["intent"] != new["intent"]:
            ctx["destination"] = None  # reset conflicting navigation

        ctx["intent"] = new["intent"]

    # Client / API uses ``location``; decision layer uses ``source`` — keep them aligned.
    if isinstance(ctx.get("location"), str) and ctx["location"].strip():
        if not (isinstance(ctx.get("source"), str) and ctx["source"].strip()):
            ctx["source"] = ctx["location"].strip()
    if isinstance(ctx.get("source"), str) and ctx["source"].strip():
        if not (isinstance(ctx.get("location"), str) and ctx["location"].strip()):
            ctx["location"] = ctx["source"].strip()

    return ctx


# -------------------------------
# 🔹 Consistency Layer
# -------------------------------
def _apply_consistency(ctx: Dict) -> Dict:

    # ❌ invalid sources
    if ctx.get("source") in ["wifi", "atm", "lounge", "shop"]:
        ctx["source"] = None

    dest = ctx.get("destination")
    if isinstance(dest, str) and dest.strip().lower() in SERVICE_LABELS:
        ctx["destination"] = None

    return ctx


# -------------------------------
# 🔹 Signal Layer
# -------------------------------
def _apply_signal_extraction(ctx: Dict, message: str) -> Dict:

    signals = extract_signals(message)

    signal_intent = signals.get("intent")

    # 🔥 Intent logic
    if signal_intent:
        if not ctx.get("intent"):
            ctx["intent"] = signal_intent
        elif ctx.get("behavior") == "relaxed" and signal_intent == "lounge":
            ctx["intent"] = "lounge"

    # Behavior always updates
    ctx["behavior"] = signals.get("behavior")

    return ctx


# -------------------------------
# 🔹 Decision Layer
# -------------------------------
def _decision(ctx: Dict, prev_ctx: Dict) -> Dict:

    source = ctx.get("source")
    destination = ctx.get("destination")
    intent = ctx.get("intent")

    # -------------------------------
    # 🔥 HARD RULE: Need source
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

    # -------------------------------
    # Navigation
    # -------------------------------
    if destination:
        return {
            "context": ctx,
            "ready": True,
            "needs_clarification": False,
            "clarification_message": None,
            "fallback": False,
        }

    # -------------------------------
    # Recommendation / intent present
    # -------------------------------
    if intent:
        return {
            "context": ctx,
            "ready": True,
            "needs_clarification": False,
            "clarification_message": None,
            "fallback": False,
        }

    # -------------------------------
    # Missing intent
    # -------------------------------
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

    # -------------------------------
    # STEP 0: 🔥 RESET (NEW FIX)
    # -------------------------------
    if _should_reset_intent(message):
        prev_context["intent"] = None
        prev_context["behavior"] = None

    # -------------------------------
    # STEP 1: Merge
    # -------------------------------
    ctx = _merge_context(prev_context, locating_output)

    # -------------------------------
    # STEP 2: Consistency
    # -------------------------------
    ctx = _apply_consistency(ctx)

    # -------------------------------
    # STEP 3: Signals
    # -------------------------------
    ctx = _apply_signal_extraction(ctx, message)

    # -------------------------------
    # STEP 4: Decision
    # -------------------------------
    decision = _decision(ctx, prev_context)

    return decision