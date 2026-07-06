"""Assemble deal rows and write CSV / markdown outputs."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from weekly_ad_analysis.brief import render_video_brief


OUTPUT_FIELDS = [
    "week_start",
    "week_end",
    "market",
    "market_display_name",
    "retailer",
    "canonical_product_id",
    "canonical_category_id",
    "department",
    "category",
    "canonical_name",
    "ad_item_name",
    "brand",
    "raw_ad_text",
    "page_number",
    "deal_type",
    "is_five_dollar_friday",
    "deal_price",
    "size",
    "quantity",
    "normalized_unit",
    "normalized_unit_price",
    "costco_match_name",
    "costco_price",
    "costco_size",
    "costco_unit_price",
    "percent_difference_vs_costco",
    "costco_match_type",
    "costco_match_confidence",
    "market_all_time_low_unit_price",
    "market_90_day_low_unit_price",
    "market_median_unit_price",
    "percent_above_all_time_low",
    "percent_below_median",
    "historical_benchmark_bucket",
    "deal_bucket",
    "content_score",
    "confidence",
    "script_angle",
    "notes",
]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_debug_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("ad_item_name,raw_ad_text,page_number,notes\n", encoding="utf-8")
        return
    fields = ["ad_item_name", "raw_ad_text", "page_number", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_skipped_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = OUTPUT_FIELDS + ["skip_reason"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def sort_ranked(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            0 if row.get("is_five_dollar_friday") else 1,
            -int(row.get("content_score") or 0),
            {"high": 0, "medium": 1, "low": 2}.get(row.get("confidence") or "low", 2),
        ),
    )


def write_all_outputs(
    output_dir: Path,
    *,
    matched: list[dict],
    skipped: list[dict],
    unmatched: list[dict],
    market_display_name: str,
    retailer_label: str,
    week_start: str,
    week_end: str,
) -> None:
    ranked = sort_ranked(
        [row for row in matched if row.get("deal_bucket") != "Skip / not worth highlighting"]
    )
    write_csv(output_dir / "matched_watchlist_deals.csv", matched)
    write_csv(output_dir / "ranked_video_candidates.csv", ranked)
    write_skipped_csv(output_dir / "skipped_watchlist_matches.csv", skipped)
    write_debug_csv(
        output_dir / "debug_unmatched_items.csv",
        [
            {
                "ad_item_name": row.get("ad_item_name"),
                "raw_ad_text": row.get("raw_ad_text"),
                "page_number": row.get("page_number"),
                "notes": "food-like ad text with no watchlist match",
            }
            for row in unmatched
        ],
    )
    brief = render_video_brief(
        market_display_name=market_display_name,
        retailer_label=retailer_label,
        week_start=week_start,
        week_end=week_end,
        ranked=ranked,
        skipped=skipped,
    )
    (output_dir / "video_brief.md").write_text(brief, encoding="utf-8")
