"""Match ad rows to canonical products and tracker families."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_weekly_ad_prices import (  # noqa: E402
    FAMILY_MATCHERS,
    MATCHERS,
    ProductMatcher,
    match_confidence,
    matches,
    normalize_unit_price,
    pick_best_row,
    preference_score,
    row_text,
    split_text,
)
from price_tracker.canonical_match_eligibility import EligibilityIndex  # noqa: E402
from weekly_ad_analysis.ad_loader import AdOfferRow
from weekly_ad_analysis.config_loader import ContentWatchlistEntry


@dataclass(frozen=True)
class WatchlistMatch:
    tracker_id: str
    tracker_kind: str  # canonical | family
    display_name: str
    department: str
    category: str
    content: ContentWatchlistEntry
    ad_row: AdOfferRow
    match_confidence: str
    brand: str | None
    match_output_class: str = "canonical_tracker_match"


def _row_dict(ad_row: AdOfferRow) -> dict[str, str]:
    return {
        "split_product_text": ad_row.split_product_text or ad_row.ad_item_name,
        "raw_offer_text": ad_row.raw_ad_text,
        "promo_text": ad_row.promo_text or "",
        "advertised_price": str(ad_row.advertised_price) if ad_row.advertised_price is not None else "",
        "price_basis": ad_row.price_basis or "",
        "package_unit": ad_row.package_unit or "",
        "package_size_min": str(ad_row.package_size_min) if ad_row.package_size_min is not None else "",
        "package_size_max": str(ad_row.package_size_max) if ad_row.package_size_max is not None else "",
    }


def _guess_brand(text: str) -> str | None:
    brands = [
        "Chobani", "Fage", "Tillamook", "Häagen-Dazs", "Haagen-Dazs", "Nature Valley",
        "Doritos", "Cheetos", "Oreo", "Kettle Brand", "Mission", "Cheerios", "Coca-Cola",
        "Ben & Jerry", "Ritz", "RXBAR",
    ]
    for brand in brands:
        if brand.lower() in text.lower():
            return brand
    return None


def match_watchlist_rows(
    ad_rows: list[AdOfferRow],
    eligible: list[ContentWatchlistEntry],
    *,
    canonical_display: dict[str, tuple[str, str, str]],
    family_display: dict[str, tuple[str, str, str]],
) -> tuple[list[WatchlistMatch], list[AdOfferRow]]:
    dict_rows = [_row_dict(row) for row in ad_rows]
    matches_out: list[WatchlistMatch] = []
    matched_row_indexes: set[int] = set()

    canonical_ids = {
        entry.canonical_product_id
        for entry in eligible
        if entry.canonical_product_id
    }
    family_ids = {
        entry.canonical_category_id
        for entry in eligible
        if entry.canonical_category_id
    }

    content_by_canonical = {
        e.canonical_product_id: e for e in eligible if e.canonical_product_id
    }
    content_by_family = {
        e.canonical_category_id: e for e in eligible if e.canonical_category_id
    }

    eligibility = EligibilityIndex()

    for matcher in MATCHERS:
        if matcher.canonical_id not in canonical_ids:
            continue
        best = pick_best_row(dict_rows, matcher)
        if best is None:
            continue
        idx = dict_rows.index(best)
        matched_row_indexes.add(idx)
        dept, category = canonical_display.get(matcher.canonical_id, ("Food", "general", "general"))[1:]
        display_name = canonical_display.get(matcher.canonical_id, (matcher.canonical_id, "Food", "general"))[0]
        conf = match_confidence(best, matcher) or "low"
        elig = eligibility.evaluate(best, matcher.canonical_id, keyword_confidence=conf)
        if elig.match_decision != "accepted":
            continue
        ad_row = ad_rows[idx]
        matches_out.append(
            WatchlistMatch(
                tracker_id=matcher.canonical_id,
                tracker_kind="canonical",
                display_name=display_name,
                department=dept,
                category=category,
                content=content_by_canonical[matcher.canonical_id],
                ad_row=ad_row,
                match_confidence=conf,
                brand=_guess_brand(ad_row.raw_ad_text),
                match_output_class=elig.output_class,
            )
        )

    for matcher in FAMILY_MATCHERS:
        if matcher.canonical_id not in family_ids:
            continue
        best = pick_best_row(dict_rows, matcher)
        if best is None:
            continue
        idx = dict_rows.index(best)
        matched_row_indexes.add(idx)
        display, dept, category = family_display.get(
            matcher.canonical_id,
            (matcher.canonical_id, "Food", "general"),
        )
        pseudo = ProductMatcher(
            matcher.canonical_id,
            matcher.patterns,
            matcher.exclude_patterns,
            matcher.prefer_patterns,
        )
        conf = match_confidence(best, pseudo) or "low"
        ad_row = ad_rows[idx]
        matches_out.append(
            WatchlistMatch(
                tracker_id=matcher.canonical_id,
                tracker_kind="family",
                display_name=display,
                department=dept,
                category=category,
                content=content_by_family[matcher.canonical_id],
                ad_row=ad_row,
                match_confidence=conf,
                brand=_guess_brand(ad_row.raw_ad_text),
            )
        )

    unmatched_food_like: list[AdOfferRow] = []
    food_hint = re.compile(
        r"chicken|beef|salmon|shrimp|eggs?|yogurt|cheese|grapes|berries|strawberr|avocado|"
        r"chips|crackers|cookies|cereal|ice cream|soda|milk|butter|pasta|bread|corn|apples?",
        re.I,
    )
    exclude_hint = re.compile(
        r"paper towel|toilet paper|detergent|diaper|shampoo|pharmacy|beer|wine|vodka|"
        r"dog food|cat food|litter|cleaning",
        re.I,
    )
    for idx, row in enumerate(ad_rows):
        if idx in matched_row_indexes:
            continue
        text = row.raw_ad_text or row.ad_item_name
        if exclude_hint.search(text):
            continue
        if food_hint.search(text):
            unmatched_food_like.append(row)

    return matches_out, unmatched_food_like


def ad_row_to_price_dict(ad_row: AdOfferRow) -> dict[str, str]:
    return _row_dict(ad_row)


def compute_normalized_unit_price(ad_row: AdOfferRow, matcher: ProductMatcher | None = None) -> float | None:
    row = _row_dict(ad_row)
    if matcher is None and ad_row.advertised_price is not None:
        return ad_row.advertised_price
    if matcher is not None:
        return normalize_unit_price(row)
    return ad_row.advertised_price
