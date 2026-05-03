"""
Single place to align chat / context fields with the walking graph.

- Mirrors ``location`` and ``source`` (client and older code used both).
- When values look like RAG ``node-*`` ids or known aliases, rewrites to canonical graph ids
  via ``node_mapper`` so RAG, navigation, and context agree.
"""

from __future__ import annotations

from typing import Any

from app.core.graph.node_mapper import resolve_to_graph_node_id
from app.services.navigation_service import resolve_place_label_to_graph_node


def normalize_chat_context(ctx: dict[str, Any]) -> dict[str, Any]:
    """Mutates and returns the same dict for call-site convenience."""
    if not ctx:
        return ctx

    loc = ctx.get("location")
    src = ctx.get("source")
    if isinstance(loc, str) and loc.strip() and (not isinstance(src, str) or not src.strip()):
        ctx["source"] = loc.strip()
    if isinstance(src, str) and src.strip() and (not isinstance(loc, str) or not loc.strip()):
        ctx["location"] = src.strip()

    for key in ("source", "location", "destination"):
        val = ctx.get(key)
        if not isinstance(val, str) or not val.strip():
            continue
        trimmed = val.strip()
        gid, how = resolve_to_graph_node_id(trimmed)
        if gid and how != "unmapped":
            ctx[key] = gid

    # Shop / facility display names (not covered by node_mapper) on source, location, or destination.
    for key in ("source", "location", "destination"):
        val = ctx.get(key)
        if not isinstance(val, str) or not val.strip():
            continue
        pl = resolve_place_label_to_graph_node(val.strip())
        if pl:
            ctx[key] = pl

    if ctx.get("source") and ctx.get("location") and ctx["source"] != ctx["location"]:
        ctx["location"] = ctx["source"]

    return ctx
