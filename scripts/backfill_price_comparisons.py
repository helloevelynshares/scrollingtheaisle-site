#!/usr/bin/env python3
"""Backfill price_comparisons from grocery observations + Costco warehouse CSVs.

Loads Costco prices from costco-mvp/costco_data (override with COSTCO_DATA_ROOT).
Writes SQL seed + frontend fallback TS.

Usage:
  python3 scripts/backfill_price_comparisons.py
  COSTCO_DATA_ROOT=/path/to/costco_data python3 scripts/backfill_price_comparisons.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from price_comparison.canonical_metadata import (  # noqa: E402
    CANONICAL_PACKAGES,
    GROCERY_FEEDS,
)
from price_comparison.compare import ComparisonResult, compare_prices  # noqa: E402
from price_comparison.costco_loader import (  # noqa: E402
    costco_data_root,
    load_location_catalog,
    match_costco_item,
)

SQL_OUTPUT = ROOT / "supabase" / "migrations" / "20260616_price_comparisons_seed.sql"
TS_OUTPUT = ROOT / "src" / "data" / "priceComparisons.generated.ts"

SAFEWAY_BASELINES: dict[str, tuple[float, str]] = {
    "strawberries": (4.99, "Strawberries 1 lb"),
    "avocados": (2.0, "Medium Hass Avocado"),
    "doritos_nacho_cheese": (5.49, "Doritos Nacho Cheese Tortilla Chips 9.25 oz"),
    "cheetos_crunchy": (5.49, "Cheetos Cheese Flavored Crunchy Snacks 8.5 oz"),
    "coke_zero": (12.99, "Coca-Cola Zero Sugar Soda 12 pack"),
    "chobani_greek_yogurt": (7.99, "Chobani Non-Fat Plain Greek Yogurt 32 oz"),
    "cheerios": (6.99, "Cheerios Whole Grain Oat Toasted Cereal 8.9 oz"),
    "tillamook_ice_cream": (6.99, "Tillamook Oregon Strawberry Ice Cream 1.75 qt"),
    "mission_tortilla_chips": (4.49, "Mission Round Yellow Corn Tortilla Chips 11 oz"),
    "nature_valley_bars": (4.99, "Nature Valley Crunchy Oats 'n Honey Granola Bars 12 ct"),
}

VONS_BASELINES: dict[str, tuple[float, str]] = {
    "strawberries": (3.99, "Strawberries 1 lb"),
    "avocados": (1.25, "Medium Hass Avocado"),
    "doritos_nacho_cheese": (5.49, "Doritos Nacho Cheese Tortilla Chips"),
    "cheetos_crunchy": (5.49, "Cheetos Crunchy"),
    "coke_zero": (8.99, "Coca-Cola Zero Sugar Soda 12 pack"),
    "chobani_greek_yogurt": (7.99, "Chobani Greek Yogurt 32 oz"),
    "cheerios": (6.99, "Cheerios"),
    "tillamook_ice_cream": (6.99, "Tillamook Ice Cream"),
    "mission_tortilla_chips": (4.49, "Mission Tortilla Chips"),
    "nature_valley_bars": (4.99, "Nature Valley Bars"),
    "grapes": (2.99, "Seedless Grapes per lb"),
    "eggs_18_count": (5.99, "Lucerne Cage Free Eggs 18 ct"),
    "fage_greek_yogurt": (6.99, "Fage Greek Yogurt 32 oz"),
    "kettle_brand_chips": (5.49, "Kettle Brand Potato Chips 8 oz"),
}


def parse_ts_export(path: Path, weeks_key: str, prices_key: str) -> tuple[list[dict], dict]:
    text = path.read_text(encoding="utf-8")
    weeks_match = re.search(rf"export const {weeks_key}.*?=\s*(\[.*?\]);", text, re.S)
    prices_match = re.search(rf"export const {prices_key}.*?=\s*(\{{.*?\}});", text, re.S)
    if not weeks_match or not prices_match:
        raise RuntimeError(f"Could not parse {path}")
    return json.loads(weeks_match.group(1)), json.loads(prices_match.group(1))


def latest_effective_price(
    canonical_id: str,
    weeks: list[dict],
    prices: dict,
    baseline: float | None,
) -> float | None:
    if not weeks:
        return baseline
    sorted_weeks = sorted(weeks, key=lambda w: w["weekStart"])
    for week in reversed(sorted_weeks):
        entry = prices.get(canonical_id, {}).get(week["weekStart"])
        if not entry:
            continue
        ad_price = entry.get("price")
        confidence = entry.get("confidence")
        if ad_price is not None and confidence is not None and confidence != "low":
            return float(ad_price)
    return baseline


def sql_str(value: str | None) -> str:
    if value is None:
        return "null"
    return "'" + value.replace("'", "''") + "'"


def sql_num(value: float | None) -> str:
    if value is None:
        return "null"
    return f"{value:.4f}".rstrip("0").rstrip(".")


def row_to_sql(row: ComparisonResult) -> str:
    cols = (
        "canonical_product_id, grocery_feed_id, grocery_store_label, "
        "grocery_price, grocery_package_description, grocery_unit_type, grocery_unit_count, "
        "grocery_unit_price, costco_region_id, costco_store_label, costco_price, "
        "costco_package_description, costco_unit_type, costco_unit_count, costco_unit_price, "
        "winner, savings_amount, savings_percent, comparison_status, comparison_note, source"
    )
    vals = ", ".join(
        [
            sql_str(row.canonical_product_id),
            sql_str(row.grocery_feed_id),
            sql_str(row.grocery_store_label),
            sql_num(row.grocery_price),
            sql_str(row.grocery_package_description),
            sql_str(row.grocery_unit_type),
            sql_num(row.grocery_unit_count),
            sql_num(row.grocery_unit_price),
            sql_str(row.costco_region_id),
            sql_str(row.costco_store_label),
            sql_num(row.costco_price),
            sql_str(row.costco_package_description),
            sql_str(row.costco_unit_type),
            sql_num(row.costco_unit_count),
            sql_num(row.costco_unit_price),
            sql_str(row.winner),
            sql_num(row.savings_amount),
            sql_num(row.savings_percent),
            sql_str(row.comparison_status),
            sql_str(row.comparison_note),
            sql_str(row.source),
        ]
    )
    updates = (
        "grocery_store_label = excluded.grocery_store_label, "
        "grocery_price = excluded.grocery_price, "
        "grocery_package_description = excluded.grocery_package_description, "
        "grocery_unit_type = excluded.grocery_unit_type, "
        "grocery_unit_count = excluded.grocery_unit_count, "
        "grocery_unit_price = excluded.grocery_unit_price, "
        "costco_store_label = excluded.costco_store_label, "
        "costco_price = excluded.costco_price, "
        "costco_package_description = excluded.costco_package_description, "
        "costco_unit_type = excluded.costco_unit_type, "
        "costco_unit_count = excluded.costco_unit_count, "
        "costco_unit_price = excluded.costco_unit_price, "
        "winner = excluded.winner, "
        "savings_amount = excluded.savings_amount, "
        "savings_percent = excluded.savings_percent, "
        "comparison_status = excluded.comparison_status, "
        "comparison_note = excluded.comparison_note, "
        "source = excluded.source, "
        "updated_at = now()"
    )
    return (
        f"insert into price_comparisons ({cols}) values ({vals}) "
        f"on conflict (canonical_product_id, grocery_feed_id, costco_region_id) do update set {updates};"
    )


def result_to_dict(row: ComparisonResult) -> dict:
    return {
        "canonicalProductId": row.canonical_product_id,
        "groceryFeedId": row.grocery_feed_id,
        "groceryStoreLabel": row.grocery_store_label,
        "groceryPrice": row.grocery_price,
        "groceryUnitType": row.grocery_unit_type,
        "groceryUnitPrice": row.grocery_unit_price,
        "costcoRegionId": row.costco_region_id,
        "costcoStoreLabel": row.costco_store_label,
        "costcoPrice": row.costco_price,
        "costcoUnitType": row.costco_unit_type,
        "costcoUnitPrice": row.costco_unit_price,
        "winner": row.winner,
        "savingsAmount": row.savings_amount,
        "savingsPercent": row.savings_percent,
        "comparisonStatus": row.comparison_status,
        "comparisonNote": row.comparison_note,
    }


def main() -> None:
    safeway_weeks, safeway_prices = parse_ts_export(
        ROOT / "src" / "data" / "weeklyAdPrices.generated.ts",
        "WEEKLY_AD_WEEKS",
        "WEEKLY_AD_PRICES",
    )
    vons_weeks, vons_prices = parse_ts_export(
        ROOT / "src" / "data" / "vonsWeeklyAdPrices.generated.ts",
        "VONS_WEEKLY_AD_WEEKS",
        "VONS_WEEKLY_AD_PRICES",
    )

    data_root = costco_data_root()
    catalogs: dict[str, list] = {}
    for feed in GROCERY_FEEDS.values():
        slug = feed["costco_location_slug"]
        if slug not in catalogs:
            catalogs[slug] = load_location_catalog(slug, data_root)

    results: list[ComparisonResult] = []
    review: list[str] = []

    feed_sources = {
        "safeway_bay_area": (safeway_weeks, safeway_prices, SAFEWAY_BASELINES),
        "vons_albertsons_socal": (vons_weeks, vons_prices, VONS_BASELINES),
    }

    for canonical_id, meta in CANONICAL_PACKAGES.items():
        for feed_id, feed_cfg in GROCERY_FEEDS.items():
            weeks, prices, baselines = feed_sources[feed_id]
            baseline_tuple = baselines.get(canonical_id)
            baseline_price = baseline_tuple[0] if baseline_tuple else None
            size_label = baseline_tuple[1] if baseline_tuple else meta.comparable_unit

            grocery_price = latest_effective_price(
                canonical_id, weeks, prices, baseline_price
            )
            if grocery_price is None and canonical_id not in prices:
                continue

            slug = feed_cfg["costco_location_slug"]
            catalog = catalogs[slug]
            costco_item, match_note = match_costco_item(canonical_id, catalog)

            row = compare_prices(
                canonical_id=canonical_id,
                grocery_feed_id=feed_id,
                grocery_store_label=feed_cfg["label"],
                grocery_effective_price=grocery_price,
                grocery_size_label=size_label,
                costco_region_id=feed_cfg["costco_region_id"],
                costco_store_label=feed_cfg["costco_store_label"],
                costco_item=costco_item,
                costco_searched=True,
            )
            if match_note and row.comparison_status == "not_sold_at_costco":
                row.comparison_note = match_note

            results.append(row)
            if row.comparison_status in {"needs_review", "unit_mismatch"}:
                review.append(
                    f"{canonical_id} @ {feed_id}: {row.comparison_status} — {row.comparison_note}"
                )

    sql_lines = [
        "-- AUTO-GENERATED by scripts/backfill_price_comparisons.py",
        f"-- Costco source: {data_root}",
        "",
    ]
    for row in results:
        sql_lines.append(row_to_sql(row))

    SQL_OUTPUT.write_text("\n".join(sql_lines) + "\n", encoding="utf-8")

    by_key: dict[str, dict] = {}
    for row in results:
        key = f"{row.canonical_product_id}:{row.grocery_feed_id}"
        by_key[key] = result_to_dict(row)

    ts_body = json.dumps(by_key, indent=2)
    TS_OUTPUT.write_text(
        f"""// AUTO-GENERATED by scripts/backfill_price_comparisons.py — do not edit by hand.
// Costco source: {data_root}

export type PriceComparisonWinner =
  | "grocery"
  | "costco"
  | "tie"
  | "grocery_only"
  | "unknown";

export type PriceComparisonStatus =
  | "comparable"
  | "not_sold_at_costco"
  | "missing_costco_price"
  | "missing_grocery_price"
  | "unit_mismatch"
  | "needs_review";

export type PriceComparisonView = {{
  canonicalProductId: string;
  groceryFeedId: string;
  groceryStoreLabel: string;
  groceryPrice: number | null;
  groceryUnitType: string | null;
  groceryUnitPrice: number | null;
  costcoRegionId: string | null;
  costcoStoreLabel: string | null;
  costcoPrice: number | null;
  costcoUnitType: string | null;
  costcoUnitPrice: number | null;
  winner: PriceComparisonWinner;
  savingsAmount: number | null;
  savingsPercent: number | null;
  comparisonStatus: PriceComparisonStatus;
  comparisonNote: string | null;
}};

export const PRICE_COMPARISONS_BY_KEY: Record<string, PriceComparisonView> = {ts_body};
""",
        encoding="utf-8",
    )

    print(f"Wrote {SQL_OUTPUT.relative_to(ROOT)} ({len(results)} rows)")
    print(f"Wrote {TS_OUTPUT.relative_to(ROOT)}")
    print(f"Costco data root: {data_root}")
    for slug, catalog in catalogs.items():
        print(f"  {slug}: {len(catalog)} unique items from CSV merge")

    winners = {}
    for row in results:
        winners[row.winner] = winners.get(row.winner, 0) + 1
    print("Winners:", winners)

    if review:
        print(f"\nNeeds review ({len(review)}):")
        for line in review:
            print(f"  - {line}")


if __name__ == "__main__":
    main()
