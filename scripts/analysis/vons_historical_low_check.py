#!/usr/bin/env python3
"""Compare current Vons weekly-ad matches against historical Vons ad unit prices."""

from __future__ import annotations

import argparse
import csv
import glob
import os
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
from price_comparison.canonical_metadata import CANONICAL_PACKAGES  # noqa: E402
from weekly_ad_analysis.costco_match import compare_to_costco  # noqa: E402

DEFAULT_DATA_ROOT = Path.home() / "Documents" / "scrolling-the-aisle"
DATA_ROOT = Path(os.environ.get("SCROLLING_THE_AISLE_ROOT", DEFAULT_DATA_ROOT))

EXCLUDE_OFFER_RE = re.compile(
    r"beer|wine|vodka|whiskey|liquor|champagne|"
    r"paper towel|toilet paper|detergent|laundry|fabric softener|"
    r"shampoo|conditioner|pharmacy|vitamin|medicine|"
    r"dog food|cat food|litter|"
    r"cleaning|bleach|disinfect|"
    r"diaper|baby wipe|formula(?! bar)",
    re.I,
)

DELI_PARTY_RE = re.compile(r"party pack|party tray|50 piece|100 piece|150 piece", re.I)

OUTPUT_FIELDS = [
    "market",
    "ad_week_start",
    "ad_week_end",
    "tracker_key",
    "tracker_kind",
    "canonical_product_id",
    "family_key",
    "display_name",
    "brand",
    "current_offer_text",
    "current_price",
    "current_package_size",
    "current_unit",
    "current_unit_price",
    "historical_min_unit_price",
    "historical_median_unit_price",
    "historical_avg_unit_price",
    "weeks_seen",
    "rank_from_lowest",
    "pct_above_historical_low",
    "pct_below_median",
    "historical_label",
    "is_all_time_low",
    "is_tied_all_time_low",
    "is_near_low_5pct",
    "last_seen_at_or_below_current_price",
    "historical_low_offer_text",
    "costco_match_name",
    "costco_unit_price",
    "percent_difference_vs_costco",
    "summary_section",
    "confidence",
    "manual_review",
    "manual_review_reason",
]


@dataclass(frozen=True)
class TrackerMapping:
    tracker_key: str
    tracker_kind: str
    display_name: str
    category_group: str
    comparable_unit: str
    patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...]
    prefer_patterns: tuple[str, ...]
    costco_comparable: bool
    maps_to_canonical_id: str | None


@dataclass(frozen=True)
class NormalizedOffer:
    row: dict[str, str]
    unit_price: float | None
    unit: str | None
    manual_review: bool
    manual_review_reason: str | None
    confidence: str


def load_mappings(path: Path) -> list[TrackerMapping]:
    mappings: list[TrackerMapping] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            patterns = tuple(p.strip() for p in (raw.get("patterns") or "").split("|") if p.strip())
            if not patterns:
                continue
            exclude = tuple(
                p.strip() for p in (raw.get("exclude_patterns") or "").split("|") if p.strip()
            )
            prefer = tuple(
                p.strip() for p in (raw.get("prefer_patterns") or "").split("|") if p.strip()
            )
            canonical = (raw.get("maps_to_canonical_id") or "").strip() or None
            mappings.append(
                TrackerMapping(
                    tracker_key=raw["tracker_key"].strip(),
                    tracker_kind=raw["tracker_kind"].strip(),
                    display_name=raw["display_name"].strip(),
                    category_group=raw["category_group"].strip(),
                    comparable_unit=raw["comparable_unit"].strip(),
                    patterns=patterns,
                    exclude_patterns=exclude,
                    prefer_patterns=prefer,
                    costco_comparable=(raw.get("costco_comparable") or "").lower() == "true",
                    maps_to_canonical_id=canonical,
                )
            )
    return mappings


def mapping_matcher(mapping: TrackerMapping) -> ProductMatcher:
    return ProductMatcher(
        mapping.tracker_key,
        mapping.patterns,
        mapping.exclude_patterns,
        mapping.prefer_patterns,
    )


def row_matches_mapping(row: dict[str, str], mapping: TrackerMapping) -> bool:
    return matches(row, mapping_matcher(mapping))


def should_exclude_row(row: dict[str, str]) -> bool:
    text = row_text(row)
    if EXCLUDE_OFFER_RE.search(text):
        return True
    if row.get("split_status") == "excluded":
        return True
    if DELI_PARTY_RE.search(text) and "ben_jerrys" not in text.lower():
        return True
    return False


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(str(value).replace("$", "").strip())
    except ValueError:
        return None


def _avg_size(row: dict[str, str]) -> float | None:
    lo = _parse_float(row.get("package_size_min"))
    hi = _parse_float(row.get("package_size_max"))
    if lo is not None and hi is not None:
        return (lo + hi) / 2
    return lo or hi


def _offer_text(row: dict[str, str]) -> str:
    return " ".join(
        filter(
            None,
            [
                row.get("promo_text"),
                row.get("raw_offer_text"),
                row.get("split_product_text"),
                row.get("package_text"),
            ],
        )
    ).lower()


def _promo_text(row: dict[str, str]) -> str:
    return _offer_text(row)


def _effective_count_price(price: float, promo: str) -> tuple[float | None, str | None]:
    m = re.search(r"(\d+)\s*for\s*\$?\s*(\d+(?:\.\d+)?)", promo, re.I)
    if m:
        count = float(m.group(1))
        total = float(m.group(2))
        if count > 0:
            return round(total / count, 4), None
    m = re.search(r"(\d+)\s*/\s*\$?\s*(\d+(?:\.\d+)?)", promo, re.I)
    if m:
        count = float(m.group(1))
        total = float(m.group(2))
        if count > 0:
            return round(total / count, 4), None
    if re.search(r"2\s*for\s*\$?\s*5", promo, re.I):
        return round(2.5, 4), None
    if re.search(r"4\s*/\s*\$?\s*5|4\s+for\s+\$?\s*5", promo, re.I):
        return round(1.25, 4), None
    return None, None


def _bogo_effective_price(price: float, promo: str) -> tuple[float | None, str | None]:
    if re.search(r"buy\s*1\s*get\s*1\s*free|bogo", promo, re.I):
        return round(price / 2, 4), None
    m = re.search(r"buy\s*(\d+)\s*get\s*(\d+)\s*free", promo, re.I)
    if m:
        buy = int(m.group(1))
        free = int(m.group(2))
        total_units = buy + free
        if total_units > 0:
            return round((price * buy) / total_units, 4), None
    return None, None


def normalize_offer_unit_price(
    row: dict[str, str],
    mapping: TrackerMapping,
) -> NormalizedOffer:
    reasons: list[str] = []
    basis = (row.get("price_basis") or "").lower()
    promo = _promo_text(row)
    price = _parse_float(row.get("advertised_price"))
    unit = mapping.comparable_unit
    review_reasons = (row.get("review_reasons") or "").lower()

    if price is None:
        return NormalizedOffer(row, None, unit, True, "missing advertised price", "low")

    if "ambiguous_multi_product_offer" in review_reasons or row.get("split_status") == "group_not_split":
        reasons.append("multi-product offer")
    if "missing_package_size" in review_reasons and unit in {"oz", "each"}:
        reasons.append("missing package size")
    if "broad_group_needs_human_grounding" in review_reasons:
        reasons.append("broad grouped offer")

    # per-lb meat/produce
    if basis == "per_lb" or (row.get("package_unit") or "").lower() == "lb":
        return NormalizedOffer(row, round(price, 4), "lb", bool(reasons), "; ".join(reasons) or None, "high")

    count_price, _ = _effective_count_price(price, promo)
    if count_price is not None and unit in {"each", "ear", "can", "bar"}:
        if unit == "can" and count_price > 3:
            reasons.append("soda pack price may need manual review")
            return NormalizedOffer(row, None, unit, True, "; ".join(reasons), "low")
        conf = "medium" if reasons else "high"
        return NormalizedOffer(row, count_price, unit, bool(reasons), "; ".join(reasons) or None, conf)

    bogo_price, _ = _bogo_effective_price(price, promo)
    if bogo_price is not None:
        conf = "medium" if reasons else "high"
        return NormalizedOffer(row, bogo_price, unit, bool(reasons), "; ".join(reasons) or None, conf)

    # per oz from package size
    if unit == "oz":
        avg = _avg_size(row)
        pkg_text = row.get("package_text") or ""
        if not avg and pkg_text:
            m = re.search(r"(\d+(?:\.\d+)?)\s*oz", pkg_text.lower())
            if m:
                avg = float(m.group(1))
        if avg and avg > 0:
            per_pack = price
            if basis == "multi_buy":
                if "2 for" in promo:
                    per_pack = price / 2
                elif count_price is not None:
                    per_pack = count_price
            return NormalizedOffer(
                row,
                round(per_pack / avg, 4),
                "oz",
                bool(reasons),
                "; ".join(reasons) or None,
                "medium" if reasons else "high",
            )
        if basis == "multi_buy" and re.search(r"2\s*for\s*\$?\s*5", promo, re.I):
            reasons.append("multi-buy chip offer without package size")
            return NormalizedOffer(row, None, "oz", True, "; ".join(reasons), "low")
        reasons.append("cannot normalize to per oz")
        return NormalizedOffer(row, None, "oz", True, "; ".join(reasons), "low")

    if unit in {"each", "egg"}:
        avg = _avg_size(row)
        pkg_unit = (row.get("package_unit") or "").lower()
        if avg and avg > 1 and pkg_unit in {"ct", "ct.", "count", "each", "egg", "eggs"}:
            return NormalizedOffer(
                row,
                round(price / avg, 4),
                unit,
                bool(reasons),
                "; ".join(reasons) or None,
                "medium" if reasons else "high",
            )

    base = normalize_unit_price(row)
    if base is not None and unit in {"each", "bar", "bag", "can", "ear"}:
        conf = match_confidence(row, mapping_matcher(mapping)) or "medium"
        return NormalizedOffer(
            row,
            round(base, 4),
            unit,
            bool(reasons),
            "; ".join(reasons) or None,
            conf,
        )

    if base is not None:
        conf = match_confidence(row, mapping_matcher(mapping)) or "medium"
        return NormalizedOffer(row, round(base, 4), unit, bool(reasons), "; ".join(reasons) or None, conf)

    reasons.append("unable to normalize unit price")
    return NormalizedOffer(row, None, unit, True, "; ".join(reasons), "low")


def load_split_rows(paths: list[Path], *, banner: str = "Vons") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    banner_norm = banner.strip().lower()
    for path in paths:
        if not path.is_file():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if (row.get("banner") or "").strip().lower() != banner_norm:
                    continue
                if should_exclude_row(row):
                    continue
                item_id = row.get("split_item_id") or ""
                dedupe_key = item_id or "|".join(
                    [
                        row.get("week_start", ""),
                        row.get("split_product_text", ""),
                        row.get("advertised_price", ""),
                        row.get("raw_offer_text", ""),
                    ]
                )
                if dedupe_key in seen_ids:
                    continue
                seen_ids.add(dedupe_key)
                rows.append(row)
    return rows


def guess_brand(text: str) -> str:
    brands = [
        "Fage", "Chobani", "Oikos", "Tillamook", "Häagen-Dazs", "Haagen-Dazs",
        "Nature Valley", "Doritos", "Cheetos", "Lay's", "Lays", "Tostitos",
        "Oreo", "Ritz", "Cheez-It", "Goldfish", "Kettle Brand", "Cheerios",
        "Coca-Cola", "Pepsi", "Sprite", "Ben & Jerry", "Outshine",
    ]
    lower = text.lower()
    for brand in brands:
        if brand.lower() in lower:
            return brand
    return ""


def pick_best_row_for_mapping(
    rows: list[dict[str, str]],
    mapping: TrackerMapping,
) -> dict[str, str] | None:
    matcher = mapping_matcher(mapping)
    candidates = [row for row in rows if row_matches_mapping(row, mapping)]
    if not candidates:
        return None
    return max(candidates, key=lambda row: preference_score(row, matcher))


def build_weekly_series(
    historical_rows: list[dict[str, str]],
    mapping: TrackerMapping,
) -> list[tuple[str, float, str]]:
    by_week: dict[str, list[dict[str, str]]] = {}
    for row in historical_rows:
        week = row.get("week_start") or ""
        if not week:
            continue
        if not row_matches_mapping(row, mapping):
            continue
        by_week.setdefault(week, []).append(row)

    series: list[tuple[str, float, str]] = []
    for week in sorted(by_week):
        best = pick_best_row_for_mapping(by_week[week], mapping)
        if best is None:
            continue
        normalized = normalize_offer_unit_price(best, mapping)
        if normalized.unit_price is None or normalized.manual_review:
            continue
        if normalized.confidence == "low":
            continue
        offer_text = best.get("split_product_text") or best.get("raw_offer_text") or ""
        series.append((week, normalized.unit_price, offer_text))
    return series


def historical_stats(series: list[tuple[str, float, str]]) -> dict:
    if not series:
        return {
            "min": None,
            "median": None,
            "avg": None,
            "weeks_seen": 0,
            "low_week": None,
            "low_offer_text": None,
        }
    prices = [price for _, price, _ in series]
    sorted_prices = sorted(prices)
    mid = len(sorted_prices) // 2
    if len(sorted_prices) % 2:
        median = sorted_prices[mid]
    else:
        median = round((sorted_prices[mid - 1] + sorted_prices[mid]) / 2, 4)
    min_price = min(prices)
    low_week = None
    low_offer = None
    for week, price, text in series:
        if price == min_price:
            low_week = week
            low_offer = text
            break
    return {
        "min": min_price,
        "median": median,
        "avg": round(sum(prices) / len(prices), 4),
        "weeks_seen": len(series),
        "low_week": low_week,
        "low_offer_text": low_offer,
    }


def retailer_short_name(banner: str) -> str:
    return "Safeway" if banner.strip().lower() == "safeway" else "Vons"


def summary_section_labels(retailer_short: str) -> dict[str, str]:
    return {
        "all_time_low": f"All-time low {retailer_short} buys",
        "near_all_time_low": "Near all-time low",
        "good_buy": f"Good {retailer_short} buy, no Costco comp",
        "costco_parity": f"On par with Costco, {retailer_short} wins on variety",
        "costco_wins": "Costco still wins",
        "manual_review": "Manual review needed",
    }


def classify_historical(current: float, stats: dict, series: list[tuple[str, float, str]] | None = None) -> dict:
    min_price = stats["min"]
    median = stats["median"]
    weeks = stats["weeks_seen"]
    eps = 0.005

    if min_price is None or weeks < 2:
        return {
            "historical_label": "insufficient history",
            "is_all_time_low": False,
            "is_tied_all_time_low": False,
            "is_near_low_5pct": False,
            "pct_above_historical_low": None,
            "pct_below_median": None,
            "rank_from_lowest": None,
        }

    pct_above = round(((current - min_price) / min_price) * 100, 2) if min_price > 0 else None
    pct_below_median = (
        round(((median - current) / median) * 100, 2) if median and median > 0 else None
    )

    is_tied = abs(current - min_price) <= max(min_price * eps, 0.001)
    is_all_time = current < min_price - max(min_price * eps, 0.001)
    is_near = not is_all_time and not is_tied and current <= min_price * 1.05

    if is_all_time:
        label = "all-time low"
    elif is_tied:
        label = "tied all-time low"
    elif is_near:
        label = "within 5% of all-time low"
    elif median is not None and current < median * 0.97:
        label = "historically good but not near low"
    else:
        label = "not special historically"

    all_prices = sorted(price for _, price, _ in (series or [])) + [round(current, 4)]
    all_prices = sorted(set(all_prices))
    rank = all_prices.index(round(current, 4)) + 1 if round(current, 4) in all_prices else None

    return {
        "historical_label": label,
        "is_all_time_low": is_all_time,
        "is_tied_all_time_low": is_tied,
        "is_near_low_5pct": is_near or is_all_time or is_tied,
        "pct_above_historical_low": pct_above,
        "pct_below_median": pct_below_median,
        "rank_from_lowest": rank,
    }


def last_seen_at_or_below(current: float, series: list[tuple[str, float, str]]) -> str | None:
    eligible = [week for week, price, _ in series if price <= current + 0.001]
    return eligible[-1] if eligible else None


def summary_section(
    *,
    manual_review: bool,
    historical_label: str,
    costco_pct: float | None,
    costco_comparable: bool,
    section_labels: dict[str, str],
) -> str:
    if manual_review:
        return section_labels["manual_review"]
    if historical_label in {"all-time low", "tied all-time low"}:
        return section_labels["all_time_low"]
    if historical_label == "within 5% of all-time low":
        return section_labels["near_all_time_low"]
    if costco_comparable and costco_pct is not None:
        if costco_pct <= 0:
            return section_labels["costco_parity"]
        if costco_pct > 15:
            return section_labels["costco_wins"]
    if historical_label == "historically good but not near low":
        return section_labels["good_buy"]
    if costco_comparable and costco_pct is not None and costco_pct > 15:
        return section_labels["costco_wins"]
    if historical_label == "not special historically":
        return section_labels["manual_review"] if costco_pct is None else section_labels["costco_wins"]
    return section_labels["good_buy"]


def rank_candidates(rows: list[dict]) -> list[dict]:
    def sort_key(row: dict) -> tuple:
        atl = 0 if row.get("is_all_time_low") else 1
        tied = 0 if row.get("is_tied_all_time_low") else 1
        near = 0 if row.get("is_near_low_5pct") else 1
        below_med = -(row.get("pct_below_median") or 0)
        costco_adv = -(row.get("percent_difference_vs_costco") or 0)
        return (atl, tied, near, below_med, costco_adv)

    return sorted(rows, key=sort_key)


def discover_historical_paths(data_root: Path, *, banner: str = "Vons") -> list[Path]:
    subdir = "product_discovery_vons" if banner.strip().lower() == "vons" else "product_discovery_safeway"
    market_folder = "socal_oc" if banner.strip().lower() == "vons" else "bay_area"
    patterns = [
        data_root / f"outputs/{subdir}/split_offer_items.csv",
        data_root / f"outputs/{subdir}_*/split_offer_items.csv",
        ROOT / f"data/weekly_ads/*/{market_folder}/split_offer_items.csv",
    ]
    paths: list[Path] = []
    for pattern in patterns:
        if "*" in str(pattern):
            paths.extend(Path(p) for p in glob.glob(str(pattern)))
        elif pattern.is_file():
            paths.append(pattern)
    return sorted(set(paths))


def run_check(
    *,
    current_week_start: str,
    current_week_end: str,
    current_split_csv: Path,
    historical_paths: list[Path],
    mappings_path: Path,
    costco_csv: Path | None,
    output_csv: Path,
    output_md: Path,
    market: str = "socal_oc",
    banner: str = "Vons",
    retailer_label: str = "Vons / Albertsons",
    costco_region_slug: str = "tustin",
    grocery_feed_id: str = "vons_albertsons_socal",
    costco_store_label: str = "SoCal Costco",
) -> list[dict]:
    mappings = load_mappings(mappings_path)
    retailer_short = retailer_short_name(banner)
    section_labels = summary_section_labels(retailer_short)
    current_rows = load_split_rows([current_split_csv], banner=banner)
    current_rows = [r for r in current_rows if (r.get("week_start") or "") == current_week_start]

    historical_all = load_split_rows(historical_paths, banner=banner)
    historical_rows = [
        r for r in historical_all if (r.get("week_start") or "") != current_week_start
    ]

    results: list[dict] = []
    for mapping in mappings:
        current_best = pick_best_row_for_mapping(current_rows, mapping)
        if current_best is None:
            continue

        normalized = normalize_offer_unit_price(current_best, mapping)
        series = build_weekly_series(historical_rows, mapping)
        stats = historical_stats(series)

        current_price = _parse_float(current_best.get("advertised_price"))
        package_text = current_best.get("package_text") or ""
        offer_text = current_best.get("split_product_text") or current_best.get("raw_offer_text") or ""

        hist = (
            classify_historical(normalized.unit_price, stats, series)
            if normalized.unit_price is not None and not normalized.manual_review
            else {
                "historical_label": "insufficient history",
                "is_all_time_low": False,
                "is_tied_all_time_low": False,
                "is_near_low_5pct": False,
                "pct_above_historical_low": None,
                "pct_below_median": None,
                "rank_from_lowest": None,
            }
        )

        canonical_id = mapping.maps_to_canonical_id or (
            mapping.tracker_key if mapping.tracker_kind == "canonical" else ""
        )
        family_key = mapping.tracker_key if mapping.tracker_kind == "family" else ""

        costco_name = ""
        costco_unit = None
        costco_pct = None
        if mapping.costco_comparable and canonical_id and costco_csv and costco_csv.is_file():
            costco = compare_to_costco(
                canonical_id=canonical_id,
                grocer_price=current_price,
                grocer_size_label=package_text,
                costco_csv=costco_csv,
                costco_region_slug=costco_region_slug,
                grocery_feed_id=grocery_feed_id,
                grocery_store_label=retailer_label,
                costco_store_label=costco_store_label,
            )
            costco_name = costco.costco_match_name or ""
            costco_unit = costco.costco_unit_price
            costco_pct = costco.percent_difference_vs_costco

        manual = normalized.manual_review or normalized.unit_price is None
        manual_reason = normalized.manual_review_reason or (
            "unable to normalize unit price" if normalized.unit_price is None else ""
        )

        section = summary_section(
            manual_review=manual,
            historical_label=hist["historical_label"],
            costco_pct=costco_pct,
            costco_comparable=mapping.costco_comparable and bool(canonical_id),
            section_labels=section_labels,
        )

        results.append(
            {
                "market": market,
                "ad_week_start": current_week_start,
                "ad_week_end": current_week_end,
                "tracker_key": mapping.tracker_key,
                "tracker_kind": mapping.tracker_kind,
                "canonical_product_id": canonical_id if mapping.tracker_kind != "family" else "",
                "family_key": family_key,
                "display_name": mapping.display_name,
                "brand": guess_brand(offer_text),
                "current_offer_text": offer_text,
                "current_price": current_price,
                "current_package_size": package_text,
                "current_unit": normalized.unit,
                "current_unit_price": normalized.unit_price,
                "historical_min_unit_price": stats["min"],
                "historical_median_unit_price": stats["median"],
                "historical_avg_unit_price": stats["avg"],
                "weeks_seen": stats["weeks_seen"],
                "rank_from_lowest": hist["rank_from_lowest"],
                "pct_above_historical_low": hist["pct_above_historical_low"],
                "pct_below_median": hist["pct_below_median"],
                "historical_label": hist["historical_label"],
                "is_all_time_low": hist["is_all_time_low"],
                "is_tied_all_time_low": hist["is_tied_all_time_low"],
                "is_near_low_5pct": hist["is_near_low_5pct"],
                "last_seen_at_or_below_current_price": last_seen_at_or_below(
                    normalized.unit_price or 999999, series
                )
                if normalized.unit_price is not None
                else None,
                "historical_low_offer_text": stats["low_offer_text"],
                "costco_match_name": costco_name,
                "costco_unit_price": costco_unit,
                "percent_difference_vs_costco": costco_pct,
                "summary_section": section,
                "confidence": normalized.confidence,
                "manual_review": manual,
                "manual_review_reason": manual_reason,
            }
        )

    ranked = rank_candidates([r for r in results if not r.get("manual_review")]) + [
        r for r in results if r.get("manual_review")
    ]
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in ranked:
            writer.writerow(row)

    write_summary_md(
        output_md,
        ranked=ranked,
        current_week_start=current_week_start,
        current_week_end=current_week_end,
        retailer_label=retailer_label,
        market_label=market,
        section_labels=section_labels,
    )
    return ranked


def write_summary_md(
    path: Path,
    *,
    ranked: list[dict],
    current_week_start: str,
    current_week_end: str,
    retailer_label: str = "Vons / Albertsons",
    market_label: str = "socal_oc",
    section_labels: dict[str, str] | None = None,
) -> None:
    labels = section_labels or summary_section_labels(retailer_short_name("Vons"))
    sections = [
        labels["all_time_low"],
        labels["near_all_time_low"],
        labels["good_buy"],
        labels["costco_parity"],
        labels["costco_wins"],
        labels["manual_review"],
    ]
    lines = [
        f"# {retailer_label} historical-low summary — week of {current_week_start}",
        "",
        f"**Market:** {market_label}",
        f"**Retailer:** {retailer_label}",
        f"**Ad week:** {current_week_start} → {current_week_end}",
        f"**Historical baseline:** prior {retailer_label} weekly ads only (same retailer, not cross-store).",
        "",
    ]
    for section in sections:
        items = [r for r in ranked if r.get("summary_section") == section]
        lines.append(f"## {section}")
        lines.append("")
        if not items:
            lines.append("_None this week._")
            lines.append("")
            continue
        for item in items:
            price = item.get("current_unit_price")
            unit = item.get("current_unit") or "unit"
            hist = item.get("historical_label")
            lines.append(f"### {item.get('display_name')}")
            lines.append(f"- **Offer:** {item.get('current_offer_text')}")
            if price is not None:
                lines.append(f"- **Unit price:** ${price:.2f} / {unit}")
            lines.append(f"- **History:** {hist} ({item.get('weeks_seen')} prior weeks tracked)")
            if item.get("pct_below_median") is not None:
                lines.append(f"- **Vs median:** {item.get('pct_below_median')}% below median")
            if item.get("costco_match_name"):
                lines.append(
                    f"- **Costco:** {item.get('costco_match_name')} "
                    f"({item.get('percent_difference_vs_costco')}% vs Costco unit)"
                )
            if item.get("manual_review_reason"):
                lines.append(f"- **Review:** {item.get('manual_review_reason')}")
            lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vons historical low check for STA food watchlist.")
    parser.add_argument("--week-start", default="2026-07-01")
    parser.add_argument("--week-end", default="2026-07-07")
    parser.add_argument(
        "--current-split-csv",
        type=Path,
        default=ROOT / "data/weekly_ads/2026-07-01/socal_oc/split_offer_items.csv",
    )
    parser.add_argument(
        "--historical-glob",
        action="append",
        default=[],
        help="Extra split_offer_items.csv paths (repeatable)",
    )
    parser.add_argument(
        "--mappings",
        type=Path,
        default=ROOT / "config/vons_historical_low_category_mappings.csv",
    )
    parser.add_argument(
        "--costco-csv",
        type=Path,
        default=ROOT / "data/weekly_ads/2026-07-01/socal_oc/costco_consolidated.csv",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=ROOT / "outputs/vons_2026-07-01_historical_low_candidates.csv",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "outputs/vons_2026-07-01_historical_low_summary.md",
    )
    parser.add_argument("--market", default="socal_oc")
    parser.add_argument("--banner", default="Vons", choices=["Vons", "Safeway"])
    parser.add_argument("--retailer-label", default="Vons / Albertsons")
    parser.add_argument("--costco-region-slug", default="tustin")
    parser.add_argument("--grocery-feed-id", default="vons_albertsons_socal")
    parser.add_argument("--costco-store-label", default="SoCal Costco")
    parser.add_argument("--top", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    historical_paths = discover_historical_paths(DATA_ROOT, banner=args.banner)
    historical_paths.extend(args.historical_glob)
    historical_paths = sorted(set(Path(p) for p in historical_paths))

    ranked = run_check(
        current_week_start=args.week_start,
        current_week_end=args.week_end,
        current_split_csv=args.current_split_csv,
        historical_paths=historical_paths,
        mappings_path=args.mappings,
        costco_csv=args.costco_csv if args.costco_csv.is_file() else None,
        output_csv=args.output_csv,
        output_md=args.output_md,
        market=args.market,
        banner=args.banner,
        retailer_label=args.retailer_label,
        costco_region_slug=args.costco_region_slug,
        grocery_feed_id=args.grocery_feed_id,
        costco_store_label=args.costco_store_label,
    )

    print(f"Wrote {args.output_csv} ({len(ranked)} matches)")
    print(f"Wrote {args.output_md}")
    print("")
    print(f"Top {args.top} candidates:")
    for idx, row in enumerate(ranked[: args.top], start=1):
        price = row.get("current_unit_price")
        unit = row.get("current_unit") or "unit"
        costco_pct = row.get("percent_difference_vs_costco")
        costco_label = f"{costco_pct}%" if costco_pct is not None else "n/a"
        med = row.get("pct_below_median")
        med_label = f"{med}%" if med is not None else "n/a"
        if price is not None:
            print(
                f"{idx:2}. {row.get('display_name')} — "
                f"{row.get('historical_label')} — "
                f"${price:.2f}/{unit} "
                f"(median save {med_label}, Costco {costco_label})"
            )
        else:
            print(f"{idx:2}. {row.get('display_name')} — manual review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
