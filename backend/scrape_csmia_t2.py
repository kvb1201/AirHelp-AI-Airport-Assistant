"""Scrape official CSMIA Mumbai website data for Terminal 2 only."""

from __future__ import annotations

import csv
import json
import re
from html import unescape
from pathlib import Path

import requests

from app.services.rag_service import build_knowledge_base


BASE_URL = "https://csmia-mumbai.adaniairports.com"
DINING_PAGE = f"{BASE_URL}/en/shop-and-dine/dining"
SHOPPING_PAGE = f"{BASE_URL}/en/shop-and-dine/shopping"
LOUNGES_PAGE = f"{BASE_URL}/en/airport-services/lounges"
DINING_API = f"{BASE_URL}/api/sitecore/Dining/Search"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"
RAW_ROOT = DATA_ROOT / "raw"


def clean_text(value: str) -> str:
    """Normalize HTML fragments into compact text."""
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    if "Ã" in text:
        try:
            text = text.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
    text = text.replace("Ã ", "à")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }
    )
    return session


def extract_datasource_id(page_html: str) -> str:
    match = re.search(r'id="dataSourceId"\s+value="([^"]+)"', page_html)
    if not match:
        raise RuntimeError("Unable to find dataSourceId in page HTML")
    return match.group(1)


def fetch_listing_html(session: requests.Session, page_url: str) -> str:
    """Use the official search endpoint that powers shopping and dining."""
    page_response = session.get(page_url, timeout=30)
    page_response.encoding = "utf-8"
    page_html = page_response.text
    payload = {
        "DataSourceId": extract_datasource_id(page_html),
        "Category": "",
        "Terminal": "",
        "Area": "",
        "SearchText": "",
        "PageSize": "500",
        "PageNumber": "1",
        "isLoadMore": False,
    }
    response = session.post(DINING_API, json=payload, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.json()["DiningFolderHtml"]


def split_terminal_cards(cards_html: str) -> list[str]:
    parts = re.split(r'(?=<div class="terminalCard scale-anm">)', cards_html)
    return [part for part in parts if 'terminalCard scale-anm' in part]


def parse_shop_dine_cards(cards_html: str, entity_type: str, source_query: str) -> list[dict]:
    records: list[dict] = []
    next_id = 1
    for card in split_terminal_cards(cards_html):
        name_match = re.search(r"<h4>(.*?)</h4>", card, flags=re.S)
        terminal_match = re.search(r'<div class="terminalContent">.*?<span>(.*?)</span>', card, flags=re.S)
        tag_match = re.search(r'<div class="tags">\s*<span>(.*?)</span>', card, flags=re.S)
        addresses = [clean_text(text) for text in re.findall(r'<li class="address">(.*?)</li>', card, flags=re.S)]

        if not name_match or not terminal_match:
            continue

        terminal = clean_text(terminal_match.group(1))
        if terminal != "T2":
            continue

        name = clean_text(name_match.group(1))
        category = clean_text(tag_match.group(1)) if tag_match else entity_type
        location_text = " | ".join(addresses) if addresses else "Terminal 2"
        description = (
            f"Official CSMIA listing for {name} in Terminal 2. "
            f"Category: {category}. Location: {location_text}."
        )

        records.append(
            {
                "id": f"{entity_type}_{next_id:03d}",
                "name": name,
                "terminal": "T2",
                "category": category,
                "description": description,
                "location_text": location_text,
                "source_type": "official",
                "source_name": "csmia_adani_airports",
                "source_query": source_query,
            }
        )
        next_id += 1

    return records


def parse_lounges_page(page_html: str, source_query: str) -> list[dict]:
    """Extract lounge entries that explicitly mention Terminal 2 addresses."""
    starts = [match.start() for match in re.finditer(r'<div class="tab-pane', page_html)]
    records: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()

    for start, end in zip(starts, starts[1:] + [len(page_html)]):
        chunk = page_html[start:end]
        name_match = re.search(r"<h4>(.*?)</h4>", chunk, flags=re.S)
        address_match = re.search(r'<li class="address">(.*?)</li>', chunk, flags=re.S)
        if not name_match or not address_match:
            continue

        address = clean_text(address_match.group(1))
        if "Terminal-2" not in address and "Terminal 2" not in address and "T2" not in address:
            continue

        name = clean_text(name_match.group(1))
        key = (name, address)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        description_match = re.search(r"</div>\s*<p>(.*?)</p>", chunk, flags=re.S)
        description = clean_text(description_match.group(1)) if description_match else ""
        if not description:
            bullet_items = [clean_text(text) for text in re.findall(r"<li>(.*?)</li>", chunk, flags=re.S)]
            description = " ".join(bullet_items[:6]).strip()
        if not description:
            description = f"Official CSMIA lounge listing for {name} in Terminal 2."

        records.append(
            {
                "id": f"service_{len(records) + 1:03d}",
                "name": name,
                "terminal": "T2",
                "category": "lounge",
                "description": description,
                "location_text": address,
                "source_type": "official",
                "source_name": "csmia_adani_airports",
                "source_query": source_query,
            }
        )

    return records


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def write_collection_sheet(records: list[dict]) -> None:
    fieldnames = [
        "id",
        "entity_type",
        "name",
        "terminal",
        "category",
        "description",
        "location_text",
        "source_type",
        "source_name",
        "source_query",
    ]
    with (RAW_ROOT / "collection_sheet.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    session = get_session()
    food_records = parse_shop_dine_cards(fetch_listing_html(session, DINING_PAGE), "food", DINING_PAGE)
    shop_records = parse_shop_dine_cards(fetch_listing_html(session, SHOPPING_PAGE), "shop", SHOPPING_PAGE)
    lounge_response = session.get(LOUNGES_PAGE, timeout=30)
    lounge_response.encoding = "utf-8"
    service_records = parse_lounges_page(lounge_response.text, LOUNGES_PAGE)

    write_json(RAW_ROOT / "food.json", food_records)
    write_json(RAW_ROOT / "shops.json", shop_records)
    write_json(RAW_ROOT / "services.json", service_records)

    rows = []
    for entity_type, records in [("food", food_records), ("shop", shop_records), ("service", service_records)]:
        for record in records:
            rows.append({"entity_type": entity_type, **record})
    write_collection_sheet(rows)

    # Keep normalized outputs in sync with the freshly scraped official data.
    build_knowledge_base()

    print(f"Scraped {len(food_records)} food records")
    print(f"Scraped {len(shop_records)} shop records")
    print(f"Scraped {len(service_records)} service records")


if __name__ == "__main__":
    main()
