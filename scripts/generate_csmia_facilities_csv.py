#!/usr/bin/env python3
"""
Build backend/app/data/facilities_bom.csv from CSMIA airport facilities.

1) POST /api/sitecore/AirportServices/Search (same as Services-Search.js) for any extra cards.
2) GET the facilities page HTML and parse:
   - `.service-card` grid (main facilities)
   - `.swiper-slide.imageCardContent` under "Other Facilities" (Pranaam-related)

Static rows ensure every item from the live page is present even if the API/network fails.
Directory: https://csmia-mumbai.adaniairports.com/en/airport-facilities
"""

from __future__ import annotations

import csv
import hashlib
import html as html_module
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "backend" / "app" / "data" / "mumbai_t2_level02_graph.json"
OUT_CSV = ROOT / "backend" / "app" / "data" / "facilities_bom.csv"

SITE = "https://csmia-mumbai.adaniairports.com"
FACILITIES_PAGE = f"{SITE}/en/airport-facilities"
SEARCH_URL = f"{SITE}/api/sitecore/AirportServices/Search"
DATA_SOURCE = "{1985F592-B182-4004-9F05-5369E01D851A}"

# Every main + other facility name from the official page (no omissions).
STATIC_MAIN: list[tuple[str, str]] = [
    ("Information Desk", "/en/airport-facilities/information-desk"),
    ("Lost and Found", "/en/airport-facilities/lost-and-found-services"),
    ("Transportation", "/en/airport-facilities/transport"),
    ("Wi-Fi", "/en/airport-facilities/wifi-service"),
    ("Special Assistance", "/en/airport-facilities/special-assistance"),
    ("Digi Yatra", "/en/airport-facilities/digiyatra"),
    ("Self-Baggage Drop", "/en/airport-facilities/self-baggage-drop"),
    ("Baby Care Room", "/en/airport-facilities/baby-care-room"),
    ("Inter Terminal Coach", "/en/airport-facilities/inter-terminal-coach-facility"),
    ("Buggy", "/en/airport-facilities/automated-buggy-service"),
    ("Baggage Trolley", "/en/airport-facilities/baggage-trolleys"),
    ("Prayer Room", "/en/airport-facilities/prayer-room"),
    ("Smoking Room", "/en/airport-facilities/smoking-zones"),
]
STATIC_OTHER: list[str] = [
    "Charging Stations",
    "Help Phones",
    "Slumber Chairs",
    "ATMs",
    "Entertainment Screens",
]

# Map facility display name → walking-graph node (T2 L02 schematic; BOM-wide services).
NAME_TO_NODE: dict[str, str] = {
    "information desk": "t2_information",
    "lost and found": "t2_lost_found",
    "transportation": "t2_entrance",
    "wi-fi": "t2_hub_02_02",
    "wifi": "t2_hub_02_02",
    "special assistance": "t2_medical",
    "digi yatra": "t2_security_merge",
    "self-baggage drop": "t2_circ_south_1",
    "baby care room": "t2_medical",
    "inter terminal coach": "t2_entrance",
    "buggy": "t2_post_security",
    "baggage trolley": "t2_baggage_claim",
    "prayer room": "t2_hub_04_03",
    "smoking room": "t2_post_security",
    "charging stations": "t2_hub_02_02",
    "help phones": "t2_information",
    "slumber chairs": "t2_baggage_claim",
    "atms": "t2_forex",
    "entertainment screens": "t2_hub_03_01",
}


def load_node_xy() -> dict[str, tuple[float, float]]:
    raw = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    out: dict[str, tuple[float, float]] = {}
    for nid, meta in raw["nodes"].items():
        out[nid] = (float(meta["x"]), float(meta["y"]))
    return out


def graph_node_for(name: str) -> str:
    k = html_module.unescape(name).lower().strip()
    k = k.replace("’", "'")
    return NAME_TO_NODE.get(k, "t2_information")


def jitter_xy(bx: float, by: float, seed: str) -> tuple[float, float]:
    h = int(hashlib.md5(seed.encode("utf-8")).hexdigest()[:8], 16)
    dx = ((h % 241) - 120) / 72.0
    dy = (((h // 241) % 241) - 120) / 72.0
    return round(bx + dx, 4), round(by + dy, 4)


def fetch_search_html() -> str:
    payload = {
        "DataSourceId": DATA_SOURCE,
        "SearchText": "",
        "PageSize": 500,
        "PageNumber": "1",
        "isLoadMore": False,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SEARCH_URL,
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("DiningFolderHtml") or ""


def fetch_page_html() -> str:
    req = urllib.request.Request(
        FACILITIES_PAGE,
        headers={"User-Agent": "Mozilla/5.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_service_cards(html: str) -> list[dict]:
    rows: list[dict] = []
    for m in re.finditer(
        r'<div class="col-sm-12 col-md-6 col-lg-3 service-card">\s*'
        r'<div class="imageCardContent">\s*<a href="([^"]*)">.*?<h3>([^<]+)</h3>',
        html,
        re.S,
    ):
        path = m.group(1).strip()
        title = html_module.unescape(m.group(2)).strip()
        url = SITE + path if path.startswith("/") else path
        rows.append(
            {
                "name_display": title,
                "page_url": url,
                "section": "main_facilities",
            }
        )
    return rows


def parse_other_facilities(html: str) -> list[dict]:
    rows: list[dict] = []
    for m in re.finditer(
        r'<div class="swiper-slide imageCardContent">.*?<h3>([^<]+)</h3>',
        html,
        re.S,
    ):
        title = html_module.unescape(m.group(1)).strip()
        if not title:
            continue
        rows.append(
            {
                "name_display": title,
                "page_url": FACILITIES_PAGE,
                "section": "other_facilities_pranaam",
            }
        )
    return rows


def merge_static(
    parsed_main: list[dict], parsed_other: list[dict]
) -> list[dict]:
    """Union: static list wins URLs; add any API-only names."""
    by_name: dict[str, dict] = {}
    for title, path in STATIC_MAIN:
        by_name[title.lower()] = {
            "name_display": title,
            "page_url": SITE + path,
            "section": "main_facilities",
        }
    for title in STATIC_OTHER:
        by_name[title.lower()] = {
            "name_display": title,
            "page_url": FACILITIES_PAGE,
            "section": "other_facilities_pranaam",
        }
    for r in parsed_main + parsed_other:
        k = r["name_display"].lower()
        if k not in by_name:
            by_name[k] = r
        elif r.get("page_url") and by_name[k].get("page_url") == FACILITIES_PAGE:
            by_name[k]["page_url"] = r["page_url"]
    return list(by_name.values())


def rows_to_csv_rows(items: list[dict], node_xy: dict[str, tuple[float, float]]) -> list[dict]:
    out: list[dict] = []
    for r in sorted(items, key=lambda x: (x["section"], x["name_display"].lower())):
        name = r["name_display"]
        gid = graph_node_for(name)
        bx, by = node_xy.get(gid, (50.0, 50.0))
        seed = f"{name}|{r['section']}|{gid}"
        x, y = jitter_xy(bx, by, seed)
        fid = "fac_" + hashlib.md5(seed.encode("utf-8")).hexdigest()[:14]
        listing = (
            f"CSMIA Airport Facilities — {name} ({r['section'].replace('_', ' ')})"
        )
        out.append(
            {
                "facility_id": fid,
                "name_display": name,
                "name_normalized": re.sub(
                    r"[^a-z0-9]+",
                    "_",
                    html_module.unescape(name).lower(),
                ).strip("_")[:80],
                "category": r["section"],
                "x_norm": x,
                "y_norm": y,
                "floor": "L02",
                "zone": "facilities_overlay",
                "source": "csmia_facilities",
                "confidence": "high",
                "graph_node_id": gid,
                "listing_location": listing,
                "near_graph_hint": gid,
                "page_url": r.get("page_url") or "",
            }
        )
    return out


def main() -> None:
    node_xy = load_node_xy()
    page_html = ""
    search_html = ""
    try:
        page_html = fetch_page_html()
    except OSError as e:
        print("warn: GET facilities page failed:", e, file=sys.stderr)
    try:
        search_html = fetch_search_html()
    except OSError as e:
        print("warn: POST AirportServices/Search failed:", e, file=sys.stderr)

    parsed_main = parse_service_cards(page_html) + parse_service_cards(search_html)
    parsed_other = parse_other_facilities(page_html)
    merged = merge_static(parsed_main, parsed_other)
    csv_rows = rows_to_csv_rows(merged, node_xy)

    fieldnames = [
        "facility_id",
        "name_display",
        "name_normalized",
        "category",
        "x_norm",
        "y_norm",
        "floor",
        "zone",
        "source",
        "confidence",
        "graph_node_id",
        "listing_location",
        "near_graph_hint",
        "page_url",
    ]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(csv_rows)
    print(f"Wrote {len(csv_rows)} facilities to {OUT_CSV}")


if __name__ == "__main__":
    main()
