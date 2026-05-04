"""
Map casual food / drink phrasing ("I want a sandwich", "craving pizza") to shop rows in
``shops_t2_l02.csv`` via ``name_normalized`` hints, so ``resolve_shop_name_to_graph_node`` can
pick a routable ``t2_*`` anchor (nearest outlet wins in CSV matcher tie-break).

Rules use word boundaries where possible to avoid false positives. Brands must match CSV
``name_normalized`` tokens (underscores).

**Kinds of keywords worth adding over time** (extend ``_CRAVING_RULES_RAW``):

1. **Conversational / vague** — ``quick bite``, ``grab a bite``, ``something to eat``, ``light meal``,
   ``snack before flight``, ``food near me``, ``eat before boarding``.
2. **Typos & voice** — ``sanwich``, ``coffe``, ``burge``, ``piza``, ``dosha`` (common ASR errors).
3. **Hinglish / local English** — ``khana``, ``chai pakoda``, ``vada pav``, ``misal``, ``thali``,
   ``meetha``, ``namkeen``, ``jaldi kuch khana``.
4. **Diet / restrictions** — ``halal``, ``jain``, ``no onion garlic``, ``gluten free``, ``vegan meal``,
   ``keto``, ``sugar free dessert``.
5. **Time-of-day** — ``breakfast``, ``midnight snack``, ``late night food``, ``pre-flight meal``.
6. **Kids / combos** — ``kids meal``, ``combo meal``, ``sharing box``.
7. **Cuisine labels** — ``indo chinese``, ``continental``, ``street food``, ``mughlai``, ``chettinad``.
8. **Single dishes not yet covered** — map to the closest outlet category in your CSV (e.g. new QSR).
9. **Brand nicknames** — ``mcds``, ``bk``, ``sbux`` (verify against false positives).
10. **“Where / I need” variants** — handled in ``orchestrator._resolve_destination``; cravings here are
    the **food noun** fragment only.

When you add a new outlet to ``shops_t2_l02.csv``, add a regex row + tuple of ``name_normalized`` hints.
"""

from __future__ import annotations

import re
from functools import lru_cache

# (regex on full lowercased user fragment, ordered shop name_normalized hints — first CSV match wins)
_CRAVING_RULES_RAW: tuple[tuple[str, tuple[str, ...]], ...] = (
    # —— Sandwiches / subs ——
    (
        r"\b(sandwich|sandwiches|sub\b|subs\b|footlong|submarine\s+sandwich|hoagie|grinder|"
        r"club\s+sandwich|cold\s+cut|deli\s+sandwich|panini|baguette\s+sandwich)\b",
        ("subway",),
    ),
    # —— Burgers / American fast ——
    (
        r"\b(burger|burgers|cheeseburger|veggie\s+burger|fries|french\s+fries|"
        r"big\s*mac|mcnugget|mcflurry|happy\s+meal|filet[\s-]*o[\s-]*fish|kids\s+meal)\b",
        ("mcdonald_s", "burger_king", "good_flippin_burgers"),
    ),
    (r"\b(whopper|impossible\s+burger)\b", ("burger_king", "mcdonald_s")),
    (r"\b(mcds|mickey\s*d'?s?|golden\s+arches)\b", ("mcdonald_s",)),
    (r"\b(bk|burger\s+king)\b", ("burger_king", "mcdonald_s")),
    (r"\b(sbux|starbucks)\b", ("starbucks",)),
    # —— Pizza / Italian quick ——
    (
        r"\b(pizza|pizzas|slice\s+of\s+pizza|pepperoni|margherita|cheese\s+pizza|"
        r"deep\s+dish|calzone|garlic\s+bread)\b",
        ("pizza_hut", "domino_s", "donna_italia"),
    ),
    (r"\b(pasta|spaghetti|lasagne|lasagna|penne|alfredo)\b", ("donna_italia", "pizza_hut")),
    # —— Fried chicken ——
    (
        r"\b(fried\s+chicken|chicken\s+bucket|chicken\s+wings|hot\s+wings|"
        r"popcorn\s+chicken|zinger|bucket\s+meal)\b",
        ("kfc", "joshh"),
    ),
    (r"\b(kfc|kentucky)\b", ("kfc",)),
    # —— Coffee / café drinks ——
    (
        r"\b(coffee|espresso|latte|cappuccino|americano|macchiato|frappuccino|frappe|"
        r"cold\s+brew|mocha|flat\s+white|affogato)\b",
        ("starbucks", "costa_coffee", "coffee_bean_tea_leaf_cbtl", "cafeccino", "coffee_more"),
    ),
    (r"\b(frappuccino)\b", ("starbucks",)),
    (r"\b(costa)\b", ("costa_coffee",)),
    (r"\b(cbtl|coffee\s+bean)\b", ("coffee_bean_tea_leaf_cbtl",)),
    # —— Tea / chai ——
    (
        r"\b(chai|cutting\s+chai|masala\s+chai|ginger\s+tea|kulhad|irani\s+chai)\b",
        ("chaipoint", "madras_coffee_house", "cafelicious"),
    ),
    (r"\b(bubble\s+tea|boba|pearl\s+milk\s+tea)\b", ("chaipoint", "starbucks", "costa_coffee")),
    # —— Ice cream / dessert cold ——
    (
        r"\b(ice\s*cream|icecream|gelato|sundae|milkshake|thickshake|"
        r"scoops|popsicle|kulfi)\b",
        ("baskin_robbins", "amul_ice_cream_lounge", "naturals"),
    ),
    (r"\b(amul\s+ice)\b", ("amul_ice_cream_lounge",)),
    (r"\b(falooda|faluda|rabri)\b", ("haldirams", "haldiram_s", "kailash_parbat")),
    # —— South Indian breakfast / meals ——
    (
        r"\b(dosa|dosas|idli|idlis|vada|vadas|uttapam|sambar|rassam|rasam|"
        r"medu\s+vada|masala\s+dosa|rava\s+dosa|mysore\s+dosa)\b",
        ("dosa_plaza", "idli_com", "balaji_andhra_bhojanalaya", "kailash_parbat"),
    ),
    (r"\b(chettinad|andhra\s+meal|south\s+indian\s+thali)\b", ("balaji_andhra_bhojanalaya", "amreli", "dosa_plaza")),
    # —— North Indian / curry / thali ——
    (
        r"\b(biryani|biryanies|butter\s+chicken|chicken\s+tikka|tikka\s+masala|"
        r"paneer|dal\s+makhani|naan|roti|kulcha|paratha|thali|veg\s+thali|"
        r"chhole|chole|rajma|kadhi|korma|kebab|seekh\s+kebab|mughlai|hyderabadi)\b",
        ("moti_mahal", "haldiram_s", "haldirams", "curry_kitchen", "kailash_parbat", "dosa_plaza"),
    ),
    (r"\b(naan|butter\s+naan|garlic\s+naan)\b", ("moti_mahal", "haldiram_s", "curry_kitchen")),
    (r"\b(masala\s+dabba|indian\s+thali)\b", ("masala_twist", "amreli", "haldiram_s")),
    # —— Street snacks / chaat / Indian quick ——
    (
        r"\b(chaat|pani\s+puri|gol\s+gappa|bhel|sev\s+puri|samosa|kachori|"
        r"pav\s+bhaji|vada\s+pav|misal|pakora|pakoda|bhajiya)\b",
        ("haldirams", "haldiram_s", "jumbo_king", "naashto", "chitale_bandhu"),
    ),
    # —— Sweets / mithai ——
    (
        r"\b(sweet|sweets|mithai|ladoo|laddu|jalebi|barfi|peda|soan\s+papdi|"
        r"rasgulla|gulab\s+jamun|modak)\b",
        ("haldirams", "haldiram_s", "chitale_bandhu", "lal_sweets", "bikaji", "gourmet_baklava"),
    ),
    # —— Bakery / pastry / cake / donuts ——
    (
        r"\b(pastry|pastries|croissant|danish|muffin|cupcake|cake|brownie|"
        r"cookie|cookies|donut|doughnut|bakery|cheesecake)\b",
        ("mad_over_donuts", "baker_street", "flurys", "smoor"),
    ),
    (r"\b(cheese\s+toast|grilled\s+cheese)\b", ("foody_s", "flurys", "baker_street")),
    # —— Mexican / wrap ——
    (
        r"\b(burrito|burritos|taco|tacos|quesadilla|nachos|guacamole|salsa|"
        r"mexican\s+food|tex[\s-]*mex)\b",
        ("new_york_burrito_company", "burger_taco_co"),
    ),
    (r"\b(hot\s+dog|corn\s+dog|frankfurter)\b", ("jumbo_king", "good_flippin_burgers", "burger_king")),
    # —— Asian / noodles ——
    (r"\b(noodles|ramen|chow\s+mein|hakka|manchurian|fried\s+rice|dim\s+sum|sushi)\b", ("asia_7",)),
    (r"\b(indo[\s-]*chinese|indochinese|schezwan|schezuan|gobi\s+manchurian)\b", ("asia_7", "fresco")),
    # —— Middle Eastern ——
    (r"\b(falafel|shawarma|hummus|mezze|kebab\s+wrap)\b", ("falafel_express",)),
    # —— Salad / light meal ——
    (r"\b(salad|salads|caesar\s+salad|greens|healthy\s+bowl)\b", ("all_good_deli", "subway")),
    # —— Juice / fresh juice ——
    (r"\b(juice|juices|smoothie|smoothies|fresh\s+juice|detox\s+juice)\b", ("squeeze_juice",)),
    # —— Breakfast / all-day Indian light ——
    (r"\b(breakfast|upma|poha|paratha\s+breakfast|continental\s+breakfast)\b", ("naashto", "flurys")),
    (r"\b(continental\s+food|continental\s+meal)\b", ("flurys", "amreli", "all_good_deli")),
    # —— Liquor / duty ——
    (
        r"\b(wine|wines|beer|beers|whisky|whiskey|vodka|rum|gin|"
        r"liquor|spirits|champagne|prosecco)\b",
        ("living_liquidz",),
    ),
    # —— Vegan / conscious / diet ——
    (r"\b(vegan|plant[\s-]*based|jain\s+food|satvik|no\s+onion\s+no\s+garlic)\b", ("mitti_caf", "isha_life", "dosa_plaza")),
    (
        r"\b(halal\s+food|halal\s+meal|kosher|gluten[\s-]*free|no\s+gluten|dairy[\s-]*free|"
        r"lactose\s+free|sugar[\s-]*free\s+dessert|keto\s+meal|low\s+carb)\b",
        ("mitti_caf", "all_good_deli", "subway"),
    ),
    # —— Generic spicy / Indian ——
    (r"\b(spicy\s+food|indian\s+food|desi\s+khana|curry|rice\s+and\s+curry|street\s+food)\b", ("haldiram_s", "moti_mahal", "foody_s")),
    # —— Rolls / frankie ——
    (r"\b(kathi\s+roll|kati\s+roll|frankie|shawarma\s+roll|egg\s+roll)\b", ("falafel_express", "jumbo_king")),
    # —— Waffle / crepe ——
    (r"\b(waffle|waffles|crepe|crêpe|pancakes)\b", ("flurys", "starbucks", "costa_coffee")),
    # —— Soup ——
    (r"\b(soup|soup\s+of\s+the\s+day|tomato\s+soup|minestrone)\b", ("all_good_deli", "flurys")),
    # —— Grill / BBQ ——
    (r"\b(bbq|barbecue|grilled\s+chicken|tandoori)\b", ("moti_mahal", "kfc", "good_flippin_burgers")),
    # —— Typos / ASR ——
    (r"\b(sanwich|sandwhich|samwich)\b", ("subway",)),
    (r"\b(coffe|expresso|expressso|capuccino)\b", ("starbucks", "costa_coffee")),
    (r"\b(burge|cheeseburge|piza|peeza)\b", ("mcdonald_s", "burger_king", "pizza_hut")),
    (r"\b(dosha|iddli)\b", ("dosa_plaza", "idli_com")),
    # —— Conversational hunger ——
    (
        r"\b(quick\s+bite|grab\s+a\s+bite|something\s+to\s+eat|something\s+small\s+to\s+eat|"
        r"light\s+meal|small\s+meal|snack\s+before\s+flight|eat\s+before\s+boarding|"
        r"pre[\s-]*flight\s+meal|inflight\s+snack|need\s+food|need\s+something\s+to\s+eat)\b",
        ("foody_s", "boarding_bite", "naashto", "all_good_deli"),
    ),
    (r"\b(midnight\s+snack|late\s+night\s+food|open\s+24\s*hours?\s+food)\b", ("foody_s", "naashto", "cafe_2_0")),
    (r"\b(food\s+court|foodcourt|quick\s+service|qsr)\b", ("foody_s", "asia_7", "dosa_plaza")),
    # —— Hinglish ——
    (
        r"\b(khana|khaana|kuch\s+khana|jaldi\s+khana|chai\s+and\s+snack|chai\s+snack|"
        r"meetha|mithai\s+shop|namkeen|tikki|tikka\s+roll)\b",
        ("haldirams", "chaipoint", "naashto", "chitale_bandhu"),
    ),
    (r"\b(momos?|dimsums?|gyoza|pot\s+stickers)\b", ("asia_7", "falafel_express")),
    (r"\b(pho|ramen|udon|soba|pad\s+thai|tom\s+yum)\b", ("asia_7",)),
    (r"\b(poke\s+bowl|sushi\s+bowl|bibimbap)\b", ("asia_7", "all_good_deli")),
    # —— Small plates / bar snacks ——
    (r"\b(tapas|small\s+plates|bar\s+snacks?|finger\s+food)\b", ("bar_fly", "craverie", "foody_s")),
)


@lru_cache(maxsize=1)
def _compiled_rules() -> tuple[tuple[re.Pattern[str], tuple[str, ...]], ...]:
    out: list[tuple[re.Pattern[str], tuple[str, ...]]] = []
    for raw_pat, brands in _CRAVING_RULES_RAW:
        out.append((re.compile(raw_pat, re.I), brands))
    return tuple(out)


def iter_shop_hints_from_craving(text: str) -> list[str]:
    """
    Return ordered ``name_normalized``-style hints for ``text`` (user phrase, destination fragment,
    or full utterance). Multiple rules may match; hints are de-duplicated in rule order.
    """
    t = (text or "").strip().lower()
    if len(t) < 2:
        return []
    hints: list[str] = []
    seen: set[str] = set()
    for pat, brands in _compiled_rules():
        if not pat.search(t):
            continue
        for b in brands:
            b = b.strip().lower()
            if b and b not in seen:
                seen.add(b)
                hints.append(b)
    return hints


def craving_hints_for_queries(*parts: str | None) -> list[str]:
    """Merge hints from several message fragments (e.g. user message + destination label)."""
    merged: list[str] = []
    seen: set[str] = set()
    for p in parts:
        if not p:
            continue
        for h in iter_shop_hints_from_craving(str(p)):
            if h not in seen:
                seen.add(h)
                merged.append(h)
    return merged
