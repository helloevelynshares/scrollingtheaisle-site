#!/usr/bin/env python3
"""Generate weekly ad prices for the staging price tracker.

Reads Safeway and Vons flyer manifests from data/weekly_ads/ and offer rows from the
scrolling-the-aisle repo (split_offer_items.csv). Writes
src/data/weeklyAdPrices.generated.ts and src/data/vonsWeeklyAdPrices.generated.ts.

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
    "fage_greek_yogurt",
    "frito_lay_multipack_chips",
    "haagen_dazs_ice_cream",
    "grapes",
    "eggs_18_count",
    "oreos_sandwich_cookies",
    "protein_bars",
    "kettle_brand_chips",
]

TRACKER_FAMILY_IDS = [
    "ben_jerrys_ice_cream",
    "ritz_crackers_snacks",
]


@dataclass(frozen=True)
class FeedConfig:
    feed_label: str
    manifest_path: Path
    split_items_path: Path
    output_path: Path
    banner_filter: str | None = None


FEEDS: tuple[FeedConfig, ...] = (
    FeedConfig(
        feed_label="Safeway",
        manifest_path=ROOT / "data" / "weekly_ads" / "flyer_manifest_safeway.csv",
        split_items_path=DATA_ROOT
        / "outputs"
        / "product_discovery_safeway"
        / "split_offer_items.csv",
        output_path=ROOT / "src" / "data" / "weeklyAdPrices.generated.ts",
        banner_filter="Safeway",
    ),
    FeedConfig(
        feed_label="Vons",
        manifest_path=ROOT / "data" / "weekly_ads" / "flyer_manifest_vons.csv",
        split_items_path=DATA_ROOT
        / "outputs"
        / "product_discovery_vons"
        / "split_offer_items.csv",
        output_path=ROOT / "src" / "data" / "vonsWeeklyAdPrices.generated.ts",
        banner_filter="Vons",
    ),
)


@dataclass(frozen=True)
class ProductMatcher:
    canonical_id: str
    patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...] = ()
    prefer_patterns: tuple[str, ...] = ()


@dataclass(frozen=True)
class FamilyMemberMatcher:
    family_id: str
    member_id: str
    patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...] = ()
    prefer_patterns: tuple[str, ...] = ()


FAMILY_MATCHERS: tuple[ProductMatcher, ...] = (
    ProductMatcher(
        "ben_jerrys_ice_cream",
        patterns=(r"ben\s*&\s*jerry", r"ben and jerry"),
        exclude_patterns=(
            r"popsicle",
            r"cookie dough chunks?",
            r"haagen.?dazs",
            r"häagen.?dazs",
            r"klondike",
            r"dreyer",
        ),
        prefer_patterns=(
            r"ben\s*&\s*jerry.*ice cream",
            r"ben and jerry.*ice cream",
            r"ben\s*&\s*jerry.*bars",
        ),
    ),
    ProductMatcher(
        "ritz_crackers_snacks",
        patterns=(r"ritz crackers?", r"ritz snack crackers?"),
        exclude_patterns=(
            r"lay'?s",
            r"fritos?",
            r"ruffles?",
            r"toasted chips",
            r"cheese crackers",
        ),
        prefer_patterns=(r"^ritz crackers?", r"ritz crackers? \d", r"ritz crackers? 5"),
    ),
)

FAMILY_MEMBER_MATCHERS: tuple[FamilyMemberMatcher, ...] = (
    FamilyMemberMatcher(
        "ben_jerrys_ice_cream",
        "pint",
        patterns=(r"ben\s*&\s*jerry", r"ben and jerry"),
        exclude_patterns=(
            r"popsicle",
            r"cookie dough chunks?",
            r"non.?dairy",
            r"bars?",
            r"haagen.?dazs",
            r"häagen.?dazs",
        ),
        prefer_patterns=(r"ben\s*&\s*jerry.*pint", r"ben\s*&\s*jerry.*16", r"ice cream pint"),
    ),
    FamilyMemberMatcher(
        "ben_jerrys_ice_cream",
        "non_dairy_pint",
        patterns=(r"ben\s*&\s*jerry", r"ben and jerry"),
        exclude_patterns=(r"popsicle", r"cookie dough chunks?", r"bars?"),
        prefer_patterns=(r"non.?dairy", r"frozen dessert"),
    ),
    FamilyMemberMatcher(
        "ben_jerrys_ice_cream",
        "bars_4ct",
        patterns=(r"ben\s*&\s*jerry", r"ben and jerry"),
        exclude_patterns=(r"popsicle", r"cookie dough chunks?", r"pint", r"16 oz"),
        prefer_patterns=(r"bars?", r"4.?ct", r"4 count"),
    ),
    FamilyMemberMatcher(
        "ritz_crackers_snacks",
        "classic_box",
        patterns=(r"ritz crackers?",),
        exclude_patterns=(
            r"lay'?s",
            r"fritos?",
            r"ruffles?",
            r"toasted chips",
            r"cheese crackers",
        ),
        prefer_patterns=(r"^ritz crackers?", r"ritz crackers? \d", r"7\.1-13\.7"),
    ),
)


MATCHERS: tuple[ProductMatcher, ...] = (
    ProductMatcher(
        "strawberries",
        patterns=(r"strawberries", r"fresh strawberries", r"organic strawberries"),
        exclude_patterns=(r"^blueberr", r"^raspberr", r"^blackberr", r"2 lb"),
        prefer_patterns=(r"^strawberries$", r"1-lb", r"fresh strawberries"),
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
        patterns=(r"nature valley", r"nature valley bars"),
        exclude_patterns=(r"pop-tarts",),
        prefer_patterns=(
            r"nature valley bars",
            r"nature valley crunchy",
            r"nature valley protein",
        ),
    ),
    ProductMatcher(
        "fage_greek_yogurt",
        patterns=(r"fage", r"fage greek", r"fage total"),
        exclude_patterns=(r"chobani",),
        prefer_patterns=(
            r"fage total",
            r"fage greek yogurt",
            r"fage 0%",
            r"fage 2%",
        ),
    ),
    ProductMatcher(
        "frito_lay_multipack_chips",
        patterns=(
            r"frito.?lay",
            r"variety pack",
            r"chip multipack",
            r"42 count",
            r"30 count",
            r"snack pack chips",
        ),
        prefer_patterns=(
            r"frito.?lay variety",
            r"42 count",
            r"30 count",
            r"variety pack chips",
        ),
    ),
    ProductMatcher(
        "haagen_dazs_ice_cream",
        patterns=(r"haagen.?dazs", r"häagen.?dazs", r"ice cream bars"),
        exclude_patterns=(r"tillamook",),
        prefer_patterns=(r"haagen.?dazs ice cream", r"haagen.?dazs bars"),
    ),
    ProductMatcher(
        "grapes",
        patterns=(r"grapes", r"green grapes", r"red grapes", r"seedless grapes"),
        exclude_patterns=(r"grape juice", r"grape tomato"),
        prefer_patterns=(r"seedless grapes", r"green grapes", r"red grapes"),
    ),
    ProductMatcher(
        "eggs_18_count",
        patterns=(r"eggs", r"18 count eggs", r"18-count eggs"),
        exclude_patterns=(r"egg nog", r"egg roll", r"egg beaters", r"egg bite"),
        prefer_patterns=(r"18 count", r"18-count", r"large eggs"),
    ),
    ProductMatcher(
        "oreos_sandwich_cookies",
        patterns=(r"oreo", r"sandwich cookies"),
        exclude_patterns=(r"oreo ice cream", r"oreo thins"),
        prefer_patterns=(r"oreo cookies", r"family size oreo", r"^oreos?$"),
    ),
    ProductMatcher(
        "protein_bars",
        patterns=(
            r"protein bars",
            r"rxbar",
            r"rx bars",
            r"kai'?s protein",
            r"kize protein",
        ),
        exclude_patterns=(r"nature valley protein",),
        prefer_patterns=(r"protein bars", r"rxbar"),
    ),
    ProductMatcher(
        "kettle_brand_chips",
        patterns=(r"kettle brand", r"kettle chips", r"kettle cooked"),
        exclude_patterns=(r"lay's.*kettle cooked", r"lays.*kettle cooked"),
        prefer_patterns=(r"kettle brand", r"kettle brand potato chips"),
    ),
)


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_split_items(path: Path, banner_filter: str | None) -> list[dict[str, str]]:
    if not path.is_file():
        print(f"Warning: missing split offer items at {path} — skipping feed output")
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if banner_filter:
        banner_norm = banner_filter.strip().lower()
        rows = [
            row
            for row in rows
            if (row.get("banner") or "").strip().lower() == banner_norm
        ]
    return rows


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


def pick_best_member_row(
    rows: list[dict[str, str]], matcher: FamilyMemberMatcher
) -> dict[str, str] | None:
    pseudo = ProductMatcher(
        matcher.family_id,
        matcher.patterns,
        matcher.exclude_patterns,
        matcher.prefer_patterns,
    )
    return pick_best_row(rows, pseudo)


def build_family_prices(
    feed_label: str,
    manifest: list[dict[str, str]],
    split_items: list[dict[str, str]],
) -> tuple[
    list[dict[str, str]],
    dict[str, dict[str, dict[str, object | None]]],
    dict[str, dict[str, dict[str, dict[str, object | None]]]],
]:
    weeks: list[dict[str, str]] = []
    family_prices: dict[str, dict[str, dict[str, object | None]]] = {
        family_id: {} for family_id in TRACKER_FAMILY_IDS
    }
    member_prices: dict[str, dict[str, dict[str, dict[str, object | None]]]] = {
        family_id: {} for family_id in TRACKER_FAMILY_IDS
    }
    for family_id in TRACKER_FAMILY_IDS:
        member_prices[family_id] = {}

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
                "sourceLabel": format_week_label(feed_label, week_start, week_end),
            }
        )

        for matcher in FAMILY_MATCHERS:
            best = pick_best_row(week_rows, matcher)
            if best is None:
                family_prices[matcher.canonical_id][week_start] = {
                    "price": None,
                    "offerText": None,
                    "confidence": None,
                }
                continue

            family_prices[matcher.canonical_id][week_start] = {
                "price": normalize_unit_price(best),
                "offerText": best.get("split_product_text")
                or best.get("raw_offer_text"),
                "confidence": match_confidence(best, matcher),
            }

        for matcher in FAMILY_MEMBER_MATCHERS:
            member_bucket = member_prices.setdefault(matcher.family_id, {})
            member_weeks = member_bucket.setdefault(matcher.member_id, {})
            best = pick_best_member_row(week_rows, matcher)
            if best is None:
                member_weeks[week_start] = {
                    "price": None,
                    "offerText": None,
                    "confidence": None,
                }
                continue

            pseudo = ProductMatcher(
                matcher.family_id,
                matcher.patterns,
                matcher.exclude_patterns,
                matcher.prefer_patterns,
            )
            member_weeks[week_start] = {
                "price": normalize_unit_price(best),
                "offerText": best.get("split_product_text")
                or best.get("raw_offer_text"),
                "confidence": match_confidence(best, pseudo),
            }

    return weeks, family_prices, member_prices


def render_combined_family_ts(
    safeway_manifest_path: Path,
    safeway_split_path: Path,
    safeway_weeks: list[dict[str, str]],
    safeway_family: dict[str, dict[str, dict[str, object | None]]],
    safeway_members: dict[str, dict[str, dict[str, dict[str, object | None]]]],
    vons_weeks: list[dict[str, str]],
    vons_family: dict[str, dict[str, dict[str, object | None]]],
    vons_members: dict[str, dict[str, dict[str, dict[str, object | None]]]],
) -> str:
    try:
        rel_split = safeway_split_path.relative_to(DATA_ROOT)
    except ValueError:
        rel_split = safeway_split_path
    return f"""// AUTO-GENERATED by scripts/generate_weekly_ad_prices.py — do not edit by hand.
// Source manifest: {safeway_manifest_path.relative_to(ROOT)}
// Source offers: scrolling-the-aisle/{rel_split}

import type {{ GeneratedWeeklyAdPrice, WeeklyAdWeek }} from "./weeklyAdPrices.generated";

export type {{ GeneratedWeeklyAdPrice, WeeklyAdWeek }};

export const FAMILY_WEEKLY_AD_WEEKS: WeeklyAdWeek[] = {json.dumps(safeway_weeks, indent=2)};

export const FAMILY_WEEKLY_AD_PRICES: Record<
  string,
  Record<string, GeneratedWeeklyAdPrice>
> = {json.dumps(safeway_family, indent=2)};

export const FAMILY_MEMBER_WEEKLY_AD_PRICES: Record<
  string,
  Record<string, Record<string, GeneratedWeeklyAdPrice>>
> = {json.dumps(safeway_members, indent=2)};

export const VONS_FAMILY_WEEKLY_AD_WEEKS: WeeklyAdWeek[] = {json.dumps(vons_weeks, indent=2)};

export const VONS_FAMILY_WEEKLY_AD_PRICES: Record<
  string,
  Record<string, GeneratedWeeklyAdPrice>
> = {json.dumps(vons_family, indent=2)};

export const VONS_FAMILY_MEMBER_WEEKLY_AD_PRICES: Record<
  string,
  Record<string, Record<string, GeneratedWeeklyAdPrice>>
> = {json.dumps(vons_members, indent=2)};
"""


def format_week_label(feed_label: str, week_start: str, week_end: str) -> str:
    start = week_start[5:].replace("-", "/")
    end = week_end[5:].replace("-", "/")
    return f"{feed_label} weekly ad {start}–{end}"


def build_prices(
    feed_label: str,
    manifest: list[dict[str, str]],
    split_items: list[dict[str, str]],
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
                "sourceLabel": format_week_label(feed_label, week_start, week_end),
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
    feed_label: str,
    manifest_path: Path,
    split_items_path: Path,
    weeks: list[dict[str, str]],
    prices: dict[str, dict[str, dict[str, object | None]]],
) -> str:
    weeks_json = json.dumps(weeks, indent=2)
    prices_json = json.dumps(prices, indent=2)
    export_weeks = "WEEKLY_AD_WEEKS" if feed_label == "Safeway" else "VONS_WEEKLY_AD_WEEKS"
    export_prices = "WEEKLY_AD_PRICES" if feed_label == "Safeway" else "VONS_WEEKLY_AD_PRICES"
    try:
        rel_split = split_items_path.relative_to(DATA_ROOT)
    except ValueError:
        rel_split = split_items_path
    return f"""// AUTO-GENERATED by scripts/generate_weekly_ad_prices.py — do not edit by hand.
// Source manifest: {manifest_path.relative_to(ROOT)}
// Source offers: scrolling-the-aisle/{rel_split}

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

export const {export_weeks}: WeeklyAdWeek[] = {weeks_json};

export const {export_prices}: Record<
  string,
  Record<string, GeneratedWeeklyAdPrice>
> = {prices_json};
"""


FAMILY_OUTPUT = ROOT / "src" / "data" / "familyWeeklyAdPrices.generated.ts"


def generate_feed(config: FeedConfig) -> None:
    manifest = load_manifest(config.manifest_path)
    split_items = load_split_items(config.split_items_path, config.banner_filter)
    weeks, prices = build_prices(config.feed_label, manifest, split_items)
    config.output_path.write_text(
        render_ts(
            config.feed_label,
            config.manifest_path,
            config.split_items_path,
            weeks,
            prices,
        ),
        encoding="utf-8",
    )
    print(
        f"Wrote {config.output_path.relative_to(ROOT)} "
        f"({len(weeks)} weeks, {len(TRACKER_CANONICAL_IDS)} products)"
    )


def generate_family_prices() -> None:
    safeway = FEEDS[0]
    vons = FEEDS[1]
    safeway_manifest = load_manifest(safeway.manifest_path)
    vons_manifest = load_manifest(vons.manifest_path)
    safeway_items = load_split_items(safeway.split_items_path, safeway.banner_filter)
    vons_items = load_split_items(vons.split_items_path, vons.banner_filter)

    safeway_weeks, safeway_family, safeway_members = build_family_prices(
        safeway.feed_label, safeway_manifest, safeway_items
    )
    vons_weeks, vons_family, vons_members = build_family_prices(
        vons.feed_label, vons_manifest, vons_items
    )

    FAMILY_OUTPUT.write_text(
        render_combined_family_ts(
            safeway.manifest_path,
            safeway.split_items_path,
            safeway_weeks,
            safeway_family,
            safeway_members,
            vons_weeks,
            vons_family,
            vons_members,
        ),
        encoding="utf-8",
    )
    print(
        f"Wrote {FAMILY_OUTPUT.relative_to(ROOT)} "
        f"({len(TRACKER_FAMILY_IDS)} families)"
    )


def main() -> None:
    for config in FEEDS:
        generate_feed(config)
    generate_family_prices()


if __name__ == "__main__":
    main()
