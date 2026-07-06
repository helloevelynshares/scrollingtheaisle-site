"""Costco comparison for weekly ad matches."""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from price_comparison.canonical_metadata import CANONICAL_PACKAGES  # noqa: E402
from price_comparison.compare import compare_prices  # noqa: E402
from price_comparison.costco_loader import (  # noqa: E402
    CostcoItem,
    _observation_to_item,
    _row_to_observation,
    match_costco_item,
    parse_costco_filename,
)
from price_comparison.unit_normalize import parse_item_sign  # noqa: E402


@dataclass(frozen=True)
class CostcoMatchResult:
    costco_match_name: str | None
    costco_brand: str | None
    costco_price: float | None
    costco_size: str | None
    costco_unit_price: float | None
    costco_unit_type: str | None
    match_type: str
    match_confidence: str
    percent_difference_vs_costco: float | None
    notes: str | None


def _match_type_label(canonical_id: str, item: CostcoItem | None) -> str:
    if item is None:
        return "no comp"
    sign = item.item_sign.lower()
    meta = CANONICAL_PACKAGES.get(canonical_id)
    if meta and "kirkland" in sign:
        return "different brand same category"
    if meta and any(re.search(pat, sign) for pat in meta.costco_prefer):
        return "exact brand"
    return "category benchmark only"


def load_catalog_from_csv(csv_path: Path, region_slug: str) -> list[CostcoItem]:
    parsed = parse_costco_filename(csv_path)
    if parsed:
        file_date, file_region = parsed
    else:
        from datetime import date

        file_date = date.today().isoformat()
        file_region = region_slug
    by_item: dict[str, CostcoItem] = {}
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            obs = _row_to_observation(
                row,
                file_date=file_date,
                region=file_region,
                source_file=csv_path.name,
            )
            if obs is None:
                continue
            item = _observation_to_item(obs)
            meta = None
            parsed_pkg = parse_item_sign(item.item_sign, "oz")
            item = replace(item, parsed=parsed_pkg)
            by_item[item.item_number] = item
    return list(by_item.values())


def compare_to_costco(
    *,
    canonical_id: str,
    grocer_price: float | None,
    grocer_size_label: str | None,
    costco_csv: Path,
    costco_region_slug: str,
    grocery_feed_id: str,
    grocery_store_label: str,
    costco_store_label: str,
) -> CostcoMatchResult:
    if grocer_price is None:
        return CostcoMatchResult(
            None, None, None, None, None, None, "no comp", "low", None,
            "No grocer unit price to compare",
        )

    catalog = load_catalog_from_csv(costco_csv, costco_region_slug)
    item, note = match_costco_item(
        canonical_id, catalog, warehouse=costco_region_slug,
    )
    if item is None:
        return CostcoMatchResult(
            None, None, None, None, None, None, "no comp", "low", None, note,
        )

    result = compare_prices(
        canonical_id=canonical_id,
        grocery_feed_id=grocery_feed_id,
        grocery_store_label=grocery_store_label,
        grocery_effective_price=grocer_price,
        grocery_size_label=grocer_size_label,
        costco_region_id="costco_sf" if costco_region_slug == "san_francisco" else "costco_oc",
        costco_store_label=costco_store_label,
        costco_item=item,
        costco_searched=True,
    )

    if result.comparison_status not in {"comparable", "needs_review"}:
        return CostcoMatchResult(
            item.item_sign,
            "Kirkland" if "kirkland" in item.item_sign.lower() else None,
            item.sell_price,
            item.item_sign,
            result.costco_unit_price,
            result.costco_unit_type,
            _match_type_label(canonical_id, item),
            "low" if result.comparison_status == "unit_mismatch" else "medium",
            None,
            result.comparison_note,
        )

    pct = None
    if result.grocery_unit_price is not None and result.costco_unit_price is not None:
        cheaper = min(result.grocery_unit_price, result.costco_unit_price)
        if cheaper > 0:
            pct = round(
                ((result.costco_unit_price - result.grocery_unit_price) / result.costco_unit_price) * 100,
                2,
            )

    conf = "high"
    if result.comparison_status == "needs_review":
        conf = "medium"
    if _match_type_label(canonical_id, item) == "category benchmark only":
        conf = "medium"

    return CostcoMatchResult(
        item.item_sign,
        "Kirkland" if "kirkland" in item.item_sign.lower() else None,
        item.sell_price,
        item.item_sign,
        result.costco_unit_price,
        result.costco_unit_type,
        _match_type_label(canonical_id, item),
        conf,
        pct,
        result.comparison_note,
    )
