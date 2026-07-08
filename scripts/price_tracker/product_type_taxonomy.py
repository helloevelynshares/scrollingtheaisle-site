"""Classify weekly ad offer text into product-type buckets for canonical match checks."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Ordered: more specific types first when multiple could match.
PRODUCT_TYPE_PATTERNS: dict[str, tuple[str, ...]] = {
    # Salmon
    "smoked_salmon": (
        r"smoked\s+salmon",
        r"nova\s+salmon",
        r"\bnova\b",
        r"\blox\b",
        r"togarashi",
        r"gravlax",
        r"cured\s+salmon",
        r"salmon\s+(?:jerky|spread|dip)",
        r"(?:acme|echo\s+falls).{0,30}salmon",
        r"salmon.{0,20}\b[234]\s*oz\b",
    ),
    "canned_salmon": (
        r"canned\s+salmon",
        r"salmon\s+pouch",
        r"salmon\s+packet",
    ),
    "salmon_spread_or_dip": (
        r"salmon\s+spread",
        r"salmon\s+dip",
    ),
    "frozen_salmon": (
        r"frozen\s+salmon",
    ),
    "fresh_salmon_fillets": (
        r"fresh\s+(?:atlantic\s+)?salmon",
        r"atlantic\s+salmon\s+fillet",
        r"salmon\s+fillet",
        r"salmon\s+fillets",
        r"salmon\s+portion",
        r"salmon\s+whole\s+fillet",
        r"farm\s+raised.{0,20}salmon",
        r"salmon.{0,20}(?:per\s+lb|\blb\b)",
    ),
    # Soda
    "2_liter_bottle": (
        r"2\s*[- ]?liter",
        r"2\s*l\b",
        r"1\.25\s*liter",
        r"1\s*liter",
    ),
    "single_bottle": (
        r"20\s*oz",
        r"single\s+bottle",
        r"\b1\s*btl\b",
    ),
    "8_pack_bottles": (
        r"8\s*[- ]?pack.{0,20}bottle",
        r"6\s*[- ]?pack.{0,20}bottle",
    ),
    "12_pack_cans": (
        r"12\s*[- ]?pack",
        r"12\s*pk",
        r"12\s*ct",
        r"12\s*[- ]?count",
        r"12\s*fl\s*oz\s*cans?",
    ),
    # Ice cream
    "bars_or_novelties": (
        r"\bbars?\b",
        r"cones?",
        r"novelties",
        r"\b4\s*ct\b",
        r"\b3\s*ct\b",
    ),
    "tub": (
        r"\btub\b",
        r"1\.5\s*qt",
        r"48\s*oz",
    ),
    "pint": (
        r"\bpint\b",
        # "14 oz" is ambiguous (ice cream pint vs cracker box) — require an ice
        # cream / pint context so it does not swallow snack-cracker sizes.
        r"14\s*oz.{0,20}(?:ice\s+cream|pint)",
        r"(?:ice\s+cream|pint).{0,20}14\s*oz",
        r"16\s*oz.{0,20}ice\s+cream",
    ),
    "multipack": (
        r"multi\s*pack",
        r"\b4\s*pack\b",
    ),
    # Butter
    "butter_spread": (
        r"butter\s+spread",
        r"spreadable",
        r"\bspread\b.{0,20}butter",
        r"13\s*to\s*15",
        r"13-15",
        r"\btub\b",
        r"whipped\s+butter",
    ),
    "plant_based_spread": (
        r"plant[\s-]based",
        r"vegan\s+butter",
        r"margarine",
    ),
    "butter_sticks": (
        r"butter.{0,20}16",
        r"16\s*oz.{0,20}butter",
        r"butter\s+quarters?",
        r"butter\s+sticks?",
        r"1\s*lb\s+butter",
    ),
    # Crackers / cookies
    "ritz_crackers": (r"\britz\b",),
    "chips_ahoy": (r"chips\s*ahoy",),
    "oreo": (r"\boreo\b",),
    "wheat_thins": (r"wheat\s+thins",),
    "triscuits": (r"triscuit",),
    "chicken_in_a_biskit": (r"chicken\s+in\s+a\s+biskit",),
    # Nabisco single-serve / multipack snack packs — NOT family-size boxes.
    "single_serve_snack_multipack": (
        r"single\s+serve",
        r"snack\s+pack",
        r"snack\s+packs",
        r"mini\s+pack",
        r"\b\d{1,2}\s*[- ]?pack\b.{0,20}(?:snack|cracker|cookie)",
        r"(?:snack|cracker|cookie).{0,20}\b\d{1,2}\s*[- ]?pack\b",
        r"\b10\s*[- ]?(?:pack|count)\b.{0,20}(?:snack|cracker|cookie|nabisco)",
        r"(?:snack|cracker|cookie|nabisco).{0,20}\b10\s*[- ]?(?:pack|count)\b",
    ),
    # Family-size Nabisco snack cracker boxes (Wheat Thins / Triscuit /
    # Chicken in a Biskit). Requires both a "family size" signal and the
    # "snack crackers" wording so bare "Nabisco snack crackers" stays generic.
    "family_size_snack_crackers": (
        r"family\s+size.{0,20}snack\s+crackers",
        r"snack\s+crackers.{0,20}family\s+size",
    ),
    "generic_nabisco_block": (
        r"nabisco",
        r"snack\s+crackers",
        r"sandwich\s+cookies",
    ),
    # Produce
    "berries_6oz_clamshell": (
        r"(?:blueberr|raspberr|blackberr).{0,20}6\s*oz",
        r"berries?\s+6\s*oz",
    ),
    "strawberries_clamshell": (r"strawberr",),
    "berries_large_pack": (r"(?:blueberr|raspberr|blackberr).{0,20}(?:18|24)\s*oz",),
    # Eggs
    "egg_whites_liquid": (
        r"egg\s+whites?",
        r"liquid\s+eggs?",
        r"egg\s+beaters",
    ),
    "eggs_dozen": (
        r"\beggs?\b",
        r"dozen",
        r"\b12\s*ct\b",
        r"\b18\s*ct\b",
        r"\b24\s*ct\b",
    ),
    # Chips
    "party_size": (r"party\s+size",),
    "kettle_cooked": (r"kettle\s+cooked",),
    "regular_chip_bag": (
        r"lay'?s",
        r"doritos",
        r"cheetos",
        r"ruffles",
        r"tostitos",
    ),
}


@dataclass(frozen=True)
class ProductTypeClassification:
    primary_type: str | None
    all_types: tuple[str, ...]


def classify_product_type(text: str) -> ProductTypeClassification:
    lowered = (text or "").lower()
    matched: list[str] = []
    for product_type, patterns in PRODUCT_TYPE_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            matched.append(product_type)
    primary = matched[0] if matched else None
    return ProductTypeClassification(primary_type=primary, all_types=tuple(matched))


def extract_unit_hint(text: str, row: dict[str, str] | None = None) -> str | None:
    lowered = (text or "").lower()
    if row:
        unit = (row.get("package_unit") or row.get("price_basis") or "").strip().lower()
        if unit == "per_lb":
            return "lb"
        if unit:
            return unit
    if re.search(r"\bper\s+lb\b|\blb\b", lowered):
        return "lb"
    if re.search(r"\beach\b|\bct\b|\bcount\b", lowered):
        return "each"
    if re.search(r"\boz\b", lowered):
        return "oz"
    return None
