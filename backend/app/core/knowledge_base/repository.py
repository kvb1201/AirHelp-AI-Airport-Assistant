"""Compile and query the airport knowledge base from the project's data folder."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from app.core.knowledge_base.schemas import (
    Flight,
    KnowledgeBaseSnapshot,
    KnowledgeChunk,
    Level,
    Offer,
    Place,
    PlaceLocation,
    PreferenceProfile,
    RawDocument,
    RawPlaceSeed,
    RecommendedForProfile,
    TerminalStructure,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = PROJECT_ROOT / "data"
RAW_ROOT = DATA_ROOT / "raw"
AIRPORT_ROOT = DATA_ROOT / "airport"
RAG_ROOT = DATA_ROOT / "rag"
MOCK_ROOT = DATA_ROOT / "mock"

TERMINAL_ID = "T2"
TERMINAL_NAME = "Mumbai Airport Terminal 2"

PLACE_CATEGORY_MAP = {
    "food": "food",
    "shops": "shop",
    "services": "service",
}

PLACE_INTENT_MAP = {
    "food": ["food", "quick_stop"],
    "shops": ["shopping"],
    "services": ["utility"],
}

PLACE_SUBCATEGORY_MAP = {
    "coffee": "coffee",
    "indian food": "indian_food",
    "retail": "general_retail",
    "meet and greet": "meet_and_greet",
    "lounge": "lounge",
}

LUXURY_BRANDS = {
    "armani exchange",
    "amrapali",
    "forest essentials",
    "hamleys",
    "sunglass hut",
    "victoria's secret",
    "tumi",
    "twg tea",
    "samsonite",
}

COFFEE_KEYWORDS = {"coffee", "cafe", "café", "brew", "chaipoint", "starbucks", "costa"}
QUICK_BITE_KEYWORDS = {"qsr", "quick bites", "snack", "burger", "pizza", "juice", "deli"}
BAR_KEYWORDS = {"bar", "pub", "beer", "house"}
LOUNGE_KEYWORDS = {"lounge", "amex"}


class KnowledgeBaseRepository:
    """Owns the V1 non-navigation airport knowledge base lifecycle."""

    def __init__(self) -> None:
        self.raw_root = RAW_ROOT
        self.airport_root = AIRPORT_ROOT
        self.rag_root = RAG_ROOT
        self.mock_root = MOCK_ROOT

    def ensure_compiled(self) -> KnowledgeBaseSnapshot:
        """Build normalized files on demand so the app can start from seed data."""
        self.airport_root.mkdir(parents=True, exist_ok=True)
        self.rag_root.mkdir(parents=True, exist_ok=True)

        snapshot = self._build_snapshot()
        self._write_snapshot(snapshot)
        return snapshot

    def load_snapshot(self) -> KnowledgeBaseSnapshot:
        """Load the compiled knowledge base, rebuilding it if files are missing."""
        required = [
            self.airport_root / "terminal_structure.json",
            self.airport_root / "places.json",
            self.airport_root / "flights.json",
            self.airport_root / "offers.json",
            self.airport_root / "raw_documents.json",
            self.rag_root / "knowledge_chunks.json",
        ]
        if not all(path.exists() for path in required):
            return self.ensure_compiled()

        return KnowledgeBaseSnapshot(
            terminal_structure=TerminalStructure.model_validate(self._read_json(required[0])),
            places=[Place.model_validate(item) for item in self._read_json(required[1])],
            flights=[Flight.model_validate(item) for item in self._read_json(required[2])],
            offers=[Offer.model_validate(item) for item in self._read_json(required[3])],
            raw_documents=[RawDocument.model_validate(item) for item in self._read_json(required[4])],
            rag_chunks=[KnowledgeChunk.model_validate(item) for item in self._read_json(required[5])],
        )

    def search_places(
        self,
        query: str,
        *,
        category: str | None = None,
        intent: str | None = None,
        limit: int = 5,
    ) -> list[Place]:
        """Use lightweight lexical scoring over structured place fields."""
        snapshot = self.load_snapshot()
        query_terms = [term for term in query.lower().split() if term]

        candidates = snapshot.places
        if category:
            candidates = [place for place in candidates if place.category == category]
        if intent:
            candidates = [place for place in candidates if intent in place.intents]

        scored: list[tuple[int, Place]] = []
        for place in candidates:
            haystack = " ".join(
                [
                    place.name.lower(),
                    place.description.lower(),
                    place.sub_category.lower(),
                    " ".join(place.intents).lower(),
                ]
            )
            score = sum(3 for term in query_terms if term in place.name.lower())
            score += sum(1 for term in query_terms if term in haystack)
            if score > 0:
                scored.append((score, place))

        scored.sort(key=lambda item: (-item[0], item[1].name))
        return [place for _, place in scored[:limit]]

    def get_relevant_chunks(self, query: str, limit: int = 5) -> list[dict]:
        """Return chunk-like records that can be passed directly to prompting code."""
        snapshot = self.load_snapshot()
        query_terms = [term for term in query.lower().split() if term]
        scored: list[tuple[int, KnowledgeChunk]] = []
        for chunk in snapshot.rag_chunks:
            text = chunk.text.lower()
            score = sum(1 for term in query_terms if term in text)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: (-item[0], item[1].id))
        return [chunk.model_dump() for _, chunk in scored[:limit]]

    def _build_snapshot(self) -> KnowledgeBaseSnapshot:
        timestamp = datetime.now(timezone.utc).isoformat()
        seeds_by_collection = self._load_seed_collections()

        raw_documents = [
            self._build_raw_document("food", seeds_by_collection["food"], timestamp),
            self._build_raw_document("shops", seeds_by_collection["shops"], timestamp),
            self._build_raw_document("services", seeds_by_collection["services"], timestamp),
        ]

        places: list[Place] = []
        for collection_name, seeds in seeds_by_collection.items():
            for seed in seeds:
                places.append(self._normalize_place_seed(collection_name, seed, timestamp))

        flights = self._load_flights(timestamp)
        offers = self._build_placeholder_offers(timestamp)
        terminal_structure = TerminalStructure(
            terminal_id=TERMINAL_ID,
            name=TERMINAL_NAME,
            levels=[
                Level(level_id="L1", name="Arrivals", zones=["A", "B"]),
                Level(level_id="L2", name="Departures", zones=["A", "B", "C"]),
            ],
            source_url="local://terminal_structure/v1",
            last_verified_at=timestamp,
            confidence=0.9,
        )
        rag_chunks = self._build_rag_chunks(places, offers, raw_documents)

        return KnowledgeBaseSnapshot(
            terminal_structure=terminal_structure,
            places=places,
            flights=flights,
            offers=offers,
            raw_documents=raw_documents,
            rag_chunks=rag_chunks,
        )

    def _load_seed_collections(self) -> dict[str, list[RawPlaceSeed]]:
        return {
            "food": self._load_seed_file("food.json"),
            "shops": self._load_seed_file("shops.json"),
            "services": self._load_seed_file("services.json"),
        }

    def _load_seed_file(self, filename: str) -> list[RawPlaceSeed]:
        payload = self._read_json(self.raw_root / filename)
        return [RawPlaceSeed.model_validate(item) for item in payload]

    def _normalize_place_seed(self, collection_name: str, seed: RawPlaceSeed, timestamp: str) -> Place:
        canonical_sub_category = PLACE_SUBCATEGORY_MAP.get(seed.category.lower(), "general")
        place_category = PLACE_CATEGORY_MAP[collection_name]
        inferred_level = self._infer_level(seed.location_text)
        near_nodes = self._infer_near(seed.location_text)
        inferred_type = self._infer_place_type(place_category, seed)
        speed = self._infer_speed(place_category, inferred_type)
        price_level = self._infer_price_level(place_category, inferred_type, seed.name)
        queue_time = self._infer_queue_time(place_category, inferred_type)
        avg_time_spent = self._infer_avg_time_spent(place_category, inferred_type)
        recommended_for = self._build_recommended_for(
            place_category,
            inferred_type,
            price_level,
            speed,
            avg_time_spent,
            seed.name,
        )

        # We store approximate location text now so the retrieval layer has a
        # stable schema even before gate-level navigation data is added.
        location = PlaceLocation(
            terminal=seed.terminal,
            level=inferred_level or ("L2" if seed.terminal == TERMINAL_ID else None),
            zone=None,
            location_text=seed.location_text or "Terminal 2 public dataset",
            near_text=near_nodes,
        )

        attributes: dict[str, str] = {}
        if place_category == "food":
            attributes["cuisine"] = inferred_type
        elif place_category == "shop":
            attributes["retailType"] = inferred_type
        else:
            attributes["serviceType"] = inferred_type

        return Place(
            id=seed.id.upper(),
            name=seed.name,
            category=place_category,
            sub_category=canonical_sub_category,
            type=inferred_type,
            level=location.level,
            near=near_nodes,
            speed=speed,
            price_level=price_level,
            queue_time=queue_time,
            avg_time_spent=avg_time_spent,
            location=location,
            recommended_for=recommended_for,
            attributes=attributes,
            service_options={"wheelchairAccessible": None},
            metadata={
                "dataQuality": "seed",
                "enrichmentSource": "heuristic_inference",
                "hasInferredAudience": True,
            },
            offers=[],
            intents=PLACE_INTENT_MAP.get(collection_name, []),
            description=seed.description,
            aliases=[seed.name.lower()],
            source_url=f"local://data/raw/{collection_name}.json",
            source_type=seed.source_type,
            source_name=seed.source_name,
            last_verified_at=timestamp,
            confidence=0.7,
            status="active",
        )

    def _infer_level(self, location_text: str | None) -> str | None:
        if not location_text:
            return None
        match = re.search(r"level[-\s]*(\d+)", location_text, flags=re.I)
        if match:
            return f"L{match.group(1)}"
        return None

    def _infer_near(self, location_text: str | None) -> list[str]:
        if not location_text:
            return []
        near: list[str] = []
        for gate in re.findall(r"gate\s*(\d+[A-Z]?)", location_text, flags=re.I):
            near.append(f"GATE_{gate.upper()}")
        if "foodcourt" in location_text.lower():
            near.append("FOODCOURT")
        if "arrival forecourt" in location_text.lower():
            near.append("ARRIVAL_FORECOURT")
        if "landside" in location_text.lower():
            near.append("LANDSIDE")
        return near

    def _infer_place_type(self, place_category: str, seed: RawPlaceSeed) -> str:
        category_text = seed.category.lower()
        name_text = seed.name.lower()
        combined = f"{name_text} {category_text}"

        if place_category == "food":
            if any(keyword in combined for keyword in COFFEE_KEYWORDS):
                return "coffee"
            if any(keyword in combined for keyword in BAR_KEYWORDS):
                return "bar_restaurant"
            if any(keyword in combined for keyword in QUICK_BITE_KEYWORDS):
                return "quick_bites"
            return "restaurant"

        if place_category == "shop":
            if name_text in LUXURY_BRANDS:
                return "luxury"
            if "jewellary" in category_text or "jewelry" in category_text:
                return "jewelry"
            if "apparel" in category_text:
                return "fashion"
            if "electronics" in category_text:
                return "electronics"
            if "books" in name_text or "ctn" in category_text:
                return "books_convenience"
            return category_text.replace(" / ", "_").replace(" ", "_")

        if any(keyword in combined for keyword in LOUNGE_KEYWORDS):
            return "lounge"
        return category_text.replace(" ", "_")

    def _infer_speed(self, place_category: str, inferred_type: str) -> str:
        if place_category == "food":
            if inferred_type in {"coffee", "quick_bites"}:
                return "fast"
            if inferred_type == "bar_restaurant":
                return "slow"
            return "medium"
        if place_category == "shop":
            if inferred_type in {"books_convenience", "electronics"}:
                return "fast"
            if inferred_type in {"luxury", "jewelry"}:
                return "slow"
            return "medium"
        return "slow" if inferred_type == "lounge" else "medium"

    def _infer_price_level(self, place_category: str, inferred_type: str, name: str) -> str:
        name_text = name.lower()
        if place_category == "food":
            if inferred_type == "coffee":
                return "medium"
            if inferred_type == "bar_restaurant":
                return "high"
            if inferred_type == "quick_bites":
                return "low"
            return "medium"
        if place_category == "shop":
            if inferred_type in {"luxury", "jewelry"} or name_text in LUXURY_BRANDS:
                return "high"
            if inferred_type in {"books_convenience", "sweets_/_packed_foods"}:
                return "low"
            return "medium"
        return "high" if inferred_type == "lounge" else "medium"

    def _infer_queue_time(self, place_category: str, inferred_type: str) -> int:
        if place_category == "food":
            return 3 if inferred_type == "coffee" else 5 if inferred_type == "quick_bites" else 8
        if place_category == "shop":
            return 2 if inferred_type in {"books_convenience", "electronics"} else 4
        return 6 if inferred_type == "lounge" else 4

    def _infer_avg_time_spent(self, place_category: str, inferred_type: str) -> int:
        if place_category == "food":
            if inferred_type == "coffee":
                return 12
            if inferred_type == "quick_bites":
                return 10
            if inferred_type == "bar_restaurant":
                return 30
            return 20
        if place_category == "shop":
            if inferred_type in {"luxury", "jewelry"}:
                return 25
            if inferred_type in {"books_convenience", "electronics"}:
                return 10
            return 18
        return 45 if inferred_type == "lounge" else 15

    def _build_recommended_for(
        self,
        place_category: str,
        inferred_type: str,
        price_level: str,
        speed: str,
        avg_time_spent: int,
        name: str,
    ) -> RecommendedForProfile:
        age_groups = ["adult"]
        travel_types = ["solo"]
        budget_levels = [price_level]
        mobility = ["normal"]
        preferences = PreferenceProfile()

        name_text = name.lower()
        if place_category == "food":
            if inferred_type == "coffee":
                age_groups = ["young", "adult"]
                travel_types = ["solo", "business"]
                preferences.food = ["coffee", "quick_service"]
                preferences.interests = ["quick_exit", "explore"]
            elif inferred_type == "quick_bites":
                age_groups = ["child", "young", "adult"]
                travel_types = ["solo", "family"]
                budget_levels = ["low", "medium"]
                preferences.food = ["fast_food"]
                preferences.interests = ["quick_exit"]
            elif inferred_type == "bar_restaurant":
                age_groups = ["adult"]
                travel_types = ["business", "solo"]
                budget_levels = ["medium", "high"]
                preferences.food = ["fine_dining"]
                preferences.interests = ["relax"]
            else:
                age_groups = ["young", "adult", "elderly"]
                travel_types = ["solo", "family", "business"]
                preferences.food = ["veg", "fine_dining"]
                preferences.interests = ["relax", "explore"]

        elif place_category == "shop":
            if inferred_type in {"luxury", "jewelry"} or name_text in LUXURY_BRANDS:
                age_groups = ["young", "adult"]
                travel_types = ["solo", "business"]
                budget_levels = ["high"]
                preferences.shopping = ["luxury"]
                preferences.interests = ["explore", "relax"]
            elif inferred_type == "electronics":
                age_groups = ["young", "adult"]
                travel_types = ["solo", "business"]
                preferences.shopping = ["electronics"]
                preferences.interests = ["quick_exit", "explore"]
            else:
                age_groups = ["young", "adult", "elderly"]
                travel_types = ["solo", "family"]
                preferences.shopping = ["local"]
                preferences.interests = ["explore"]

        else:
            age_groups = ["adult", "elderly"]
            travel_types = ["business", "family", "solo"]
            budget_levels = ["medium", "high"]
            mobility = ["normal", "assistance_needed", "wheelchair"]
            preferences.interests = ["relax"]

        # Fast coffee chains and premium brands are often chosen by younger and
        # higher-spend travelers, but this is heuristic enrichment rather than
        # a fact sourced from the airport website.
        if "starbucks" in name_text:
            age_groups = ["young", "adult"]
            budget_levels = ["medium", "high"]
            travel_types = ["solo", "business"]

        return RecommendedForProfile(
            age_groups=age_groups,
            travel_types=travel_types,
            budget_levels=budget_levels,
            mobility=mobility,
            preferences=preferences,
            min_time_available=max(5, avg_time_spent if speed == "slow" else avg_time_spent // 2),
        )

    def _build_raw_document(self, page_type: str, seeds: list[RawPlaceSeed], timestamp: str) -> RawDocument:
        content = json.dumps([seed.model_dump() for seed in seeds], indent=2, ensure_ascii=False)
        return RawDocument(
            id=f"raw_{page_type}",
            source_url=f"local://data/raw/{page_type}.json",
            source_type="manual_seed",
            page_type=page_type,
            fetched_at=timestamp,
            content=content,
            checksum=sha256(content.encode("utf-8")).hexdigest(),
        )

    def _load_flights(self, timestamp: str) -> list[Flight]:
        flights_path = self.mock_root / "flights.json"
        payload = self._read_json(flights_path)
        if isinstance(payload, list) and payload:
            return [Flight.model_validate(item) for item in payload]

        # Placeholder records preserve the final schema until a live flight
        # source is wired into the backend.
        return [
            Flight(
                flight_id="TBD_FLIGHT_FEED",
                airline="Unknown",
                type="departure",
                terminal=TERMINAL_ID,
                gate=None,
                check_in=None,
                timings={"scheduled": "", "boarding": "", "departure": ""},
                status="data_pending",
                category="unknown",
                source_url="local://pending/flights",
                last_verified_at=timestamp,
            )
        ]

    def _build_placeholder_offers(self, timestamp: str) -> list[Offer]:
        return [
            Offer(
                offer_id="TBD_OFFER_FEED",
                title="Offers feed pending ingestion",
                type="info",
                description="Official airport offer pages have not been normalized yet.",
                valid_at=[],
                valid_till=None,
                tags=["pending"],
                source_url="local://pending/offers",
                last_verified_at=timestamp,
                status="draft",
            )
        ]

    def _build_rag_chunks(
        self,
        places: list[Place],
        offers: list[Offer],
        raw_documents: list[RawDocument],
    ) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []

        for place in places:
            chunks.append(
                KnowledgeChunk(
                    id=f"chunk_place_{place.id.lower()}",
                    entity_type="place",
                    entity_id=place.id,
                    text=(
                        f"{place.name} is a {place.category} in {place.location.terminal}. "
                        f"Type: {place.type}. "
                        f"Price level: {place.price_level}. "
                        f"Speed: {place.speed}. "
                        f"Recommended for age groups: {', '.join(place.recommended_for.age_groups)}. "
                        f"Description: {place.description}. "
                        f"Intents: {', '.join(place.intents)}."
                    ),
                    source_url=place.source_url,
                )
            )

        for offer in offers:
            chunks.append(
                KnowledgeChunk(
                    id=f"chunk_offer_{offer.offer_id.lower()}",
                    entity_type="offer",
                    entity_id=offer.offer_id,
                    text=f"{offer.title}. {offer.description}. Tags: {', '.join(offer.tags)}.",
                    source_url=offer.source_url,
                )
            )

        for document in raw_documents:
            chunks.append(
                KnowledgeChunk(
                    id=f"chunk_raw_{document.id}",
                    entity_type="raw_document",
                    entity_id=document.id,
                    text=document.content,
                    source_url=document.source_url,
                )
            )

        return chunks

    def _write_snapshot(self, snapshot: KnowledgeBaseSnapshot) -> None:
        self._write_json(self.airport_root / "terminal_structure.json", snapshot.terminal_structure.model_dump())
        self._write_json(self.airport_root / "places.json", [item.model_dump() for item in snapshot.places])
        self._write_json(self.airport_root / "flights.json", [item.model_dump() for item in snapshot.flights])
        self._write_json(self.airport_root / "offers.json", [item.model_dump() for item in snapshot.offers])
        self._write_json(
            self.airport_root / "raw_documents.json",
            [item.model_dump() for item in snapshot.raw_documents],
        )
        self._write_json(self.rag_root / "knowledge_chunks.json", [item.model_dump() for item in snapshot.rag_chunks])

    def _read_json(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: Path, payload: object) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
