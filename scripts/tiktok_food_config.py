"""Food-only TikTok SKU selection: exclusions, lexicon, and priority weights."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Staples to drop from the old canonical-50 grocery list
NON_FOOD_QUERY_EXACT = frozenset(
    {
        "bottled water",
        "paper towels",
        "toilet paper",
        "dish soap",
        "laundry detergent",
        "shampoo",
        "toothpaste",
        "disposable diapers",
        "baby food pouches",
        "dry dog food",
        "dry cat food",
    }
)

NON_FOOD_CATEGORY_KEYWORDS = frozenset(
    {
        "household",
        "personal care",
        "pet",
        "baby",
        "cleaning",
        "hygiene",
        "paper goods",
    }
)

VIEW_PRIORITY_HIGH = 2.0  # views >= 10k
VIEW_PRIORITY_HIGHEST = 3.0  # views >= 20k
VIEW_PRIORITY_SECONDARY = 1.0  # views < 10k


@dataclass(frozen=True)
class FoodLexiconEntry:
    item_mentioned: str
    brand_guess: str
    category: str
    content_theme: str
    patterns: tuple[str, ...]
    suggested_search_query: str


def view_priority_score(views: int) -> float:
    if views >= 20_000:
        return VIEW_PRIORITY_HIGHEST
    if views >= 10_000:
        return VIEW_PRIORITY_HIGH
    return VIEW_PRIORITY_SECONDARY


# Brand / product patterns for transcript mining (food-only)
FOOD_LEXICON: tuple[FoodLexiconEntry, ...] = (
    FoodLexiconEntry(
        "Oreo cookies",
        "Oreo",
        "cookies_snacks",
        "cookies_snacks",
        (r"\boreos?\b",),
        "oreo",
    ),
    FoodLexiconEntry(
        "Oreo Cakesters",
        "Oreo",
        "cookies_snacks",
        "cookies_snacks",
        (r"\boreo\s+cakesters?\b", r"\bcakesters?\b"),
        "oreo cakesters",
    ),
    FoodLexiconEntry(
        "Nilla Wafers",
        "Nilla",
        "cookies_snacks",
        "cookies_snacks",
        (r"\bnilla\s+wafer", r"\bnilla\b"),
        "nilla wafers",
    ),
    FoodLexiconEntry(
        "Ritz crackers",
        "Ritz",
        "crackers_snacks",
        "crackers_snacks",
        (r"\britz\b",),
        "ritz crackers",
    ),
    FoodLexiconEntry(
        "Wheat Thins",
        "Wheat Thins",
        "crackers_snacks",
        "crackers_snacks",
        (r"\bwheat\s+thins?\b",),
        "wheat thins",
    ),
    FoodLexiconEntry(
        "Triscuit crackers",
        "Triscuit",
        "crackers_snacks",
        "crackers_snacks",
        (r"\btriscuit", r"\btriscuits?\b"),
        "triscuit",
    ),
    FoodLexiconEntry(
        "Chips Ahoy",
        "Chips Ahoy",
        "cookies_snacks",
        "cookies_snacks",
        (r"\bchips\s+ahoy\b",),
        "chips ahoy",
    ),
    FoodLexiconEntry(
        "Kettle Brand jalapeño chips",
        "Kettle Brand",
        "chips_snacks",
        "chips_snacks",
        (r"\bkettle\s+brand\b.*\bjalap", r"\bjalapeno\s+chips?\b"),
        "kettle brand jalapeno chips",
    ),
    FoodLexiconEntry(
        "Kettle Brand honey dijon chips",
        "Kettle Brand",
        "chips_snacks",
        "chips_snacks",
        (r"\bkettle\s+brand\b.*\bhoney\s+dijon", r"\bhoney\s+dijon\s+chips?\b"),
        "kettle brand honey dijon chips",
    ),
    FoodLexiconEntry(
        "Breyers Carb Smart ice cream",
        "Breyers",
        "ice_cream_frozen",
        "ice_cream_frozen",
        (r"\bbreyers?\b", r"\bcarb\s+smart\b"),
        "breyers carb smart vanilla",
    ),
    FoodLexiconEntry(
        "Ben & Jerry's ice cream bars",
        "Ben & Jerry's",
        "ice_cream_frozen",
        "ice_cream_frozen",
        (r"\bben\s*&?\s*jerry", r"\bben\s+and\s+jerry"),
        "ben and jerrys ice cream bars",
    ),
    FoodLexiconEntry(
        "Häagen-Dazs ice cream",
        "Häagen-Dazs",
        "ice_cream_frozen",
        "ice_cream_frozen",
        (r"\bhaagen[\s-]?dazs", r"\bhäagen[\s-]?dazs"),
        "haagen dazs vanilla bean",
    ),
    FoodLexiconEntry(
        "Baskin-Robbins ice cream",
        "Baskin-Robbins",
        "ice_cream_frozen",
        "ice_cream_frozen",
        (r"\bbaskin[\s-]?robbins",),
        "baskin robbins ice cream",
    ),
    FoodLexiconEntry(
        "Philadelphia cream cheese",
        "Philadelphia",
        "dairy",
        "dairy_spreads",
        (r"\bphiladelphia\b", r"\bwhipped\s+cream\s+cheese"),
        "philadelphia whipped cream cheese",
    ),
    FoodLexiconEntry(
        "Wonder bagels",
        "Wonder",
        "bakery",
        "bakery_bread",
        (r"\bwonder\s+bagel",),
        "wonder bagels",
    ),
    FoodLexiconEntry(
        "Wonder English muffins",
        "Wonder",
        "bakery",
        "bakery_bread",
        (r"\bwonder\s+english\s+muffin", r"\benglish\s+muffins?\b"),
        "wonder english muffins",
    ),
    FoodLexiconEntry(
        "Kerrygold butter",
        "Kerrygold",
        "dairy",
        "dairy_butter",
        (r"\bkerrygold\b",),
        "kerrygold butter",
    ),
    FoodLexiconEntry(
        "chicken breast",
        "",
        "meat_protein",
        "meat_protein",
        (r"\bboneless\s+chicken\s+breast", r"\bchicken\s+breast\b"),
        "chicken breast value pack",
    ),
    FoodLexiconEntry(
        "90% lean ground beef",
        "",
        "meat_protein",
        "meat_protein",
        (r"\b90\s*%?\s*lean\s+ground\s+beef", r"\bground\s+beef\b"),
        "90 lean ground beef",
    ),
    FoodLexiconEntry(
        "beef chuck roast",
        "",
        "meat_protein",
        "meat_protein",
        (r"\bchuck\s+roast", r"\bbeef\s+chuck"),
        "beef chuck roast",
    ),
    FoodLexiconEntry(
        "Atlantic salmon fillet",
        "",
        "meat_protein",
        "meat_protein",
        (r"\batlantic\s+salmon", r"\bsalmon\s+fillet"),
        "atlantic salmon fillet",
    ),
    FoodLexiconEntry(
        "red seedless grapes",
        "",
        "produce",
        "produce_fruit",
        (r"\bred\s+seedless\s+grapes?", r"\bseedless\s+grapes?\b"),
        "red seedless grapes",
    ),
    FoodLexiconEntry(
        "Gala apples",
        "",
        "produce",
        "produce_fruit",
        (r"\bgala\s+apple",),
        "gala apples",
    ),
    FoodLexiconEntry(
        "navel oranges",
        "",
        "produce",
        "produce_fruit",
        (r"\bnavel\s+orange",),
        "navel oranges",
    ),
    FoodLexiconEntry(
        "sweet corn",
        "",
        "produce",
        "produce_vegetables",
        (r"\bsweet\s+corn\b", r"\bcorn\s+on\s+the\s+cob"),
        "sweet corn",
    ),
    FoodLexiconEntry(
        "bell peppers",
        "",
        "produce",
        "produce_vegetables",
        (r"\bbell\s+pepper",),
        "bell peppers",
    ),
    FoodLexiconEntry(
        "ice cream",
        "",
        "ice_cream_frozen",
        "ice_cream_frozen",
        (r"\bice\s+cream\b",),
        "ice cream",
    ),
    FoodLexiconEntry(
        "cream cheese",
        "",
        "dairy",
        "dairy_spreads",
        (r"\bcream\s+cheese\b",),
        "cream cheese",
    ),
    FoodLexiconEntry(
        "butter",
        "Kerrygold",
        "dairy",
        "dairy_butter",
        (r"\bbutter\b",),
        "butter",
    ),
)

COMPILED_LEXICON: tuple[tuple[re.Pattern[str], FoodLexiconEntry], ...] = tuple(
    (re.compile(p, re.IGNORECASE), entry)
    for entry in FOOD_LEXICON
    for p in entry.patterns
)


def is_non_food_query(query: str) -> bool:
    return query.strip().lower() in NON_FOOD_QUERY_EXACT


def snippet_around(text: str, start: int, end: int, radius: int = 90) -> str:
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    snippet = text[lo:hi].replace("\n", " ")
    return " ".join(snippet.split())
