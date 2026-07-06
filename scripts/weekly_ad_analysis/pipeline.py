"""Weekly ad analysis pipeline."""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_weekly_ad_prices import MATCHERS, ProductMatcher  # noqa: E402
from price_comparison.canonical_metadata import CANONICAL_PACKAGES  # noqa: E402
from weekly_ad_analysis.ad_loader import load_ad_rows  # noqa: E402
from weekly_ad_analysis.benchmarks import compute_benchmark  # noqa: E402
from weekly_ad_analysis.config_loader import (  # noqa: E402
    CANONICAL_DISPLAY,
    FAMILY_DISPLAY,
    MarketConfig,
    eligible_watchlist,
    load_content_watchlist,
    load_markets,
)
from weekly_ad_analysis.costco_match import CostcoMatchResult, compare_to_costco  # noqa: E402
from weekly_ad_analysis.matcher import (  # noqa: E402
    WatchlistMatch,
    ad_row_to_price_dict,
    compute_normalized_unit_price,
    match_watchlist_rows,
)
from weekly_ad_analysis.output import write_all_outputs  # noqa: E402
from weekly_ad_analysis.scoring import score_deal  # noqa: E402


def _matcher_for(tracker_id: str, tracker_kind: str) -> ProductMatcher | None:
    if tracker_kind == "canonical":
        for matcher in MATCHERS:
            if matcher.canonical_id == tracker_id:
                return matcher
    return None


def _is_five_dollar_friday(ad_row) -> bool:
    text = " ".join(
        filter(None, [ad_row.promo_text, ad_row.raw_ad_text, ad_row.ad_item_name])
    ).lower()
    if ad_row.availability_type_guess == "friday_only":
        return True
    if ad_row.promo_type_guess == "five_dollar_friday":
        return True
    return "$5" in text and "friday" in text


def _deal_type(ad_row) -> str:
    if _is_five_dollar_friday(ad_row):
        return "$5 Friday"
    mapping = {
        "bogo": "BOGO",
        "buy_x_get_y": "buy-X-get-Y",
        "multi_buy": "multi-buy",
        "digital_coupon": "digital coupon",
        "member_price": "member price",
        "five_dollar_friday": "$5 Friday",
        "week_long": "week-long deal",
    }
    return mapping.get(ad_row.promo_type_guess or "", ad_row.promo_type_guess or "other")


def _week_end(week_start: str) -> str:
    start = date.fromisoformat(week_start)
    return (start + timedelta(days=6)).isoformat()


def _build_row(
    match: WatchlistMatch,
    *,
    market: MarketConfig,
    week_start: str,
    week_end: str,
    costco: CostcoMatchResult,
    benchmark,
    scored,
    normalized_unit_price: float | None,
    normalized_unit: str | None,
    unit_math_uncertain: bool,
) -> dict:
    ad = match.ad_row
    canonical_id = match.tracker_id if match.tracker_kind == "canonical" else ""
    category_id = match.tracker_id if match.tracker_kind == "family" else ""
    deal_price = ad.advertised_price
    size = ad.package_text
    return {
        "week_start": week_start,
        "week_end": week_end,
        "market": market.id,
        "market_display_name": market.display_name,
        "retailer": market.retailer_label,
        "canonical_product_id": canonical_id,
        "canonical_category_id": category_id,
        "department": match.department,
        "category": match.category,
        "canonical_name": match.display_name,
        "ad_item_name": ad.ad_item_name,
        "brand": match.brand or "",
        "raw_ad_text": ad.raw_ad_text,
        "page_number": ad.page_number or "",
        "deal_type": _deal_type(ad),
        "is_five_dollar_friday": _is_five_dollar_friday(ad),
        "deal_price": deal_price,
        "deal_price_display": f"${deal_price:.2f}" if deal_price is not None else "unclear",
        "size": size or "",
        "quantity": "",
        "normalized_unit": normalized_unit or "",
        "normalized_unit_price": normalized_unit_price,
        "costco_match_name": costco.costco_match_name or "",
        "costco_price": costco.costco_price,
        "costco_size": costco.costco_size or "",
        "costco_unit_price": costco.costco_unit_price,
        "percent_difference_vs_costco": costco.percent_difference_vs_costco,
        "costco_match_type": costco.match_type,
        "costco_match_confidence": costco.match_confidence,
        "market_all_time_low_unit_price": benchmark.market_all_time_low_unit_price,
        "market_90_day_low_unit_price": benchmark.market_90_day_low_unit_price,
        "market_median_unit_price": benchmark.market_median_unit_price,
        "percent_above_all_time_low": benchmark.percent_above_all_time_low,
        "percent_below_median": benchmark.percent_below_median,
        "historical_benchmark_bucket": benchmark.benchmark_bucket,
        "deal_bucket": scored.deal_bucket,
        "content_score": scored.content_score,
        "confidence": scored.confidence,
        "script_angle": scored.script_angle,
        "notes": match.content.notes,
        "skip_reason": scored.skip_reason,
        "unit_math_uncertain": unit_math_uncertain,
    }


def run_analysis(
    *,
    week: str,
    market_id: str,
    input_dir: Path,
    output_dir: Path,
) -> None:
    markets = load_markets()
    market = markets[market_id]
    watchlist = eligible_watchlist(load_content_watchlist(), market_id)

    ad_rows = load_ad_rows(
        input_dir,
        pdf_filename=market.ad_pdf_filename,
        banner_filter=market.banner_filter,
    )
    matches, unmatched = match_watchlist_rows(
        ad_rows,
        watchlist,
        canonical_display=CANONICAL_DISPLAY,
        family_display=FAMILY_DISPLAY,
    )

    costco_csv = input_dir / "costco_consolidated.csv"
    if not costco_csv.is_file():
        raise FileNotFoundError(f"Missing Costco file: {costco_csv}")

    week_end = _week_end(week)
    matched_rows: list[dict] = []
    skipped_rows: list[dict] = []

    for match in matches:
        matcher = _matcher_for(match.tracker_id, match.tracker_kind)
        row_dict = ad_row_to_price_dict(match.ad_row)
        normalized_unit_price = compute_normalized_unit_price(match.ad_row, matcher)
        unit_math_uncertain = (
            normalized_unit_price is None
            or (
                match.ad_row.package_size_min is None
                and match.ad_row.package_size_max is None
                and match.ad_row.package_unit in {None, "", "count", "each"}
                and match.tracker_kind == "canonical"
            )
        )

        meta = CANONICAL_PACKAGES.get(match.tracker_id) if match.tracker_kind == "canonical" else None
        normalized_unit = meta.unit_type if meta else (match.ad_row.package_unit or "unit")

        if match.content.track_historical_low:
            benchmark = compute_benchmark(
                match.tracker_id,
                match.tracker_kind,
                market.grocery_feed_id,
                normalized_unit_price,
                week_start=week,
            )
        else:
            from weekly_ad_analysis.benchmarks import HistoricalBenchmark

            benchmark = HistoricalBenchmark(
                None, None, None, None, None, None, "insufficient history", 0
            )

        if match.content.track_costco_comp and match.tracker_kind == "canonical":
            costco = compare_to_costco(
                canonical_id=match.tracker_id,
                grocer_price=match.ad_row.advertised_price,
                grocer_size_label=match.ad_row.package_text,
                costco_csv=costco_csv,
                costco_region_slug=market.costco_region_slug,
                grocery_feed_id=market.grocery_feed_id,
                grocery_store_label=market.retailer_label,
                costco_store_label=market.costco_comparison_label,
            )
        else:
            costco = CostcoMatchResult(
                None, None, None, None, None, None, "no comp", "low", None,
                "Costco comparison disabled for this content item",
            )

        scored = score_deal(
            match,
            normalized_unit_price=normalized_unit_price,
            unit_math_uncertain=unit_math_uncertain,
            costco=costco,
            benchmark=benchmark,
            retailer_label=market.retailer_label,
            is_five_dollar_friday=_is_five_dollar_friday(match.ad_row),
        )

        row = _build_row(
            match,
            market=market,
            week_start=week,
            week_end=week_end,
            costco=costco,
            benchmark=benchmark,
            scored=scored,
            normalized_unit_price=normalized_unit_price,
            normalized_unit=normalized_unit,
            unit_math_uncertain=unit_math_uncertain,
        )
        matched_rows.append(row)
        if scored.deal_bucket in {"Skip / not worth highlighting", "Not a Costco win"}:
            skipped_rows.append(row)

    write_all_outputs(
        output_dir,
        matched=matched_rows,
        skipped=skipped_rows,
        unmatched=[
            {
                "ad_item_name": row.ad_item_name,
                "raw_ad_text": row.raw_ad_text,
                "page_number": row.page_number,
            }
            for row in unmatched
        ],
        market_display_name=market.display_name,
        retailer_label=market.retailer_label,
        week_start=week,
        week_end=week_end,
    )
