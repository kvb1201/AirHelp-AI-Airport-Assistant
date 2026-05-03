"""Load static T2 L02 shop directory from CSV (normalized x,y in 0–100)."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

_SHOPS_CSV = Path(__file__).resolve().parents[1] / "data" / "shops_t2_l02.csv"


@lru_cache(maxsize=1)
def load_shops_t2_l02() -> list[dict[str, object]]:
    if not _SHOPS_CSV.is_file():
        return []
    rows: list[dict[str, object]] = []
    with _SHOPS_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            rid = (raw.get("shop_id") or "").strip()
            if not rid:
                continue
            try:
                xn = float(raw["x_norm"])
                yn = float(raw["y_norm"])
            except (KeyError, ValueError):
                continue
            gid = (raw.get("graph_node_id") or "").strip()
            listing = (raw.get("listing_location") or "").strip()
            hint = (raw.get("near_graph_hint") or "").strip()
            rows.append(
                {
                    "shop_id": rid,
                    "name_display": (raw.get("name_display") or "").strip(),
                    "name_normalized": (raw.get("name_normalized") or raw.get("name_display") or "").strip(),
                    "category": (raw.get("category") or "").strip(),
                    "x_norm": round(xn, 4),
                    "y_norm": round(yn, 4),
                    "floor": (raw.get("floor") or "L02").strip(),
                    "zone": (raw.get("zone") or "").strip(),
                    "source": (raw.get("source") or "csv").strip(),
                    "confidence": (raw.get("confidence") or "unknown").strip(),
                    "graph_node_id": gid,
                    "listing_location": listing,
                    "near_graph_hint": hint or gid or listing,
                }
            )
    return rows
