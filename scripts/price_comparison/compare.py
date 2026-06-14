"""Compare grocery vs Costco per-unit prices."""

from __future__ import annotations

from dataclasses import dataclass

from .canonical_metadata import CANONICAL_PACKAGES, CanonicalPackageMeta
from .costco_loader import CostcoItem
from .unit_normalize import (
    ParsedPackage,
    grocery_package_from_meta,
    unit_price,
    units_compatible,
)

THRESHOLD = 0.03


@dataclass
class ComparisonResult:
    canonical_product_id: str
    grocery_feed_id: str
    grocery_store_label: str
    grocery_price: float | None
    grocery_package_description: str | None
    grocery_unit_type: str | None
    grocery_unit_count: float | None
    grocery_unit_price: float | None
    costco_region_id: str | None
    costco_store_label: str | None
    costco_price: float | None
    costco_package_description: str | None
    costco_unit_type: str | None
    costco_unit_count: float | None
    costco_unit_price: float | None
    winner: str
    savings_amount: float | None
    savings_percent: float | None
    comparison_status: str
    comparison_note: str | None
    source: str | None


def compare_prices(
    *,
    canonical_id: str,
    grocery_feed_id: str,
    grocery_store_label: str,
    grocery_effective_price: float | None,
    grocery_size_label: str | None,
    costco_region_id: str,
    costco_store_label: str,
    costco_item: CostcoItem | None,
    costco_searched: bool,
) -> ComparisonResult:
    meta = CANONICAL_PACKAGES[canonical_id]
    base = _empty_result(
        canonical_id,
        grocery_feed_id,
        grocery_store_label,
        costco_region_id,
        costco_store_label,
    )

    if grocery_effective_price is None:
        base.comparison_status = "missing_grocery_price"
        base.winner = "unknown"
        base.comparison_note = "No grocery price observation"
        return base

    grocery_pkg = grocery_package_from_meta(
        grocery_size_label,
        meta.package_quantity,
        meta.unit_type,
    )
    grocery_up = unit_price(grocery_effective_price, grocery_pkg)
    base.grocery_price = grocery_effective_price
    base.grocery_package_description = grocery_pkg.description
    base.grocery_unit_type = grocery_pkg.unit_type
    base.grocery_unit_count = grocery_pkg.unit_count
    base.grocery_unit_price = grocery_up

    if not costco_searched:
        base.comparison_status = "needs_review"
        base.winner = "unknown"
        base.comparison_note = "Costco catalog not loaded"
        return base

    if costco_item is None:
        base.comparison_status = "not_sold_at_costco"
        base.winner = "grocery_only"
        base.comparison_note = "No Costco match in warehouse search data"
        return base

    if costco_item.parsed is None:
        base.costco_price = costco_item.sell_price
        base.costco_package_description = costco_item.item_sign
        base.comparison_status = "needs_review"
        base.winner = "unknown"
        base.comparison_note = f"Could not parse Costco package size: {costco_item.item_sign}"
        base.source = costco_item.source_file
        return base

    costco_up = unit_price(costco_item.sell_price, costco_item.parsed)
    base.costco_price = costco_item.sell_price
    base.costco_package_description = costco_item.item_sign
    base.costco_unit_type = costco_item.parsed.unit_type
    base.costco_unit_count = costco_item.parsed.unit_count
    base.costco_unit_price = costco_up
    base.source = costco_item.source_file

    if grocery_up is None or costco_up is None:
        base.comparison_status = "needs_review"
        base.winner = "unknown"
        base.comparison_note = "Could not compute unit price"
        return base

    if not units_compatible(grocery_pkg.comparable_unit, costco_item.parsed.comparable_unit):
        base.comparison_status = "unit_mismatch"
        base.winner = "unknown"
        base.comparison_note = (
            f"Grocery unit ({grocery_pkg.comparable_unit}) vs "
            f"Costco unit ({costco_item.parsed.comparable_unit})"
        )
        return base

    # Normalize to grocery comparable unit when oz/fl_oz compatible
    g = grocery_up
    c = costco_up
    if grocery_pkg.comparable_unit == "oz" and costco_item.parsed.comparable_unit == "fl_oz":
        pass  # treat as comparable for beverages/snacks
    elif grocery_pkg.comparable_unit != costco_item.parsed.comparable_unit:
        base.comparison_status = "unit_mismatch"
        base.winner = "unknown"
        base.comparison_note = "Incompatible units after normalization"
        return base

    winner, savings_amount, savings_percent = _pick_winner(g, c)
    base.winner = winner
    base.savings_amount = savings_amount
    base.savings_percent = savings_percent
    base.comparison_status = "comparable"
    if costco_item.parsed.confidence == "low" or meta.costco_not_expected:
        base.comparison_status = "needs_review"
        base.comparison_note = "Fairness review suggested (proxy match or limited Costco coverage)"
    return base


def _pick_winner(grocery_up: float, costco_up: float) -> tuple[str, float | None, float | None]:
    cheaper = min(grocery_up, costco_up)
    diff = abs(grocery_up - costco_up)
    pct = round((diff / cheaper) * 100, 2) if cheaper > 0 else None

    if pct is not None and pct <= THRESHOLD * 100:
        return "tie", round(diff, 4), pct

    if grocery_up <= costco_up * (1 - THRESHOLD):
        savings = round(costco_up - grocery_up, 4)
        sp = round(((costco_up - grocery_up) / costco_up) * 100, 2) if costco_up else None
        return "grocery", savings, sp

    if costco_up <= grocery_up * (1 - THRESHOLD):
        savings = round(grocery_up - costco_up, 4)
        sp = round(((grocery_up - costco_up) / grocery_up) * 100, 2) if grocery_up else None
        return "costco", savings, sp

    return "tie", round(diff, 4), pct


def _empty_result(
    canonical_id: str,
    grocery_feed_id: str,
    grocery_store_label: str,
    costco_region_id: str,
    costco_store_label: str,
) -> ComparisonResult:
    return ComparisonResult(
        canonical_product_id=canonical_id,
        grocery_feed_id=grocery_feed_id,
        grocery_store_label=grocery_store_label,
        grocery_price=None,
        grocery_package_description=None,
        grocery_unit_type=None,
        grocery_unit_count=None,
        grocery_unit_price=None,
        costco_region_id=costco_region_id,
        costco_store_label=costco_store_label,
        costco_price=None,
        costco_package_description=None,
        costco_unit_type=None,
        costco_unit_count=None,
        costco_unit_price=None,
        winner="unknown",
        savings_amount=None,
        savings_percent=None,
        comparison_status="missing_grocery_price",
        comparison_note=None,
        source=None,
    )
