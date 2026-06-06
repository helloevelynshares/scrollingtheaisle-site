#!/usr/bin/env python3
"""Generate weekly ad prices for the staging price tracker.

Reads Safeway flyer manifest from data/weekly_ads/ and offer rows from the
scrolling-the-aisle repo (split_offer_items.csv). Writes
src/data/weeklyAdPrices.generated.ts for import in priceTrackerV1.ts.

Usage:
  python3 scripts/generate_weekly_ad_prices.py
  SCROLLING_THE_AISLE_ROOT=/path/to/scrolling-the-aisle python3 scripts/generate_weekly_ad_prices.py
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = Path.home() / "Documents" / "scrolling-the-aisle"
DATA_ROOT = Path(os.environ.get("SCROLLING_THE_AISLE_ROOT", DEFAULT_DATA_ROOT))
MANIFEST_PATH = ROOT / "data" / "weekly_ads" / "flyer_manifest_safeway.csv"
SPLIT_ITEMS_PATH = (
    DATA_ROOT / "outputs" / "product_discovery_safeway" / "split_offer_items.csv"
)
OUTPUT_PATH = ROOT / "src" / "data" / "weeklyAdPrices.generated.ts"

TRACKER_CANONICAL_IDS = [
    "strawberries",
    "avocados",
    "doritos_nacho_cheese",
    "cheetos_crunchy",
    "coke_zero",
    "chobani_greek_yogurt",
    "cheerios",
    "tillamook_ice_cream",
    "mission_tortilla_chips",
    "nature_valley_bars",
]


@dataclass(frozen=True)
class ProductMatcher:
    canonical_id: str
    patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...] = ()
    prefer_patterns: tuple[str, ...] = ()


MATCHERS: tuple[ProductMatcher, ...] = (
    ProductMatcher(
        "strawberries",
        patterns=(r"strawberries",),
        exclude_patterns=(r"^blueberr", r"^raspberr", r"^blackberr", r"2 lb"),
        prefer_patterns=(r"^strawberries$", r"1-lb"),
    ),
    ProductMatcher(
        "avocados",
        patterns=(r"hass avocado",),
        exclude_patterns=(r"signature select.*5 ct",),
        prefer_patterns=(r"hass avocado",),
    ),
    ProductMatcher(
        "doritos_nacho_cheese",
        patterns=(r"doritos",),
        exclude_patterns=(r"or cheetos", r"cheetos or"),
        prefer_patterns=(r"^doritos$", r"doritos tortilla chips"),
    ),
    ProductMatcher(
        "cheetos_crunchy",
        patterns=(r"cheetos",),
        exclude_patterns=(r"mac.?n.? cheese", r"doritos or cheetos", r"buy 2 get 2"),
        prefer_patterns=(r"cheetos, tostitos, fritos", r"cheetos cheese flavored crunchy"),
    ),
    ProductMatcher(
        "coke_zero",
        patterns=(r"coke zero", r"coca-cola zero", r"zero sugar soda"),
        prefer_patterns=(r"coke zero", r"coca-cola zero"),
    ),
    ProductMatcher(
        "chobani_greek_yogurt",
        patterns=(r"chobani greek",),
        exclude_patterns=(r"zero sugar yogurt", r"chobani complete"),
        prefer_patterns=(r"chobani greek, less sugar", r"chobani greek yogurt"),
    ),
    ProductMatcher(
        "cheerios",
        patterns=(r"cheerios",),
        exclude_patterns=(
            r"honey nut",
            r"cinnamon",
            r"protein",
            r"family size",
            r"multi grain",
            r"apple cinnamon",
        ),
        prefer_patterns=(r"general mills cheerios", r"^cheerios$"),
    ),
    ProductMatcher(
        "tillamook_ice_cream",
        patterns=(r"tillamook ice cream",),
        prefer_patterns=(r"tillamook ice cream",),
    ),
    ProductMatcher(
        "mission_tortilla_chips",
        patterns=(r"mission tortilla chips",),
        prefer_patterns=(r"mission tortilla chips",),
    ),
    ProductMatcher(
        "nature_valley_bars",
        patterns=(r"nature valley bars",),
        exclude_patterns=(r"pop-tarts",),
        prefer_patterns=(r"nature valley bars",),
    ),
)


def load_manifest() -> list[dict[str, str]]:
    with MANIFEST_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_split_items() -> list[dict[str, str]]:
    if not SPLIT_ITEMS_PATH.is_file():
        raise FileNotFoundError(
            f"Missing split offer items at {SPLIT_ITEMS_PATH}. "
            "Set SCROLLING_THE_AISLE_ROOT to the scrolling-the-aisle repo."
        )
    with SPLIT_ITEMS_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def split_text(row: dict[str, str]) -> str:
    return (row.get("split_product_text") or row.get("raw_offer_text") or "").lower()


def row_text(row: dict[str, str]) -> str:
    return " ".join(
        filter(
            None,
            [
                row.get("split_product_text"),
                row.get("raw_offer_text"),
                row.get("promo_text"),
            ],
        )
    ).lower()


def matches(row: dict[str, str], matcher: ProductMatcher) -> bool:
    text = split_text(row)
    if not any(re.search(pattern, text) for pattern in matcher.patterns):
        return False
    return not any(re.search(pattern, text) for pattern in matcher.exclude_patterns)


def parse_price(value: str | None) -> float | None:
    if not value or value in {"$", ""}:
        return None
    cleaned = value.replace("$", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_unit_price(row: dict[str, str]) -> float | None:
    price = parse_price(row.get("advertised_price"))
    if price is None:
        return None

    basis = (row.get("price_basis") or "").lower()
    promo = (row.get("promo_text") or row.get("raw_offer_text") or "").lower()
    unit = (row.get("package_unit") or "").lower()

    if basis != "multi_buy":
        return round(price, 2)

    # "When you buy 3" / "buy 3" — advertised price is already per unit.
    if re.search(r"(when you )?buy\s+\d+", promo):
        return round(price, 2)

    count_match = re.search(r"(\d+)\s*(?:for|/)\s*\$?\s*(\d+(?:\.\d+)?)", promo)
    if count_match:
        count = float(count_match.group(1))
        total = float(count_match.group(2))
        if count > 0:
            return round(total / count, 2)

    size_min = row.get("package_size_min") or ""
    size_max = row.get("package_size_max") or ""
    size = size_min or size_max
    if size and unit in {"", "count", "ct", "each"}:
        try:
            count = float(size)
            if count > 1:
                return round(price / count, 2)
        except ValueError:
            pass

    if "2 for" in promo and price > 0:
        return round(price / 2, 2)

    return round(price, 2)


def preference_score(row: dict[str, str], matcher: ProductMatcher) -> int:
    text = split_text(row)
    full = row_text(row)
    score = 0
    for index, pattern in enumerate(matcher.prefer_patterns):
        if re.search(pattern, text) or re.search(pattern, full):
            score = max(score, (len(matcher.prefer_patterns) - index) * 10)
    price = normalize_unit_price(row)
    if price is not None:
        score += 1
    return score


def match_confidence(row: dict[str, str], matcher: ProductMatcher) -> str | None:
    if normalize_unit_price(row) is None:
        return None

    text = split_text(row)
    full = row_text(row)

    if re.search(r",|\sor\s", text):
        confidence = "medium"
    elif any(re.search(pattern, text) for pattern in matcher.prefer_patterns):
        confidence = "high"
    elif matches(row, matcher):
        confidence = "medium"
    else:
        confidence = "low"

    if matcher.canonical_id == "strawberries" and re.search(r"large pack|2 lb", full):
        confidence = "medium"
    if matcher.canonical_id == "chobani_greek_yogurt":
        price = normalize_unit_price(row)
        if price is not None and price < 3:
            confidence = "medium"
        elif re.search(r"5\.3|4-5\.3|cup", full):
            confidence = "medium"
    if matcher.canonical_id == "tillamook_ice_cream" and re.search(r"48-oz", full):
        confidence = "medium"

    return confidence


def pick_best_row(
    rows: list[dict[str, str]], matcher: ProductMatcher
) -> dict[str, str] | None:
    candidates = [row for row in rows if matches(row, matcher)]
    if not candidates:
        return None
    return max(candidates, key=lambda row: preference_score(row, matcher))


def format_week_label(week_start: str, week_end: str) -> str:
    start = week_start[5:].replace("-", "/")
    end = week_end[5:].replace("-", "/")
    return f"Safeway weekly ad {start}–{end}"


def build_prices(
    manifest: list[dict[str, str]], split_items: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, dict[str, dict[str, object | None]]]]:
    weeks: list[dict[str, str]] = []
    prices: dict[str, dict[str, dict[str, object | None]]] = {
        canonical_id: {} for canonical_id in TRACKER_CANONICAL_IDS
    }

    for entry in sorted(manifest, key=lambda row: row["week_start"]):
        week_start = entry["week_start"]
        week_end = entry["week_end"]
        source_file = entry["source_file"]
        week_rows = [row for row in split_items if row["week_start"] == week_start]

        weeks.append(
            {
                "weekStart": week_start,
                "weekEnd": week_end,
                "sourceFile": source_file,
                "sourceLabel": format_week_label(week_start, week_end),
            }
        )

        for matcher in MATCHERS:
            best = pick_best_row(week_rows, matcher)
            if best is None:
                prices[matcher.canonical_id][week_start] = {
                    "price": None,
                    "offerText": None,
                    "confidence": None,
                }
                continue

            prices[matcher.canonical_id][week_start] = {
                "price": normalize_unit_price(best),
                "offerText": best.get("split_product_text")
                or best.get("raw_offer_text"),
                "confidence": match_confidence(best, matcher),
            }

    return weeks, prices


def render_ts(
    weeks: list[dict[str, str]],
    prices: dict[str, dict[str, dict[str, object | None]]],
) -> str:
    weeks_json = json.dumps(weeks, indent=2)
    prices_json = json.dumps(prices, indent=2)
    return f"""// AUTO-GENERATED by scripts/generate_weekly_ad_prices.py — do not edit by hand.
// Source manifest: data/weekly_ads/flyer_manifest_safeway.csv
// Source offers: scrolling-the-aisle/outputs/product_discovery_safeway/split_offer_items.csv

export type WeeklyAdWeek = {{
  weekStart: string;
  weekEnd: string;
  sourceFile: string;
  sourceLabel: string;
}};

export type GeneratedWeeklyAdPrice = {{
  price: number | null;
  offerText: string | null;
  confidence: "high" | "medium" | "low" | null;
}};

export const WEEKLY_AD_WEEKS: WeeklyAdWeek[] = {weeks_json};

export const WEEKLY_AD_PRICES: Record<
  string,
  Record<string, GeneratedWeeklyAdPrice>
> = {prices_json};
"""


def main() -> None:
    manifest = load_manifest()
    split_items = load_split_items()
    weeks, prices = build_prices(manifest, split_items)
    OUTPUT_PATH.write_text(render_ts(weeks, prices), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} ({len(weeks)} weeks, {len(TRACKER_CANONICAL_IDS)} products)")


if __name__ == "__main__":
    main()
