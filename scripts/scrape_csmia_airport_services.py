#!/usr/bin/env python3
"""Scrape CSMIA Airport Services page and export detailed JSON records."""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

import requests

BASE_URL = "https://csmia-mumbai.adaniairports.com"
SERVICES_PAGE = f"{BASE_URL}/en/airport-services"
SEARCH_API = f"{BASE_URL}/api/sitecore/AirportServices/Search"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = PROJECT_ROOT / "data" / "raw" / "airport_services_detailed.json"

FALLBACK_SERVICES = [
    "Duty-Free",
    "Lounges",
    "F&B Outlets",
    "Pranaam Meet & Greet",
    "Shopping",
    "Parking",
    "Valet Parking",
    "Transit Hotel",
    "Medical Centre",
    "Left Luggage",
    "Foreign Currency Exchange",
    "SIM Cards",
    "Pranaam Pharmacy",
    "Pranaam Spa Service",
    "Pranaam Vending Machines",
]


def clean_text(html_fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html_fragment)
    text = unescape(text).replace("\xa0", " ")
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


def extract_datasource_id(page_html: str) -> str | None:
    match = re.search(r'id="dataSourceId"\s+value="([^"]+)"', page_html)
    return match.group(1) if match else None


def parse_cards(html_text: str) -> list[dict]:
    cards: list[dict] = []
    for m in re.finditer(
        r'<div class="(?:[^"]*\s)?service-card(?:\s[^"]*)?">\s*'
        r'<div class="imageCardContent">\s*<a href="([^"]*)">.*?<h3>([^<]+)</h3>',
        html_text,
        flags=re.S,
    ):
        href = (m.group(1) or "").strip()
        name = clean_text(m.group(2))
        if not name:
            continue
        cards.append(
            {
                "name": name,
                "url": urljoin(BASE_URL, href) if href else SERVICES_PAGE,
            }
        )
    return cards


def fetch_search_cards(session: requests.Session, datasource_id: str) -> list[dict]:
    payload = {
        "DataSourceId": datasource_id,
        "SearchText": "",
        "PageSize": 500,
        "PageNumber": "1",
        "isLoadMore": False,
    }
    response = session.post(SEARCH_API, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    cards: list[dict] = []
    for value in data.values():
        if isinstance(value, str) and "<" in value and "service-card" in value:
            cards.extend(parse_cards(value))
    return cards


def dedupe_cards(cards: list[dict]) -> list[dict]:
    by_name: dict[str, dict] = {}
    for item in cards:
        key = item["name"].strip().lower()
        if key and key not in by_name:
            by_name[key] = item
    return list(by_name.values())


def extract_page_details(session: requests.Session, url: str) -> dict:
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        html_text = response.text
    except Exception as exc:  # noqa: BLE001
        return {
            "page_title": "",
            "headings": [],
            "summary_paragraphs": [],
            "bullet_points": [],
            "contact": {"phones": [], "emails": []},
            "error": str(exc),
        }

    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, flags=re.S | re.I)
    page_title = clean_text(title_match.group(1)) if title_match else ""
    headings = [
        clean_text(h)
        for h in re.findall(r"<h2[^>]*>(.*?)</h2>", html_text, flags=re.S | re.I)[:8]
        if clean_text(h)
    ]
    paragraphs = [
        clean_text(p)
        for p in re.findall(r"<p[^>]*>(.*?)</p>", html_text, flags=re.S | re.I)
        if clean_text(p)
    ]
    bullets = [
        clean_text(li)
        for li in re.findall(r"<li[^>]*>(.*?)</li>", html_text, flags=re.S | re.I)
        if clean_text(li)
    ]
    noise_exact = {"privacy policy", "accept all", "strictly necessary", "search"}
    noise_contains = [
        "we use cookies",
        "popular searches",
        "airport guide passenger guide",
        "shop & dine",
        "business cargo",
        "light mode",
        "dark mode",
        "datepicker-orient-top",
        "suggestion lost & found",
        "chhatrapati shivaji maharaj international airport mumbai",
    ]

    def keep_text(value: str) -> bool:
        v = value.strip().lower()
        if not v or v in noise_exact:
            return False
        return not any(token in v for token in noise_contains)

    paragraphs = [p for p in paragraphs if keep_text(p)][:12]
    bullets = [b for b in bullets if keep_text(b)][:30]
    phones = sorted(set(re.findall(r"\+?\d[\d\-\s]{7,}\d", clean_text(html_text))))[:5]
    emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html_text)))[:5]
    return {
        "page_title": page_title,
        "headings": headings,
        "summary_paragraphs": paragraphs,
        "bullet_points": bullets,
        "contact": {"phones": phones, "emails": emails},
    }


def main() -> None:
    session = get_session()
    base_response = session.get(SERVICES_PAGE, timeout=60)
    base_response.raise_for_status()
    page_html = base_response.text

    cards = parse_cards(page_html)
    datasource_id = extract_datasource_id(page_html)
    if datasource_id:
        try:
            cards.extend(fetch_search_cards(session, datasource_id))
        except Exception as exc:  # noqa: BLE001
            print(f"warn: AirportServices/Search failed: {exc}")

    cards = dedupe_cards(cards)
    existing = {c["name"].strip().lower() for c in cards}
    for name in FALLBACK_SERVICES:
        if name.lower() not in existing:
            cards.append({"name": name, "url": SERVICES_PAGE})

    cards = sorted(cards, key=lambda item: item["name"].lower())
    records = []
    for idx, card in enumerate(cards, start=1):
        records.append(
            {
                "id": f"airport_service_{idx:03d}",
                "name": card["name"],
                "service_url": card["url"],
                "source_page": SERVICES_PAGE,
                **extract_page_details(session, card["url"]),
            }
        )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} services to {OUT_JSON}")


if __name__ == "__main__":
    main()
