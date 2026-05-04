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
        gate_num = gate.get("gate_number") or gate.get("gate", "N/A")
        terminal = gate.get("terminal", "N/A")
        nearby = gate.get("nearby_facilities", [])
        nearby_str = ", ".join(str(n) for n in nearby) if nearby else "N/A"

        # Extract walking time from navigation dict if present
        nav = gate.get("navigation", {})
        walk_time = "N/A"
        for nav_key, nav_val in nav.items():
            if "security" in nav_key and isinstance(nav_val, dict):
                walk_time = f"{nav_val.get('walking_time_minutes', 'N/A')} min"
                break

        text = (
            f"Gate {gate_num}: "
            f"Located in Terminal {terminal}. "
            f"{gate.get('description', '')} "
            f"Walking time from security: {walk_time}. "
            f"Facilities nearby: {nearby_str}."
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "gate",
                "location": terminal,
                "name": f"Gate {gate_num}",
                "id": gate.get("gate_id") or _extract_id(gate, "gate", i),
            },
        })
    return docs


def _flatten_terminals(terminals: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, terminal in enumerate(terminals):
        name = terminal.get("name", "N/A")
        # Handle both old 'facilities' (list of str) and new 'facilities_summary'
        facs = terminal.get("facilities") or terminal.get("facilities_summary", [])
        facs_str = ", ".join(str(f) for f in facs) if facs else "N/A"

        text = (
            f"Terminal {name}: "
            f"{terminal.get('description', '')} "
            f"Facilities: {facs_str}. "
            f"Access: {terminal.get('access', '')}."
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "terminal",
                "location": name,
                "name": name,
                "id": terminal.get("terminal_id") or _extract_id(terminal, "terminal", i),
            },
        })
    return docs


def _flatten_food_courts(food_courts: list[dict]) -> list[dict[str, Any]]:
    """Handles both old 'food_courts' and new 'food_outlets' schema."""
    docs: list[dict[str, Any]] = []
    for i, outlet in enumerate(food_courts):
        name = outlet.get("name", "N/A")
        # location: old='location', new='location_description'
        location = outlet.get("location") or outlet.get("location_description", "N/A")
        # cuisine: old=string, new=list of strings
        cuisine = outlet.get("cuisine", "N/A")
        if isinstance(cuisine, list):
            cuisine = ", ".join(cuisine)
        # timings: old=string, new=dict{open, close}
        timings = outlet.get("timings", "N/A")
        if isinstance(timings, dict):
            if timings.get("open_24h"):
                timings = "Open 24 hours"
            else:
                timings = f"{timings.get('open', '?')} – {timings.get('close', '?')}"

        term = (outlet.get("terminal") or "").strip() or "T2"
        # RAG terminal filters / ranking look for "t2" or "terminal 2" inside ``location``.
        meta_location = f"{term} — {location}" if location else term

        text = (
            f"Food Outlet '{name}': "
            f"Terminal: {term}. "
            f"Cuisine: {cuisine}. "
            f"Location: {location}. "
            f"Timings: {timings}. "
            f"Price range: {outlet.get('price_range', 'N/A')}. "
            f"{outlet.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "food_court",
                "location": meta_location,
                "name": name,
                "id": outlet.get("outlet_id") or _extract_id(outlet, "food_court", i),
                "terminal": term,
            },
        })
    return docs


def _flatten_shops(shops: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, shop in enumerate(shops):
        name = shop.get("name", "N/A")
        location = shop.get("location") or shop.get("location_description", "N/A")

        # current_offers: old=list of strings, new=list of dicts
        offers_text = ""
        offers = shop.get("current_offers", [])
        if offers:
            offer_titles = []
            for o in offers:
                if isinstance(o, dict):
                    offer_titles.append(o.get("title", str(o)))
                else:
                    offer_titles.append(str(o))
            offers_text = f"Current offers: {'; '.join(offer_titles)}. "

        # sku_categories (old) or sub_category (new)
        skus = shop.get("sku_categories") or shop.get("sub_category", [])
        skus_str = ", ".join(str(s) for s in skus) if skus else "N/A"

        text = (
            f"Shop '{name}': "
            f"Located at {location}. "
            f"Available categories: {skus_str}. "
            f"{offers_text}"
            f"{shop.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "shop",
                "location": location,
                "name": name,
                "id": shop.get("shop_id") or _extract_id(shop, "shop", i),
            },
        })
    return docs


def _flatten_services(services: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, service in enumerate(services):
        name = service.get("name", "N/A")
        location = service.get("location") or service.get("location_description", "N/A")

        # hours: old=string, new=timings dict
        hours = service.get("hours", "N/A")
        timings = service.get("timings")
        if isinstance(timings, dict):
            if timings.get("open_24h"):
                hours = "Open 24 hours"
            else:
                hours = f"{timings.get('open', '?')} – {timings.get('close', '?')}"

        text = (
            f"Service '{name}' ({service.get('type', 'N/A')}): "
            f"Location: {location}. "
            f"{service.get('description', '')} "
            f"Hours: {hours}."
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "service",
                "location": location,
                "name": name,
                "id": service.get("service_id") or _extract_id(service, "service", i),
            },
        })
    return docs


def _flatten_facilities(facilities: list[dict]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for i, facility in enumerate(facilities):
        name = facility.get("name", "N/A")
        location = facility.get("location") or facility.get("location_description", "N/A")

        text = (
            f"Facility '{name}': "
            f"Type: {facility.get('type', 'N/A')}. "
            f"Location: {location}. "
            f"{facility.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "facility",
                "location": location,
                "name": name,
                "id": facility.get("facility_id") or _extract_id(facility, "facility", i),
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
        flights = ", ".join(str(f) for f in belt.get("flights", []))
        location = belt.get("location") or belt.get("location_description", "N/A")
        text = (
            f"Baggage Belt {belt.get('belt_number', 'N/A')}: "
            f"Terminal: {belt.get('terminal', 'N/A')}. "
            f"Assigned flights: {flights}. "
            f"Location: {location}. "
            f"{belt.get('description', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "baggage_belt",
                "location": belt.get("terminal", "unknown"),
                "name": belt.get("belt_number", f"Belt {i+1}"),
                "id": belt.get("belt_id") or _extract_id(belt, "baggage_belt", i),
            },
        })
    return docs


def _flatten_flights(flights: list[dict]) -> list[dict[str, Any]]:
    """Flatten flight data into searchable documents."""
    docs: list[dict[str, Any]] = []
    for i, flight in enumerate(flights):
        gate = flight.get("gate_number", "N/A")
        terminal = flight.get("terminal", "N/A")
        text = (
            f"Flight {flight.get('flight_number', 'N/A')} "
            f"({flight.get('airline', 'N/A')}): "
            f"{flight.get('origin', '?')} → {flight.get('destination_city', flight.get('destination', '?'))}. "
            f"Terminal: {terminal}, Gate: {gate}. "
            f"Departure: {flight.get('departure_time', 'N/A')}. "
            f"Status: {flight.get('status', 'N/A')}. "
            f"Check-in counters: {flight.get('check_in_counter_range', 'N/A')}. "
            f"{flight.get('notes', '')}"
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": "flight",
                "location": terminal,
                "name": flight.get("flight_number", f"flight_{i}"),
                "id": flight.get("flight_id") or _extract_id(flight, "flight", i),
            },
        })
    return docs


def _flatten_generic(items: list[dict], category: str) -> list[dict[str, Any]]:
    """Generic fallback flattener for unrecognised top-level keys."""
    docs: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        text = f"{category.replace('_', ' ').title()}: {_stringify_dict(item)}"
        location = (
            item.get("location")
            or item.get("location_description")
            or item.get("terminal", "unknown")
        )
        docs.append({
            "text": text.strip(),
            "metadata": {
                "category": category,
                "location": location,
                "name": item.get("name") or item.get("label", ""),
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
    "food_outlets": _flatten_food_courts,   # new key, same handler
    "shops": _flatten_shops,
    "services": _flatten_services,
    "facilities": _flatten_facilities,
    "check_in_counters": _flatten_check_in_counters,
    "baggage_belts": _flatten_baggage_belts,
    "flights": _flatten_flights,
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

    # CSV T2 shops: hard-coded persona / age / cuisine text for richer embeddings (see shop_audience_rag_docs).
    from app.services.shop_audience_rag_docs import merge_shop_audience_documents

    documents = merge_shop_audience_documents(documents)

    return documents
