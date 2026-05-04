# Knowledge base and data reference (DeepForge / ps3_DeepForge)

This document describes **what counts as “knowledge” in the project**, **where each dataset lives**, **how it was obtained or produced**, **extra fields added at compile time**, and **what the runtime computes** from it (recommendations, RAG, navigation, flight timing, travel documents). It is derived from the current backend and `data/` layout.

---

## 1. Two complementary layers

The system does **not** use a single monolithic KB file. Instead:

| Layer | Role | Primary locations |
| --- | --- | --- |
| **A. Compiled airport KB** | Normalized places, terminal shell, flights stub, offers stub, RAG text chunks (lexical retrieval) | `data/raw/*.json` → `data/airport/*.json`, `data/rag/knowledge_chunks.json` |
| **B. RAG “airport_data”** | Richer structured sections (gates, terminals, shops in older schema) used by **Chroma** embedding pipeline | `backend/app/core/rag/airport_data.json` |
| **C. Walking graph + POI overlays** | Shortest-path routing, turn-by-turn, distances; shops/facilities with **normalized map coordinates** | `backend/app/data/mumbai_t2_level02_graph.json` (via `app.core.graph.airport_data`), `backend/app/data/shops_t2_l02.csv`, `backend/app/data/facilities_bom.csv` |
| **D. Travel requirements** | Country-level document checklists + city→country map | `backend/app/data/travel_documents.json`, `backend/app/data/city_country_mapping.json` |
| **E. Orchestrator flight catalog** | Mock T2 flight list + optional food/shop snippets for demos | `backend/app/data/mumbai_t2_catalog.json` |

Layers **A** and **B** both feed “assistant” behavior but through **different code paths** (`KnowledgeBaseRepository` vs `AirportRAGPipeline`).

---

## 2. Layer A — compiled knowledge base (food, shops, services)

### 2.1 How the raw data is obtained

- **Primary refresh path**: scraper `backend/scrape_csmia_t2.py` (also documented in `docs/knowledge_base_implementation.md`).
- **Official pages used** (CSMIA / Adani):
  - Dining: `https://csmia-mumbai.adaniairports.com/en/shop-and-dine/dining`
  - Shopping: `https://csmia-mumbai.adaniairports.com/en/shop-and-dine/shopping`
  - Lounges: `https://csmia-mumbai.adaniairports.com/en/airport-services/lounges`
- Raw outputs are JSON arrays under:
  - `data/raw/food.json`
  - `data/raw/shops.json`
  - `data/raw/services.json`

Each raw row matches schema **`RawPlaceSeed`** (`backend/app/core/knowledge_base/schemas.py`): `id`, `name`, `terminal`, `category`, `description`, optional `location_text`, plus provenance fields `source_type`, `source_name`, `source_query`.

### 2.2 Compilation pipeline

`KnowledgeBaseRepository` (`backend/app/core/knowledge_base/repository.py`) runs on backend startup (via `main.py`) if compiled files are missing. It:

1. Loads the three seed files.
2. Normalizes every seed into a **`Place`** record (see §2.3).
3. Builds **`TerminalStructure`** (fixed T2 hierarchy: L1 Arrivals zones A/B, L2 Departures zones A/B/C).
4. Loads flights from **`data/mock/flights.json`** into **`Flight`** objects (or placeholders if the file is empty).
5. Adds **placeholder offers** until a real offers feed exists.
6. Wraps each seed collection into a **`RawDocument`** (full JSON text + SHA-256 checksum).
7. Materializes **`KnowledgeChunk`** rows for lexical retrieval (place summaries, offer text, raw JSON blobs).

### 2.3 Extra fields added during normalization (not in raw JSON)

For each `Place`, the repository **infers** (heuristics, not scraped facts):

| Added concept | Meaning |
| --- | --- |
| `category` | Mapped from collection: `food` → food, `shops` → shop, `services` → service |
| `sub_category` | From `PLACE_SUBCATEGORY_MAP` or `general` |
| `type` | Inferred from name/category keywords (e.g. coffee, luxury, lounge) |
| `level` | Regex on `location_text` for `level N`, else default `L2` for T2 |
| `near` | Parsed tokens: gates → `GATE_XX`, `foodcourt` → `FOODCOURT`, landside phrases, etc. |
| `speed`, `price_level`, `queue_time`, `avg_time_spent` | Rule tables by category/type |
| `recommended_for` | Synthetic audience profile (`RecommendedForProfile`) |
| `attributes` | e.g. `cuisine` / `retailType` / `serviceType` |
| `intents` | From collection: food → food/quick_stop, shops → shopping, services → utility |
| `metadata` | Flags like `dataQuality: seed`, `enrichmentSource: heuristic_inference` |
| `confidence` | Typically `0.7` for seeded data |

**Important:** These enrichments exist so retrieval and prompts have a **stable schema** before gate-accurate indoor positioning is attached (`repository.py` comments).

### 2.4 Compiled outputs

Written under:

- `data/airport/terminal_structure.json`
- `data/airport/places.json`
- `data/airport/flights.json`
- `data/airport/offers.json`
- `data/airport/raw_documents.json`
- `data/rag/knowledge_chunks.json`

### 2.5 What is computed from Layer A at query time

- **`search_places`**: Token overlap scoring on name, description, subcategory, intents.
- **`get_relevant_chunks`**: Token overlap on chunk text (used by orchestrator and `NavigationKnowledgeIntegrator` for route context).

---

## 3. Layer B — RAG pipeline (`airport_data.json`)

### 3.1 Source file

- Path: `backend/app/core/rag/airport_data.json` (see `rag_service.py`).
- Contains a large JSON object: coordinate system metadata, sample **`airport_alerts`**, **`flights`** section, and categorized POI lists consumed by `backend/app/core/rag/loader.py` (`gates`, `terminals`, `food_courts`, `food_outlets`, `shops`, `services`, `facilities`, `check_in_counters`, `baggage_belts`, `flights`, etc.).

### 3.2 Processing

- `load_airport_data()` flattens sections into `{"text", "metadata"}` documents.
- `AirportRAGPipeline` chunks, embeds, and indexes into **ChromaDB** (`backend/app/core/rag/vector_store.py`) for semantic search used during chat/recommendations.

### 3.3 Relationship to navigation

- RAG node IDs often look like `node-t2-entrance`. The walking graph uses IDs like `t2_entrance`.
- **`backend/app/data/rag_to_graph_node_map.json`** maps RAG-style IDs to **graph node IDs** without editing the large JSON files (`node_mapper.py`).

---

## 4. Layer C — navigation graph, shops, facilities

### 4.1 Graph topology

- **`app.core.graph.airport_data`** exposes **`NODES`** and **`EDGES`** built from the Mumbai T2 Level 02 graph (see module docstring: produced by `scripts/build_mumbai_t2_l02_graph.py`; serialized data under `backend/app/data/mumbai_t2_level02_graph.json`).
- **`PathFinder`** computes shortest paths in **minutes** using edge weights; **`congestion.py`** can add extra minutes on security-related edges using **time-of-day priors** and optional **`congestion_overlay.json`**.

### 4.2 Shop and facility overlays (not the same as `data/raw/shops.json`)

| File | Purpose |
| --- | --- |
| `backend/app/data/shops_t2_l02.csv` | Shop directory with **`x_norm` / `y_norm`** (0–100), **`graph_node_id`**, categories, display names |
| `backend/app/data/facilities_bom.csv` | Restrooms, information desks, medical, prayer rooms, etc., with the same coordinate + **`graph_node_id`** pattern |

Loaders (`shops_loader.py`, `facilities_loader.py`) expose rows as dictionaries used for:

- Resolving **names** to graph nodes (`navigation_service.resolve_shop_name_to_graph_node`, `resolve_facility_name_to_graph_node`).
- **Landmarks** and **“nearby within X m”** in `turn_by_turn.py` and `navigation_knowledge.py`.

### 4.3 Gate resolution policy

- **`backend/app/data/mumbai_t2_gate_segregation.json`** drives **heuristic** mapping from free text (domestic vs international keywords, level phrases) and numeric gates to a **routable** graph goal — explicitly **not** a substitute for FIDS (`gate_segregation.py`).

---

## 5. Distance, bearing, angles, and walking time

Implemented in **`backend/app/services/distance_calculator.py`**.

### 5.1 Normalized coordinates → meters

- Node and CSV coordinates are treated as **0–100 normalized** positions on a notional **900 m × 900 m** terminal envelope (`TERMINAL_WIDTH_METERS`, `TERMINAL_HEIGHT_METERS`).
- **Segment length**: Euclidean distance after scaling Δx and Δy independently:
  - `dx_m = (x2 - x1) / 100 * 900`, same for y, then `sqrt(dx_m² + dy_m²)`.

### 5.2 Bearings and turns

- **`calculate_bearing`**: `atan2(dx, dy_inverted)` so that compass bearing **0° = North**, **90° = East**, matching the “y increases downward” map convention.
- **`bearing_to_simple_direction` / `bearing_to_direction`**: Human-readable sectors (16-way or simplified ahead/left/right).
- **`calculate_turn_angle`**: Difference between successive segment bearings, normalized to **−180…180°** (negative = left turn), mapped to phrases (`continue straight`, `slight right`, `turn right`, `sharp turn`, etc.).

### 5.3 Walking time estimate

- **`estimate_walking_time`**: `distance / 1.2 m/s`, rounded up to whole minutes (minimum 1).

### 5.4 Turn-by-turn output shape

`generate_turn_by_turn_directions` (`turn_by_turn.py`) emits steps with **`distance_meters`**, **`bearing_degrees`**, **`turn_angle_degrees`**, **`direction`**, **`time_minutes`**, cumulative distance/time, and **`nearby_landmarks`** (shops/facilities within 50 m of segment endpoints by default).

---

## 6. Route enrichment and “knowledge” on paths

**`NavigationKnowledgeIntegrator`** (`navigation_knowledge.py`):

- Calls **`build_route_payload`** from `navigation_service.py` for the core route.
- **`enrich_node_with_context`**: For a graph node, finds facilities/shops on the **same floor** within **100 m** (using `normalized_to_meters`), sorted by distance; attaches **`distance_meters`** / **`distance_formatted`**.
- **`get_contextual_directions`**: Adds **`start_context`**, **`goal_context`**, and optional **`knowledge_base_context`** (top lexical chunks from Layer A if `user_query` is set).

**`goal_from_rag_snippets`** (`navigation_service.py`): When the user picks a venue from RAG without a graph ID, the code can infer a **quadrant** (NW/NE/SW/SE) from snippet text and map to fixed food/retail **hub nodes** (`t2_nw_fb`, `t2_ne_dutyfree`, etc.), or choose the hub **closest in graph travel time** from the start.

---

## 7. Flights, catalogs, and notification timing

### 7.1 Flight records in the compiled KB

- **`data/mock/flights.json`** is the source for **`data/airport/flights.json`** when the repository compiles (realistic schema: `flight_id`, `airline`, `type`, `terminal`, `gate`, `timings`, `status`, provenance fields). If the mock file were empty, a single **placeholder** `TBD_FLIGHT_FEED` record is emitted.

### 7.2 Orchestrator flight catalog

- **`backend/app/data/mumbai_t2_catalog.json`**: Labeled as a **mock hackathon** catalog. Includes flights with **`boarding_time`**, **`departure_time`**, **`gate_node_id`**, plus optional **`food_outlets`** / **`shops_dutyfree`** sections for demos.
- **`_load_flight_catalog()`** in `orchestrator.py` normalizes both this packaged format and **`data/airport/flights.json`** into a common list with `flight_number`, `boarding_time`, `departure_time`, `terminal`, `gate_display`.

### 7.3 User-specific flight context

- **`flight_storage_service.py`** persists per-user **`flight_number`**, **`boarding_time`**, **`departure_time`**, **`terminal`**, **`gate`** via **`StateManager`** (backed by `backend/app/data/users.json`).
- Boarding pass OCR (`simple_ocr_service.py` / API) extracts fields such as **`boarding_time`** into user context — **not** a static KB file, but it **feeds the same timing logic**.

### 7.4 Time nudges (orchestrator + scheduler)

**`_build_time_nudges`** (`orchestrator.py`) and **`_compute_nudge_minutes_for_flight`** (`alert_scheduler.py`) share the same structure:

1. Parse boarding and departure times to **minutes since midnight**.
2. **Fill missing values**: if only departure known, boarding ≈ departure − **45 min**; if only boarding known, departure ≈ boarding + **45 min**; if both missing, degenerate defaults.
3. Emit scheduled **events**:
   - **Head to security** at `departure_time − 120` minutes
   - **Go to gate** at `boarding_time − 45` minutes  
   - **Final call** at `boarding_time − 10` minutes  

The **alert scheduler** polls **`get_all_active_flights()`** every **60 seconds**, compares **local clock** to those thresholds, appends lines to **`backend/app/data/alerts.log`**, and records labels in **`alerts_sent`** on the user context to avoid duplicates.

---

## 8. International travel documents

- **`TravelDocumentService`** (`travel_document_service.py`) loads:
  - **`backend/app/data/travel_documents.json`** — per-country **`region`**, **`documents_required`**, **`notes`**.
  - **`backend/app/data/city_country_mapping.json`** — maps city names to countries.
- **Processing**: Regex-based **`extract_destination`**, **`map_to_country`**, then lookup. If no row exists, **regional fallback rules** (Schengen, Asia, North America, etc.) or a **generic default checklist** apply; responses flag **`fallback_used`**.

This is a **static rule-based KB**, separate from airport POI data.

---

## 9. Supplementary scraped / static assets

| Asset | Origin | Wired into runtime? |
| --- | --- | --- |
| **`data/raw/airport_services_detailed.json`** | Script `scripts/scrape_csmia_airport_services.py` (CSMIA Airport Services API + HTML cards) | **Not referenced** by backend imports — treat as **staging / future ingestion** unless you add a loader |
| **`backend/app/data/csmia_information_desk_t2_source.json`** | Official copy for special-assistance / information desk intents (`special_assistance_intents.py`) | Used for **intent text**, not the compiled `places.json` |
| **`backend/app/data/congestion_overlay.json`** | Optional overlay for congestion module | Used if present |
| **`docs/knowledge_base_implementation.md`** | Human overview of Layer A | Documentation only |

---

## 10. Quick mental model

1. **Recommendations / lexical KB context** → `data/raw` → compiled **`places`** + **`knowledge_chunks`**.
2. **Semantic RAG over structured airport JSON** → **`airport_data.json`** + Chroma.
3. **Walking directions** → **graph** + **CSV overlays** + **distance/bearing math** + optional **congestion**.
4. **Where is Starbucks / restroom** by name → CSV **`name_display`** / **`name_normalized`** → **`graph_node_id`** → pathfinding.
5. **Flight reminders** → stored user times + **fixed offset rules** + **alert scheduler**.
6. **Visa/passport questions** → **`travel_documents.json`** + city map + fallbacks.

If you add new knowledge, match it to the layer it belongs to (compiled place seed, RAG JSON section, graph/CSV POI, or travel JSON) so the correct loader and retrieval path pick it up.
