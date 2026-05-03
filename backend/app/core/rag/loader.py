"""
loader.py
---------
Loads airport knowledge-base data from a JSON file and flattens every
nested section into plain-text document strings that the RAG pipeline
can later chunk, embed, and index.

Supported JSON top-level keys
------------------------------
gates, terminals, food_courts, shops, offers, services,
facilities, check_in_counters, baggage_belts
"""

from __future__ import annotations

import json
import os
from typing import Any


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _stringify_dict(d: dict[str, Any], *, indent: int = 0) -> str:
    """Recursively convert a dict to a human-readable multiline string."""
    lines: list[str] = []
    prefix = "  " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_stringify_dict(value, indent=indent + 1))
        elif isinstance(value, list):
            items = ", ".join(str(v) for v in value)
            lines.append(f"{prefix}{key}: {items}")
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)


def _extract_id(item: dict[str, Any], category: str, index: int) -> str:
    """Return a stable document ID from common name fields or a fallback."""
    for field in ("id", "gate", "name", "code"):
        if field in item:
            return str(item[field])
    return f"{category}_{index}"


# ---------------------------------------------------------------------------
# Section-specific flatteners
# ---------------------------------------------------------------------------

def _flatten_gates(gates: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, gate in enumerate(gates):
        text = (
            f"Gate {gate.get('gate', 'N/A')}: "
            f"Located in Terminal {gate.get('terminal', 'N/A')}. "
            f"{gate.get('description', '')} "
            f"Walking time from security: {gate.get('walking_time_from_security', 'N/A')}. "
            f"Facilities nearby: {', '.join(gate.get('nearby_facilities', []))}."
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "gate",
                "location": gate.get("terminal", "unknown"),
                "id": _extract_id(gate, "gate", i),
            },
        })
    return docs


def _flatten_terminals(terminals: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, terminal in enumerate(terminals):
        text = (
            f"Terminal {terminal.get('name', 'N/A')}: "
            f"{terminal.get('description', '')} "
            f"Facilities: {', '.join(terminal.get('facilities', []))}. "
            f"Access: {terminal.get('access', '')}."
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "terminal",
                "location": terminal.get("name", "unknown"),
                "id": _extract_id(terminal, "terminal", i),
            },
        })
    return docs


def _flatten_food_courts(food_courts: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, outlet in enumerate(food_courts):
        text = (
            f"Food Outlet '{outlet.get('name', 'N/A')}': "
            f"Cuisine: {outlet.get('cuisine', 'N/A')}. "
            f"Location: {outlet.get('location', 'N/A')}. "
            f"Timings: {outlet.get('timings', 'N/A')}. "
            f"Price range: {outlet.get('price_range', 'N/A')}. "
            f"{outlet.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "food_court",
                "location": outlet.get("location", "unknown"),
                "id": _extract_id(outlet, "food_court", i),
            },
        })
    return docs


def _flatten_shops(shops: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, shop in enumerate(shops):
        offers_text = ""
        if shop.get("current_offers"):
            offers_text = f"Current offers: {'; '.join(shop['current_offers'])}. "
        skus = ", ".join(shop.get("sku_categories", []))
        text = (
            f"Shop '{shop.get('name', 'N/A')}': "
            f"Located at {shop.get('location', 'N/A')}. "
            f"Available categories: {skus}. "
            f"{offers_text}"
            f"{shop.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "shop",
                "location": shop.get("location", "unknown"),
                "id": _extract_id(shop, "shop", i),
            },
        })
    return docs


def _flatten_services(services: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, service in enumerate(services):
        text = (
            f"Service '{service.get('name', 'N/A')}' ({service.get('type', 'N/A')}): "
            f"Location: {service.get('location', 'N/A')}. "
            f"{service.get('description', '')} "
            f"Hours: {service.get('hours', 'N/A')}."
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "service",
                "location": service.get("location", "unknown"),
                "id": _extract_id(service, "service", i),
            },
        })
    return docs


def _flatten_facilities(facilities: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, facility in enumerate(facilities):
        text = (
            f"Facility '{facility.get('name', 'N/A')}': "
            f"Type: {facility.get('type', 'N/A')}. "
            f"Location: {facility.get('location', 'N/A')}. "
            f"{facility.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "facility",
                "location": facility.get("location", "unknown"),
                "id": _extract_id(facility, "facility", i),
            },
        })
    return docs


def _flatten_check_in_counters(counters: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, counter in enumerate(counters):
        airlines = ", ".join(counter.get("airlines", []))
        text = (
            f"Check-in Counter '{counter.get('name', 'N/A')}': "
            f"Terminal: {counter.get('terminal', 'N/A')}. "
            f"Airlines served: {airlines}. "
            f"Counter range: {counter.get('counter_range', 'N/A')}. "
            f"{counter.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "check_in_counter",
                "location": counter.get("terminal", "unknown"),
                "id": _extract_id(counter, "check_in_counter", i),
            },
        })
    return docs


def _flatten_baggage_belts(belts: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, belt in enumerate(belts):
        flights = ", ".join(belt.get("flights", []))
        text = (
            f"Baggage Belt {belt.get('belt_number', 'N/A')}: "
            f"Terminal: {belt.get('terminal', 'N/A')}. "
            f"Assigned flights: {flights}. "
            f"Location: {belt.get('location', 'N/A')}. "
            f"{belt.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "baggage_belt",
                "location": belt.get("terminal", "unknown"),
                "id": _extract_id(belt, "baggage_belt", i),
            },
        })
    return docs


def _flatten_generic(items: list[dict], category: str) -> list[dict[str, Any]]:
    """Generic fallback flattener for unrecognised top-level keys."""
    docs: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        text = f"{category.replace('_', ' ').title()}: {_stringify_dict(item)}"
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": category,
                "location": item.get("location", item.get("terminal", "unknown")),
                "id": _extract_id(item, category, i),
            },
        })
    return docs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_SECTION_HANDLERS: dict[str, Any] = {
    "gates": _flatten_gates,
    "terminals": _flatten_terminals,
    "food_courts": _flatten_food_courts,
    "shops": _flatten_shops,
    "services": _flatten_services,
    "facilities": _flatten_facilities,
    "check_in_counters": _flatten_check_in_counters,
    "baggage_belts": _flatten_baggage_belts,
}


def load_airport_data(json_path: str) -> list[dict[str, Any]]:
    """Load airport knowledge-base JSON and return a flat list of documents.

    Parameters
    ----------
    json_path : str
        Absolute or relative path to the airport JSON data file.

    Returns
    -------
    list[dict]
        Each element is ``{"text": str, "metadata": {"category": str,
        "location": str, "id": str}}``.

    Raises
    ------
    FileNotFoundError
        If *json_path* does not exist on disk.
    ValueError
        If the file is not valid JSON or the root element is not a dict.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Airport data file not found: '{json_path}'. "
            "Please verify the path and try again."
        )

    with open(json_path, "r", encoding="utf-8") as fh:
        try:
            data: dict[str, Any] = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in '{json_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected the root of '{json_path}' to be a JSON object (dict), "
            f"got {type(data).__name__}."
        )

    documents: list[dict[str, Any]] = []
    for section_key, section_value in data.items():
        if not isinstance(section_value, list):
            continue  # skip non-list top-level values silently
        handler = _SECTION_HANDLERS.get(section_key, None)
        if handler is not None:
            documents.extend(handler(section_value))
        else:
            documents.extend(_flatten_generic(section_value, section_key))

    return documents
