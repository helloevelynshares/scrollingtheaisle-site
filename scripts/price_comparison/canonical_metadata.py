"""Canonical product package metadata and Costco match rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalPackageMeta:
    canonical_id: str
    package_quantity: float
    package_unit: str
    unit_type: str
    comparable_unit: str
    comparison_group: str
    costco_include: tuple[str, ...]
    costco_exclude: tuple[str, ...] = ()
    costco_prefer: tuple[str, ...] = ()
    costco_not_expected: bool = False


CANONICAL_PACKAGES: dict[str, CanonicalPackageMeta] = {
    "strawberries": CanonicalPackageMeta(
        "strawberries", 1, "lb", "lb", "lb", "produce",
        (r"strawberr",), (r"yogurt|pretzel|shake|bar|protein",), (r"^strawberr", r"1\s*lb|2\s*lb"),
        costco_not_expected=True,
    ),
    "avocados": CanonicalPackageMeta(
        "avocados", 1, "each", "each", "each", "produce",
        (r"hass avocado", r"avocado(?!.*oil)",),
        (r"oil|chips|guacamole mix",),
        (r"^hass avocado", r"6\s*count|5\s*count"),
        costco_not_expected=True,
    ),
    "doritos_nacho_cheese": CanonicalPackageMeta(
        "doritos_nacho_cheese", 9.25, "oz", "oz", "oz", "snacks",
        (r"doritos",), (r"protein chips",), (r"nacho cheese", r"30\s*oz"),
    ),
    "cheetos_crunchy": CanonicalPackageMeta(
        "cheetos_crunchy", 8.5, "oz", "oz", "oz", "snacks",
        (r"cheetos",), (r"mac.?n.?cheese",), (r"crunchy", r"28\s*oz"),
    ),
    "coke_zero": CanonicalPackageMeta(
        "coke_zero", 12, "can", "can", "can", "beverages",
        (r"coke zero", r"coca.?cola zero",),
        (r"diet coke|sprite|pepsi",),
        (r"coke zero", r"35\s*count|32\s*count|24\s*count"),
        costco_not_expected=True,
    ),
    "chobani_greek_yogurt": CanonicalPackageMeta(
        "chobani_greek_yogurt", 32, "oz", "oz", "oz", "dairy",
        (r"chobani.*greek", r"chobani.*yogurt",),
        (r"drink|complete|flip|20g protein drink",),
        (r"plain greek", r"40\s*oz|48\s*oz|32\s*oz"),
    ),
    "cheerios": CanonicalPackageMeta(
        "cheerios", 8.9, "oz", "oz", "oz", "cereal",
        (r"cheerios",),
        (r"honey nut|apple cinnamon|protein|multigrain|family size",),
        (r"^general mills cheerios", r"2 pack"),
    ),
    "tillamook_ice_cream": CanonicalPackageMeta(
        "tillamook_ice_cream", 56, "oz", "oz", "oz", "frozen",
        (r"tillamook.*ice cream",),
        (r"cracker|cheddar|snack|cheese",),
        (r"ice cream", r"1\.?\d+\s*half gallon|half gallon"),
        costco_not_expected=True,
    ),
    "mission_tortilla_chips": CanonicalPackageMeta(
        "mission_tortilla_chips", 11, "oz", "oz", "oz", "snacks",
        (r"mission.*tortilla", r"mission.*chip",),
        (r"flour tortilla|soft taco",),
        (r"mission", r"tortilla chip"),
        costco_not_expected=True,
    ),
    "nature_valley_bars": CanonicalPackageMeta(
        "nature_valley_bars", 12, "bar", "bar", "bar", "snacks",
        (r"nature valley",),
        (r"protein|wafer|sweet.*salty",),
        (r"oats.*honey|crunchy|granola bar", r"49 bar|48 bar"),
    ),
    "fage_greek_yogurt": CanonicalPackageMeta(
        "fage_greek_yogurt", 32, "oz", "oz", "oz", "dairy",
        (r"fage",),
        (r"split cup|crossovers|drink",),
        (r"total.*plain|greek yogurt", r"48\s*oz|40\s*oz|32\s*oz"),
        costco_not_expected=True,
    ),
    "frito_lay_multipack_chips": CanonicalPackageMeta(
        "frito_lay_multipack_chips", 42, "bag", "bag", "bag", "snacks",
        (r"frito lay.*variety", r"frito lay.*mix", r"frito lay.*multipack",),
        (r"sunchips only|doritos only",),
        (r"variety.*30|variety.*54|classic mix|30 count|54 count",),
    ),
    "haagen_dazs_ice_cream": CanonicalPackageMeta(
        "haagen_dazs_ice_cream", 14, "oz", "oz", "oz", "frozen",
        (r"haagen.?dazs", r"häagen.?dazs",),
        (r"mini bar|bar",),
        (r"ice cream", r"14\s*oz|28\s*oz|48\s*oz"),
        costco_not_expected=True,
    ),
    "grapes": CanonicalPackageMeta(
        "grapes", 1, "lb", "lb", "lb", "produce",
        (r"grape",),
        (r"grapefruit|grape seed oil|grape leaves|grape tomato",),
        (r"seedless grape", r"per lb"),
        costco_not_expected=True,
    ),
    "eggs_18_count": CanonicalPackageMeta(
        "eggs_18_count", 18, "egg", "egg", "egg", "dairy",
        (r"\beggs\b", r"large eggs", r"cage free eggs",),
        (r"quail|cadbury|hershey|eggland.*6 ct|chocolate|protein shake",),
        (r"24 count|30 count|5 dozen|60 count|18 count",),
        costco_not_expected=True,
    ),
    "oreos_sandwich_cookies": CanonicalPackageMeta(
        "oreos_sandwich_cookies", 18, "oz", "oz", "oz", "snacks",
        (r"oreo",),
        (r"variety.*reeses|pillsbury|cake mix",),
        (r"oreo.*cookie|sandwich cookie|family",),
        costco_not_expected=True,
    ),
    "protein_bars": CanonicalPackageMeta(
        "protein_bars", 12, "bar", "bar", "bar", "snacks",
        (r"protein bar", r"rxbar", r"kirkland signature protein bar",),
        (r"shake|powder|drink|bites only",),
        (r"protein bar variety|chewy protein bar",),
    ),
    "kettle_brand_chips": CanonicalPackageMeta(
        "kettle_brand_chips", 8, "oz", "oz", "oz", "snacks",
        (r"kettle brand", r"kettle potato chips", r"kettle cooked",),
        (r"miss vickie|kirkland signature kettle|variety.*30 count",),
        (r"kettle brand", r"8\s*oz|13\s*oz|28\s*oz"),
    ),
}

GROCERY_FEEDS = {
    "safeway_bay_area": {
        "label": "Safeway",
        "costco_region_id": "costco_sf",
        "costco_location_slug": "san_francisco",
        "costco_store_label": "Costco San Francisco",
    },
    "vons_albertsons_socal": {
        "label": "Vons / Albertsons",
        "costco_region_id": "costco_oc",
        "costco_location_slug": "tustin",
        "costco_store_label": "Costco Tustin",
    },
}

DEFAULT_COSTCO_DATA_ROOT = "/Users/evelynchan/Documents/costco-mvp/costco_data"
