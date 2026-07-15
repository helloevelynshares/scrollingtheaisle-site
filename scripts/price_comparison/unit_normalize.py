"""Parse package sizes from Costco itemSign and compute per-unit prices."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedPackage:
    description: str
    unit_count: float
    unit_type: str
    comparable_unit: str
    confidence: str  # high | medium | low


PER_LB_RE = re.compile(r"per\s*lb", re.I)
LB_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pound)", re.I)
OZ_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:oz|ounce)", re.I)
FL_OZ_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:fl\s*oz|fluid ounce)", re.I)
COUNT_RE = re.compile(
    r"(\d+)\s*(?:count|ct|pack|pk|bars?|bags?|cans?|eggs?|each)(?:\b|\s|/|$)",
    re.I,
)
MULTI_PACK_RE = re.compile(
    r"(\d+)\s*pack\s*(\d+(?:\.\d+)?)\s*(?:oz|ounce|fl\s*oz|lb|pound)",
    re.I,
)
SLASH_PACK_RE = re.compile(
    r"(\d+)\s*/\s*(\d+(?:\.\d+)?)\s*(oz|fl\s*oz|lb|ounce|pound)",
    re.I,
)
EA_EACH_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:oz|ounce|fl\s*oz|lb|pound)\s*(?:ea|each)",
    re.I,
)
TWO_PACK_RE = re.compile(
    r"2\s*pack\s*(\d+(?:\.\d+)?)\s*(?:oz|ounce|fl\s*oz|lb|pound)",
    re.I,
)


def _normalize_unit(raw: str) -> str:
    u = raw.lower().strip()
    if u in {"oz", "ounce", "ounces"}:
        return "oz"
    if u in {"fl oz", "fluid ounce", "fluid ounces"}:
        return "fl_oz"
    if u in {"lb", "lbs", "pound", "pounds"}:
        return "lb"
    if u in {"ct", "count", "each", "ea"}:
        return "each"
    if u in {"bar", "bars"}:
        return "bar"
    if u in {"bag", "bags"}:
        return "bag"
    if u in {"can", "cans"}:
        return "can"
    if u in {"egg", "eggs"}:
        return "egg"
    return u


def parse_item_sign(item_sign: str, target_unit: str | None = None) -> ParsedPackage | None:
    text = item_sign.strip()
    lower = text.lower()

    if PER_LB_RE.search(lower):
        return ParsedPackage(text, 1.0, "lb", "lb", "high")

    m = MULTI_PACK_RE.search(lower)
    if m:
        packs = float(m.group(1))
        size = float(m.group(2))
        unit = _normalize_unit(m.group(0).split()[-1] if "oz" in m.group(0).lower() else "oz")
        if "lb" in m.group(0).lower() or "pound" in m.group(0).lower():
            unit = "lb"
        elif "fl" in m.group(0).lower():
            unit = "fl_oz"
        else:
            unit = "oz"
        return ParsedPackage(text, packs * size, unit, unit, "high")

    m = SLASH_PACK_RE.search(lower)
    if m:
        count = float(m.group(1))
        size = float(m.group(2))
        unit = _normalize_unit(m.group(3))
        if target_unit in {"each", "cup", "bar"}:
            unit = "bar" if target_unit == "bar" else "each"
            return ParsedPackage(text, count, unit, unit, "high")
        return ParsedPackage(text, count * size, unit, unit, "high")

    m = TWO_PACK_RE.search(lower)
    if m:
        size = float(m.group(1))
        unit = "oz"
        if "lb" in m.group(0).lower():
            unit = "lb"
        return ParsedPackage(text, 2 * size, unit, unit, "high")

    # "30 BARS 1.42 OUNCE EA" or "42 BARS 1.41 OUNCES EA"
    bar_match = re.search(
        r"(\d+)\s*bars?\s*(\d+(?:\.\d+)?)\s*(?:oz|ounce)",
        lower,
    )
    if bar_match:
        count = float(bar_match.group(1))
        return ParsedPackage(text, count, "bar", "bar", "high")

    # Multipack single-serve: "54 PACK 1 OUNCE EA", "20 COUNT 5.3 OUNCES EA".
    # When comparing per cup/each (yogurt cups, etc.), treat count as unit count.
    multipack_bag = re.search(
        r"(\d+)\s*(?:pack|count|ct)\s*(\d+(?:\.\d+)?)\s*(?:oz|ounce)\s*(?:ea|each)?",
        lower,
    )
    if multipack_bag:
        count = float(multipack_bag.group(1))
        if target_unit in {"each", "cup", "bar"}:
            unit = "bar" if target_unit == "bar" else "each"
            return ParsedPackage(text, count, unit, unit, "high")
        return ParsedPackage(text, count, "bag", "bag", "high")

    serve_each = re.search(
        r"(\d+)\s*(?:pack|count|ct)\b.*?\b(?:ea|each)\b",
        lower,
    )
    if serve_each and any(word in lower for word in ("variety", "mix", "multipack", "snack pack")):
        count = float(serve_each.group(1))
        if target_unit in {"each", "cup"}:
            return ParsedPackage(text, count, "each", "each", "medium")
        return ParsedPackage(text, count, "bag", "bag", "medium")

    count_only = COUNT_RE.search(lower)
    oz_only = OZ_RE.search(lower) or FL_OZ_RE.search(lower) or LB_RE.search(lower)
    ea_only = EA_EACH_RE.search(lower)

    if count_only and ea_only:
        count = float(count_only.group(1))
        unit = "each"
        if "bar" in lower:
            unit = "bar"
        elif "bag" in lower:
            unit = "bag"
        elif "can" in lower or "pk" in lower:
            unit = "can"
        elif "egg" in lower:
            unit = "egg"
        return ParsedPackage(text, count, unit, unit, "high")

    if oz_only and not count_only:
        size = float(oz_only.group(1))
        unit = "lb" if "lb" in oz_only.group(0).lower() or "pound" in oz_only.group(0).lower() else "oz"
        if "fl" in oz_only.group(0).lower():
            unit = "fl_oz"
        return ParsedPackage(text, size, unit, unit, "medium")

    if count_only:
        count = float(count_only.group(1))
        unit = "each"
        if "bar" in lower:
            unit = "bar"
        elif "bag" in lower:
            unit = "bag"
        elif "egg" in lower:
            unit = "egg"
        elif "can" in lower:
            unit = "can"
        return ParsedPackage(text, count, unit, unit, "medium")

    if target_unit:
        return ParsedPackage(text, 1.0, target_unit, target_unit, "low")

    return None


def unit_price(total_price: float, package: ParsedPackage) -> float | None:
    if package.unit_count <= 0:
        return None
    return round(total_price / package.unit_count, 4)


def units_compatible(a: str, b: str) -> bool:
    if a == b:
        return True
    pairs = {("oz", "fl_oz")}
    return (a, b) in pairs or (b, a) in pairs


def grocery_package_from_meta(
    size_label: str | None,
    quantity: float,
    unit_type: str,
) -> ParsedPackage:
    desc = size_label or f"{quantity} {unit_type}"
    return ParsedPackage(desc, quantity, unit_type, unit_type, "high")
