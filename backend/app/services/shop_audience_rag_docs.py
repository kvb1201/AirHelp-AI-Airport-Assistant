"""
Augment RAG index with hard-coded *semantic* text for Terminal 2 CSV shops.

These strings are not separate embedding vectors in code — they become part of
the same chunk text that ``LocalEmbedder`` embeds at index time, so queries like
“food for my elderly parents”, “avoid Chinese”, “quiet place to sit”, or
“familiar Indian vegetarian” pull better-matched outlets.

Loaded by ``load_airport_data`` after the JSON KB; re-run API / ``load_and_index``
to refresh Chroma.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.shops_loader import load_shops_t2_l02

# --- Snippets keyed by semantic tags (reused + combined per outlet) ---

_SNIPPETS: dict[str, str] = {
    "baseline": (
        "Mumbai Chhatrapati Shivaji International Airport Terminal 2 (CSIA T2) retail or F&B outlet. "
        "Use this row when matching traveler age, mobility, cuisine comfort, noise tolerance, and dietary needs."
    ),
    "senior_familiar_indian": (
        "Often a strong match for senior travelers and parents who want familiar North or South Indian flavors, "
        "vegetarian thali options, mild spice by default, and counter or quick-table service typical of Indian QSR."
    ),
    "indo_chinese_pan_asian": (
        "Indo-Chinese, pan-Asian, or wok-style menu: chili-garlic, soy, Schezwan-style sauces, noodles, rice bowls. "
        "Travelers who dislike Chinese-style or heavily seasoned Asian fast food may prefer a full-service Indian "
        "restaurant, dosa outlet, or international burger/pizza chain instead."
    ),
    "western_qsr_predictable": (
        "International quick-service brand with a predictable global menu (burgers, subs, pizza, fried chicken). "
        "Comfortable for mixed-age families, first-time flyers, and passengers who want recognizable items."
    ),
    "cafe_seated_quiet": (
        "Coffeehouse or café format with barista drinks, pastries, and usually some seating; generally calmer than "
        "a busy food court at peak hours—often easier for older adults who want to sit, rest, and sip slowly."
    ),
    "bakery_sweet_mild": (
        "Bakery, viennoiserie, donuts, or premium sweets—kid-friendly and mild; seniors watching sugar may still "
        "enjoy small portions or sugar-free options where offered."
    ),
    "indian_sweets_mithai": (
        "Indian mithai, packaged snacks, or namkeen—very familiar tastes for local and diaspora seniors; usually "
        "takeaway counters with short queues."
    ),
    "ice_cream_family": (
        "Ice cream or gelato counter—popular with children; seniors may enjoy small cups; consider mobility on "
        "slippery floors near counters."
    ),
    "juice_smoothie_light": (
        "Fresh juice or smoothie bar—lighter than a full meal; good for travelers avoiding heavy fried food."
    ),
    "middle_eastern_wrap": (
        "Middle Eastern / Lebanese-style wraps, falafel, shawarma—often halal-friendly; spice level varies; "
        "seating may be limited at peak."
    ),
    "mexican_wrap_novelty": (
        "Mexican or Tex-Mex burritos/tacos—novelty cuisine for many Indian seniors; younger travelers often seek "
        "this out more than older guests unless they already enjoy international food."
    ),
    "south_indian_breakfast": (
        "South Indian breakfast and meals—dosas, idli, vada, sambar; vegetarian-forward; familiar comfort food "
        "for many Indian seniors and usually mild spice if requested."
    ),
    "north_indian_curry": (
        "North Indian curries, breads, kebabs, or biryani—rich gravies; seniors with mild spice preference should "
        "ask for less chili; table or kiosk formats vary."
    ),
    "food_court_energy": (
        "Food-court style energy: brighter lighting, more ambient noise, and shared seating at busy times—"
        "mobility-impaired or noise-sensitive older passengers may prefer off-peak hours or a quieter café."
    ),
    "bar_evening_crowd": (
        "Bar or taproom with alcoholic beverages; music volume can rise in evenings; less ideal for travelers "
        "seeking a calm meal—pair with escort for mobility-challenged seniors."
    ),
    "veg_health_conscious": (
        "Plant-forward, salad-forward, or explicitly vegetarian / vegan-friendly positioning—useful for Jain, "
        "satvik, or health-conscious seniors avoiding heavy oils."
    ),
    "street_snack_standing": (
        "Street-snack or frankie/kathi-roll style—often eaten standing or on the go; older travelers with balance "
        "concerns may prefer a seated restaurant nearby."
    ),
    "duty_liquor_retail": (
        "Liquor or duty-free spirits retail—age-restricted purchase; not a meal venue; helpful for gifting "
        "context, not for hungry seniors unless paired with food elsewhere."
    ),
    "kids_combo_friendly": (
        "Kid-friendly combos, finger food, or bright packaging—families with young children; seniors may still "
        "enjoy familiar fried chicken or pizza here."
    ),
    "fine_casual_dining": (
        "More curated menu or chef-led casual dining than a pure kiosk—better when escorting elderly guests who "
        "want table service and clearer allergen conversations."
    ),
}

# Explicit overrides for ambiguous names (normalized keys from CSV)
_OUTLET_EXTRA: dict[str, str] = {
    "asia_7": "Primary association: pan-Asian / Indo-Chinese quick plates; explicitly mention when user wants "
    "to AVOID Chinese-style or wok-heavy meals for elderly relatives.",
    "wow_momo": "Momos and dim-sum style snacks; similar retrieval profile to Indo-Chinese—not default for seniors "
    "who want only mild Indian vegetarian.",
    "street_foods_by_punjab_grill": "Street-food presentation with Punjabi and fusion items; can be spicy—"
    "seniors preferring mild thali may choose a dedicated North Indian restaurant instead.",
    "subway": "Custom sandwiches—predictable for international travelers; seniors can choose soft bread and "
    "simple fillings to avoid tough or spicy options.",
    "mcdonald_s": "Global McDonald's menu; high familiarity for seniors traveling with grandchildren.",
    "burger_king": "Whopper-style burgers; familiar Western QSR; loud peak periods possible.",
    "kfc": "Fried chicken buckets—popular with families; grease-heavy—some older adults avoid.",
    "pizza_hut": "Pizza and garlic bread—easy to share; softer food option for denture-sensitive seniors.",
    "domino_s": "Pizza delivery-style slices—predictable Western option.",
    "starbucks": "Coffee lounge; seating; quieter than hawker-style counters for elderly rest breaks.",
    "costa_coffee": "European-style café chain; seated recovery spot.",
    "chaipoint": "Indian chai and snacks—very familiar to local seniors; usually quick counter.",
    "haldirams": "Iconic Indian sweets and savories—high familiarity for older Indian travelers.",
    "haldiram_s": "Same Haldiram's brand naming variant—sweets, chaat, packaged snacks.",
    "dosa_plaza": "Dosa specialist—vegetarian South Indian; senior-friendly default for many Indian elders.",
    "idli_com": "Idli-focused quick service—soft food, easy chewing for older adults.",
    "kailash_parbat": "North Indian vegetarian classics—often chosen for multi-generation families.",
    "moti_mahal": "North Indian curries and breads—ask for mild spice for seniors.",
    "mitti_caf": "Plant-forward / conscious eating—good match for vegan or low-oil senior requests.",
    "falafel_express": "Falafel and wraps—Middle Eastern profile; halal-friendly angle.",
    "jumbo_king": "Vada pav and Mumbai street-style—quick and economical; standing-eat culture possible.",
    "baskin_robbins": "Ice cream parlor—kids and dessert seekers.",
    "irish_house": "Irish pub format—bar noise evenings; meal plus drinks.",
    "living_liquidz": "Liquor retail—not a dining substitute for seniors needing a seated meal.",
}


def _rag_category(csv_category: str) -> str:
    """Map CSV shop category to RAG filter buckets used in ``rag_service._CATEGORY_MAP``."""
    c = (csv_category or "").strip().lower()
    if "coffee" in c:
        return "coffee_shop"
    if "bar" in c and "restaurant" in c:
        return "restaurant"
    if c in (
        "qsr",
        "quick_bites",
        "snacks",
        "confectionary",
        "sweets_/_packed_foods",
        "premium_bakery",
    ):
        return "quick_bites"
    return "shop"


def _tags_for_outlet(name_norm: str, display: str, csv_cat: str) -> list[str]:
    s = f"{name_norm} {display}".lower()
    tags: list[str] = ["baseline"]

    if csv_cat == "bar_&_restaurant" or re.search(
        r"\b(bar|taproom|pub|tavern|brew|clink|irish|heineken|hoegaarden|budweiser|black_dog|bira|cram|tikg|ultra)\b",
        s,
    ):
        tags.append("bar_evening_crowd")

    if csv_cat in ("qsr", "quick_bites", "snacks") and "bar" not in s:
        tags.append("food_court_energy")

    if re.search(
        r"asia|momo|hakka|manchur|noodle|ramen|sushi|dim|gyoza|asia|pan.?asian|wok|burrito|taco|mexican|nybc|"
        r"new_york_burrito|burger_taco",
        s,
    ):
        tags.append("indo_chinese_pan_asian")

    if re.search(
        r"mcdonald|burger_king|kfc|subway|pizza|domino|jumbo|joshh|foody|boarding|fresco|good_flippin|"
        r"wrapafella|shawarma_shack|tikg|frankie|tibbs|vaango",
        s,
    ):
        tags.append("western_qsr_predictable")

    if re.search(
        r"starbucks|costa|coffee|ccd|cafelic|third_wave|madras_coffee|coffee_more|cbtl|society_tea|chaipoint|"
        r"manis_cafe|chef_caf|cafe_2|caf_ritazza|cafeccino",
        s,
    ):
        tags.append("cafe_seated_quiet")

    if re.search(
        r"dosa|idli|kailash|balaji|andhra|south|naashto|raju_omlet|shiv_sagar|vaango|amreli|mumbai_se|mumbai_snacks",
        s,
    ):
        tags.append("south_indian_breakfast")

    if re.search(
        r"haldiram|bikaji|chitale|lal_sweets|mithai|sweet|bikaji|gourmet_baklava|baker_street|flurys|smoor|"
        r"theobroma|mad_over|donut|baskin|naturals|amul_ice|ice_cream",
        s,
    ):
        if re.search(r"baskin|amul|naturals|mad_over", s):
            tags.append("ice_cream_family")
        elif re.search(r"haldiram|bikaji|chitale|lal_sweets|mithai", s):
            tags.append("indian_sweets_mithai")
        else:
            tags.append("bakery_sweet_mild")

    if re.search(r"moti|mahal|curry_kitchen|masala_twist|zambar|ottoman|nourish|kailash|haldiram", s):
        tags.append("north_indian_curry")
    if re.search(r"donna_italia|pasta_station|messo", s):
        tags.append("fine_casual_dining")

    if re.search(r"falafel|shawarma|middle", s):
        tags.append("middle_eastern_wrap")

    if re.search(r"burrito|taco|mexican|new_york_burrito|burger_taco", s):
        tags.append("mexican_wrap_novelty")

    if re.search(r"squeeze|juice|smoothie", s):
        tags.append("juice_smoothie_light")

    if re.search(r"mitti|isha|salad|all_good|deli|health|vegan|plant", s):
        tags.append("veg_health_conscious")

    if re.search(r"wine|liquor|liquidz|black_dog|heineken|hoegaarden|budweiser|bira|taproom", s):
        tags.append("duty_liquor_retail")

    if re.search(r"mcdonald|happy|kids|pizza_hut|domino|kfc|burger_king", s):
        tags.append("kids_combo_friendly")

    if re.search(r"haldiram|dosa|idli|kailash|motim|thali|veg", s):
        tags.append("senior_familiar_indian")

    # Dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _compose_audience_text(name_norm: str, display: str, csv_cat: str) -> str:
    tags = _tags_for_outlet(name_norm, display, csv_cat)
    parts = [_SNIPPETS[t] for t in tags if t in _SNIPPETS]
    extra = _OUTLET_EXTRA.get(name_norm)
    if extra:
        parts.append(extra)
    return " ".join(parts)


def build_shop_audience_documents() -> list[dict[str, Any]]:
    """One RAG document per CSV shop row, with rich persona/cuisine text for embedding."""
    docs: list[dict[str, Any]] = []
    for row in load_shops_t2_l02():
        shop_id = str(row.get("shop_id") or "")
        display = str(row.get("name_display") or "").strip()
        norm = str(row.get("name_normalized") or "").strip()
        csv_cat = str(row.get("category") or "").strip()
        if not shop_id or not display:
            continue

        listing = str(row.get("listing_location") or row.get("near_graph_hint") or "").strip()
        floor = str(row.get("floor") or "")
        zone = str(row.get("zone") or "")
        rag_cat = _rag_category(csv_cat)

        audience = _compose_audience_text(norm, display, csv_cat)
        text = (
            f"Outlet '{display}' (internal key {norm}) at Mumbai Airport Terminal 2. "
            f"CSV category: {csv_cat}. RAG grouping for food search: {rag_cat}. "
            f"Floor {floor}, zone {zone}. Listing: {listing}. "
            f"Traveler-fit notes for chat retrieval (age, cuisine comfort, noise, mobility): {audience}"
        )

        loc_bits = [b for b in (listing, floor, zone, "Terminal 2 Mumbai") if b]
        location = " · ".join(loc_bits[:4])

        docs.append(
            {
                "text": text.strip(),
                "metadata": {
                    "category": rag_cat,
                    "location": location,
                    "name": display,
                    "id": f"csv_audience_{shop_id}",
                    "terminal": "2",
                },
            }
        )
    return docs


def merge_shop_audience_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Append CSV shop audience docs plus one global persona chunk."""
    extra = list(build_shop_audience_documents())
    persona_doc = {
        "text": (
            "AirHelp guidance — matching diners to Terminal 2 outlets by age and preference. "
            "Senior or elderly travelers often prefer familiar Indian vegetarian or mild North Indian meals, "
            "seated cafés, predictable international QSR brands, softer bakery items, and lower noise. "
            "They may wish to avoid spicy Indo-Chinese wok counters, standing-only street snacks, or loud bars "
            "in the evening. Young adults may seek novelty (Asian fusion, burritos, bubble tea). "
            "Families prioritize kids' menus, ice cream, and quick pizza or fried chicken. "
            "Passengers avoiding Chinese-style food should be steered toward Indian thali, dosa, or Western burger "
            "chains rather than pan-Asian quick service. "
            "Always confirm spice level, seating, and walking distance at the concourse."
        ),
        "metadata": {
            "category": "service",
            "location": "Terminal 2",
            "name": "Traveler age and cuisine matching (AirHelp)",
            "id": "airhelp_persona_dining_guide",
            "terminal": "2",
        },
    }
    return documents + [persona_doc] + extra
