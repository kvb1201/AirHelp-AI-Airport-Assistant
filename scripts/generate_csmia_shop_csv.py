#!/usr/bin/env python3
"""
Fetch ALL shopping + dining outlets from CSMIA Sitecore API (same as the website),
parse every terminal tab and every address line, and write backend/app/data/shops_t2_l02.csv.

API (from /assets/mumbai/js/Dining-Search.js):
  POST https://csmia-mumbai.adaniairports.com/api/sitecore/Dining/Search

Shopping dataSourceId is on /en/shop-and-dine/shopping ; dining on /en/shop-and-dine/dining .

Uses only the Python standard library (urllib).
"""

from __future__ import annotations

import csv
import hashlib
import html as html_module
import re
import sys
from pathlib import Path

import json as json_lib
import urllib.request

URL = "https://csmia-mumbai.adaniairports.com/api/sitecore/Dining/Search"
SHOPPING_DS = "{27E24C80-FF3A-45A0-9CD1-2728CBADB018}"
DINING_DS = "{EC4EEF34-B2E1-4A9D-95C2-4CEDF348C00C}"

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "backend" / "app" / "data" / "shops_t2_l02.csv"

BASE_XY: dict[str, tuple[float, float]] = {
    "t2_l04_postsec": (50.0, 32.0),
    "t2_l03_postsec": (50.0, 40.0),
    "t2_vertical_core": (50.0, 54.5),
    "t2_post_security": (50.0, 58.0),
    "t2_entrance": (50.0, 86.0),
    "t2_baggage_claim": (50.0, 76.0),
    "bom_t1_retail_hub": (8.0, 93.0),
}


def fetch_html(data_source_id: str) -> tuple[str, int]:
    payload = {
        "DataSourceId": data_source_id,
        "Category": "",
        "Terminal": "",
        "Area": "",
        "SearchText": "",
        "PageSize": "500",
        "PageNumber": "1",
        "isLoadMore": False,
    }
    body = json_lib.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json_lib.loads(resp.read().decode("utf-8"))
    return data.get("DiningFolderHtml") or "", int(data.get("TotalItems") or 0)


def norm_name(s: str) -> str:
    s = html_module.unescape(s).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:80] or "unknown"


def assign_node(terminal: str, address: str) -> tuple[str, str]:
    """Returns (graph_node_id, zone slug)."""
    a = address.lower()
    if terminal == "T1":
        return "bom_t1_retail_hub", "t1_directory"
    if "level 4" in a or "level4" in a.replace(" ", ""):
        return "t2_l04_postsec", "postsec_l04"
    if "level 3" in a or "level3" in a.replace(" ", ""):
        return "t2_l03_postsec", "postsec_l03"
    if "level 2" in a:
        return "t2_vertical_core", "l02_vertical"
    if "check" in a and "in" in a:
        return "t2_entrance", "checkin_l02"
    if "arrival" in a or "baggage" in a:
        return "t2_baggage_claim", "arrivals_l02"
    if "gate" in a:
        return "t2_post_security", "airside_l02"
    return "t2_post_security", "airside_l02"


def jitter_xy(node_id: str, seed: str) -> tuple[float, float]:
    bx, by = BASE_XY[node_id]
    h = int(hashlib.md5(seed.encode("utf-8")).hexdigest()[:8], 16)
    dx = ((h % 241) - 120) / 65.0
    dy = (((h // 241) % 241) - 120) / 65.0
    return round(bx + dx, 4), round(by + dy, 4)


def parse_cards(folder_html: str, source_label: str) -> list[dict]:
    rows: list[dict] = []
    parts = folder_html.split('class="terminalCard')
    for part in parts[1:]:
        h4 = re.search(r"<h4>([^<]+)</h4>", part)
        if not h4:
            continue
        name_display = html_module.unescape(h4.group(1)).strip()
        cat_m = re.search(r'<div class="tags">\s*<span>([^<]+)</span>', part)
        category = (
            html_module.unescape(cat_m.group(1)).strip().lower().replace(" ", "_")
            if cat_m
            else ""
        )
        links = re.findall(
            r'data-bs-target="#(terminalTab[^"]+)"[^>]*>(Terminal [12])</a>',
            part,
        )
        for tid, tlabel in links:
            term = "T1" if tlabel.strip().endswith("1") else "T2"
            um = re.search(
                rf'<div class="tab-pane[^"]*"[^>]*id="{re.escape(tid)}"[^>]*>.*?<ul>(.*?)</ul>',
                part,
                re.S,
            )
            if not um:
                continue
            addrs = re.findall(r'<li class="address">([^<]+)</li>', um.group(1))
            if not addrs:
                addrs = [""]
            for addr_i, addr_raw in enumerate(addrs):
                listing = html_module.unescape(addr_raw)
                listing = " ".join(listing.split()).strip()
                gid, zone = assign_node(term, listing)
                seed = f"{name_display}|{term}|{listing}|{category}|{source_label}|{tid}|{addr_i}"
                x, y = jitter_xy(gid, seed)
                sid = "csmia_" + hashlib.md5(seed.encode("utf-8")).hexdigest()[:14]
                rows.append(
                    {
                        "shop_id": sid,
                        "name_display": name_display,
                        "name_normalized": norm_name(name_display),
                        "category": category,
                        "x_norm": x,
                        "y_norm": y,
                        "floor": "L04"
                        if gid == "t2_l04_postsec"
                        else (
                            "L03"
                            if gid == "t2_l03_postsec"
                            else (
                                "T1"
                                if term == "T1"
                                else "L02"
                            )
                        ),
                        "zone": zone,
                        "source": source_label,
                        "confidence": "high" if listing else "medium",
                        "graph_node_id": gid,
                        "listing_location": f"Terminal {term[-1]}; {listing}"
                        if listing
                        else f"Terminal {term[-1]}",
                        "near_graph_hint": gid,
                    }
                )
    return rows


def main() -> None:
    shop_html, shop_total = fetch_html(SHOPPING_DS)
    dine_html, dine_total = fetch_html(DINING_DS)
    all_rows = parse_cards(shop_html, "csmia_shopping_api") + parse_cards(
        dine_html, "csmia_dining_api"
    )
    if len(all_rows) < shop_total + dine_total - 5:
        print(
            f"warning: parsed {len(all_rows)} rows vs TotalItems {shop_total}+{dine_total}",
            file=sys.stderr,
        )

    fieldnames = [
        "shop_id",
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
    ]
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)
    print(f"Wrote {len(all_rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
