"""
Normalize noisy, multi-clause user text so routing (navigation, locate, context)
sees the intent — not leading filler like "man", "please", or frustration lines.
"""

from __future__ import annotations

import re
from typing import List

# Phrases that strongly suggest the user wants walking directions (substring match).
_NAV_HINTS = (
    "navigate",
    "take me",
    "directions",
    "walk me",
    "guide me",
    "how do i get",
    "how do i go",
    "how to get",
    "how to go",
    "route to",
    "path to",
    "way to",
    "get me to",
    "bring me to",
    "lead me to",
    "going to",
    "need to go",
    "need to get",
    "want to go",
    "head to",
    "heading to",
    "where is",
    "where's",
    "wheres",
    "point me",
    "which way",
    "help me get",
    "help me find",
    "show me the way",
    "redirect",
    "find my way",
    "lost and",
    "can you get me",
)

# Lines / prefixes that are pure tone, not location (strip from the very beginning).
_LEADING_FILLER = re.compile(
    r"""^(?:
        (?:yo|hey|hi|hello|hiya)\b[,.\s]*|
        (?:man|dude|bro|mate|bhai|listen|look|right|ok+|okay|alright|so)\b[,.\s:!]*|
        (?:please|pls|plz)\b[,.\s]*|
        (?:sorry|uh|um|er)\b[,.\s]*|
        (?:i['’]m|i am)\s+really\s+(?:fed\s+up|frustrated|tired|annoyed|done|over\s+this|sick\s+of\s+this)(?:\s+at\s+this\s+point)?\b[^.!?\n]*[.!?]\s*|
        (?:i['’]m|i am)\s+(?:fed\s+up|so\s+done|frustrated)(?:\s+at\s+this\s+point)?\b[^.!?\n]*[.!?]\s*|
        (?:this\s+is\s+ridiculous|not\s+working|doesn['’]t\s+work)\b[^.!?\n]*[.!?]\s*|
        (?:i['’]m|i am)\s+really\s+fed\s+up\s+at\s+this\s+point\b[,.\s!?]*|
    )+""",
    re.I | re.VERBOSE,
)

# Utterances that are only venting — drop when splitting (optional light cleanup).
_VENT_ONLY = re.compile(
    r"""^(?:
        (?:i['’]m|i am)\s+really\s+fed\s+up\b.*|
        (?:i['’]m|i am)\s+so\s+(?:done|frustrated|tired)\b.*|
        (?:fed\s+up|frustrated|annoyed)\s+at\s+this\s+point\b.*|
        man\s*[.!]?\s*$
    )$""",
    re.I | re.VERBOSE,
)


def _nav_score(text: str) -> int:
    low = (text or "").lower()
    if not low.strip():
        return 0
    score = sum(2 for h in _NAV_HINTS if h in low)
    # Weak hint: "gate 12 to security", brand to brand
    if re.search(r"\b[\w\-]{2,40}\s+to\s+[\w\-]{2,40}\b", low):
        score += 1
    if re.search(r"\bfrom\s+[\w\-]{2,40}\s+to\s+[\w\-]", low):
        score += 2
    return score


def _has_stated_start_segment(text: str) -> bool:
    low = (text or "").lower()
    return bool(
        re.search(
            r"\b(?:i['’]m|i am)\s+(?:at|near|by|outside|inside)\b",
            low,
        )
        or re.search(
            r"\b(?:i['’]m|i am)\s+(?!really\b|so\s+done|not\s+sure|just\b|trying\b|here\b|there\b)([a-z0-9])",
            low,
        )  # "i am lenskart" but not "i am really fed up"
        or re.search(r"\b(?:near|at)\s+(?:the\s+)?(?:gate|terminal|t\d|pier)\b", low)
        or re.search(r"\bcurrently\s+(?:at|near)\b", low)
    )


def _split_utterances(text: str) -> List[str]:
    """Split on sentence boundaries without breaking decimals like 3.14."""
    t = (text or "").strip()
    if not t:
        return []
    parts = re.split(r"(?<!\d)(?:[.!?]+|\n+)(?!\d)\s*", t)
    out: List[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if _VENT_ONLY.match(p) and len(p) < 120:
            continue
        out.append(p)
    return out if out else [t]


def strip_leading_filler(raw: str) -> str:
    """Remove conversational / frustration prefixes from the start of the message."""
    t = (raw or "").strip()
    if not t:
        return t
    prev = None
    while prev != t:
        prev = t
        t = _LEADING_FILLER.sub("", t).lstrip()
    return t


def compose_navigation_message(raw: str) -> str:
    """
    Build one string for navigation parsing when the user writes several sentences.

    If a later sentence has "take me to …" and an earlier one says "I am at …",
    join those segments so start + goal extraction both work.
    """
    t = strip_leading_filler(raw)
    parts = _split_utterances(t)
    if len(parts) <= 1:
        return parts[0] if parts else t

    scores = [_nav_score(p) for p in parts]
    j = max(range(len(parts)), key=lambda i: (scores[i], i))
    if scores[j] <= 0:
        # No clear nav sentence: keep full text so regexes can still see "i am … take me …"
        return " ".join(parts)

    prior = parts[:j]
    if any(_has_stated_start_segment(p) for p in prior):
        return " ".join(parts[: j + 1])
    return parts[j]


def prepare_for_locate_and_context(raw: str) -> str:
    """Light cleanup for locating_engine + context_engine (single pass, no sentence picking)."""
    return strip_leading_filler((raw or "").strip())
