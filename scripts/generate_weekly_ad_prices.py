#!/usr/bin/env python3
"""Generate weekly ad prices for the staging price tracker.

Reads Safeway and Vons flyer manifests from data/weekly_ads/ and offer rows from the
scrolling-the-aisle repo (split_offer_items.csv). Writes
src/data/weeklyAdPrices.generated.ts and src/data/vonsWeeklyAdPrices.generated.ts.

Historical weekly ad extraction is cached in split_offer_items.csv (sibling repo).
This script only reads that cache — it never re-OCRs or re-extracts PDFs.

Usage:
  python3 scripts/generate_weekly_ad_prices.py                    # full rematch (default)
  python3 scripts/generate_weekly_ad_prices.py --product-id grapes
  python3 scripts/generate_weekly_ad_prices.py --product-ids grapes,eggs_18_count
  python3 scripts/generate_weekly_ad_prices.py --new-only         # products missing from output
  python3 scripts/generate_weekly_ad_prices.py --family-id ben_jerrys_ice_cream
  python3 scripts/generate_weekly_ad_prices.py --dry-run
  SCROLLING_THE_AISLE_ROOT=/path/to/scrolling-the-aisle python3 scripts/generate_weekly_ad_prices.py
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.artifacts import (  # noqa: E402
    MergeSummary,
    merge_week_prices,
    merge_weeks_list,
    parse_family_ts,
    parse_ts_export,
    product_ids_missing_from_prices,
)
from price_tracker.canonical_families import (  # noqa: E402
    LEGACY_CANONICAL_TO_FAMILY,
    load_families,
)
from price_tracker.canonical_match_audit import (  # noqa: E402
    AuditRecord,
    CanonicalMatchAuditCollector,
    write_all_audits,
)
from price_tracker.canonical_match_eligibility import EligibilityIndex  # noqa: E402
from price_tracker.normalization import normalize_price  # noqa: E402
from price_tracker.weekly_ad_preview import (  # noqa: E402
    build_feed_preview_summary,
    format_preview_summary,
    validate_tracker_product_ids_unchanged,
)
from price_tracker.yaml_matchers import build_yaml_matchers, tracker_family_ids  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = Path.home() / "Documents" / "scrolling-the-aisle"
DATA_ROOT = Path(os.environ.get("SCROLLING_THE_AISLE_ROOT", DEFAULT_DATA_ROOT))


@dataclass(frozen=True)
class ProductMatcher:
    canonical_id: str
    patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...] = ()
    prefer_patterns: tuple[str, ...] = ()


TRACKER_CANONICAL_IDS = tracker_family_ids()

_YAML_MATCHERS = build_yaml_matchers()


def _yaml_matchers_by_id() -> dict[str, ProductMatcher]:
    return {
        matcher.canonical_id: ProductMatcher(
            matcher.canonical_id,
            matcher.patterns,
            matcher.exclude_patterns,
            matcher.prefer_patterns,
        )
        for matcher in _YAML_MATCHERS
    }


MATCHERS: tuple[ProductMatcher, ...] = tuple(_yaml_matchers_by_id().values())

_NORMALIZATION_BY_ID = {m.canonical_id: m.normalization for m in _YAML_MATCHERS}
_PICK_LOWEST_BY_ID = {m.canonical_id: m.pick_lowest_in_week for m in _YAML_MATCHERS}

TRACKER_FAMILY_IDS: list[str] = []


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


def pattern_hit_rows(
    rows: list[dict[str, str]], matcher: ProductMatcher
) -> list[dict[str, str]]:
    """Rows whose split text hits include patterns (ignoring exclude list)."""
    hits: list[dict[str, str]] = []
    for row in rows:
        text = split_text(row)
        if any(re.search(pattern, text) for pattern in matcher.patterns):
            hits.append(row)
    return hits


def parse_price(value: str | None) -> float | None:
    if not value or value in {"$", ""}:
        return None
    cleaned = value.replace("$", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_unit_price(
    row: dict[str, str], matcher: ProductMatcher | None = None
) -> float | None:
    rule = _NORMALIZATION_BY_ID.get(matcher.canonical_id) if matcher else None
    return normalize_price(row, rule)


def preference_score(row: dict[str, str], matcher: ProductMatcher) -> int:
    text = split_text(row)
    full = row_text(row)
    score = 0
    for index, pattern in enumerate(matcher.prefer_patterns):
        if re.search(pattern, text) or re.search(pattern, full):
            score = max(score, (len(matcher.prefer_patterns) - index) * 10)
    price = normalize_unit_price(row, matcher)
    if price is not None:
        score += 1
    return score


def match_confidence(row: dict[str, str], matcher: ProductMatcher) -> str | None:
    if normalize_unit_price(row, matcher) is None:
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

    if matcher.canonical_id == "strawberries_1_2lb" and re.search(r"large pack|2 lb", full):
        confidence = "medium"
    if matcher.canonical_id == "chobani_yogurt_per_cup":
        price = normalize_unit_price(row, matcher)
        if price is not None and price < 3:
            confidence = "medium"
        elif re.search(r"5\.3|4-5\.3|cup", full):
            confidence = "medium"
    if matcher.canonical_id == "tillamook_ice_cream" and re.search(r"48-oz", full):
        confidence = "medium"

    return confidence


def _historical_low(
    prices: dict[str, dict[str, object | None]], family_id: str, before_week: str
) -> float | None:
    weeks = prices.get(family_id) or {}
    values: list[float] = []
    for week_start, entry in weeks.items():
        if week_start >= before_week:
            continue
        price = entry.get("price") if isinstance(entry, dict) else None
        if isinstance(price, (int, float)):
            values.append(float(price))
    return min(values) if values else None


def _prior_week_price(
    prices: dict[str, dict[str, object | None]], family_id: str, week_start: str
) -> float | None:
    weeks = prices.get(family_id) or {}
    prior_weeks = sorted(ws for ws in weeks if ws < week_start)
    if not prior_weeks:
        return None
    entry = weeks[prior_weeks[-1]]
    price = entry.get("price") if isinstance(entry, dict) else None
    return float(price) if isinstance(price, (int, float)) else None


def _audit_metadata_kwargs(elig: object) -> dict[str, object]:
    """Copy canonical display / provenance metadata from an eligibility result."""
    return {
        "display_name": getattr(elig, "display_name", None),
        "subtitle": getattr(elig, "subtitle", None),
        "manufacturer_family": getattr(elig, "manufacturer_family", None),
        "allowed_product_lines": list(getattr(elig, "allowed_product_lines", []) or []),
        "package_type": getattr(elig, "package_type", None),
        "size_range": getattr(elig, "size_range", None),
        "eligible_item_examples": list(
            getattr(elig, "eligible_item_examples", []) or []
        ),
    }


def pick_best_row(
    rows: list[dict[str, str]],
    matcher: ProductMatcher,
    *,
    eligibility: EligibilityIndex | None = None,
    feed_label: str | None = None,
    week_start: str | None = None,
    week_end: str | None = None,
    prior_price: float | None = None,
    historical_low: float | None = None,
    audit_collector: CanonicalMatchAuditCollector | None = None,
) -> dict[str, str] | None:
    candidates = [row for row in rows if matches(row, matcher)]
    if not candidates:
        # Audit near-matches blocked by exclude patterns or with no eligible candidate.
        if eligibility is not None and audit_collector and feed_label and week_start and week_end:
            for row in pattern_hit_rows(rows, matcher):
                conf_label = match_confidence(row, matcher)
                elig = eligibility.evaluate(
                    row,
                    matcher.canonical_id,
                    keyword_confidence=conf_label,
                    prior_price=prior_price,
                    historical_low=historical_low,
                )
                if elig.match_decision != "accepted":
                    unit_price = normalize_unit_price(row, matcher)
                    audit_collector.add(
                        AuditRecord(
                            week_start=week_start,
                            week_end=week_end,
                            feed=feed_label,
                            family_id=matcher.canonical_id,
                            offer_text=row.get("split_product_text")
                            or row.get("raw_offer_text")
                            or "",
                            price=unit_price,
                            match_decision=elig.match_decision,
                            match_confidence=elig.match_confidence,
                            match_reason=elig.match_reason,
                            reject_reason=elig.reject_reason,
                            canonical_intent=elig.canonical_intent,
                            ad_product_type=elig.ad_product_type,
                            hard_negative_hits=list(elig.hard_negative_hits),
                            output_class=elig.output_class,
                            updated_tracker=False,
                            graph_preview_change=(
                                f"blocked ${unit_price} — {elig.reject_reason}"
                                if unit_price is not None
                                else elig.reject_reason
                            ),
                            **_audit_metadata_kwargs(elig),
                        )
                    )
                    break
        return None

    if _PICK_LOWEST_BY_ID.get(matcher.canonical_id):

        def normalized_price(row: dict[str, str]) -> float:
            value = normalize_unit_price(row, matcher)
            return value if value is not None else float("inf")

        ranked = sorted(candidates, key=normalized_price)
    else:
        ranked = sorted(candidates, key=lambda row: preference_score(row, matcher), reverse=True)

    best_row: dict[str, str] | None = None
    best_eligibility = None
    audit_row: dict[str, str] | None = None

    for row in ranked:
        conf_label = match_confidence(row, matcher)
        if eligibility is not None:
            elig = eligibility.evaluate(
                row,
                matcher.canonical_id,
                keyword_confidence=conf_label,
                prior_price=prior_price,
                historical_low=historical_low,
            )
        else:
            from price_tracker.canonical_match_eligibility import MatchEligibilityResult

            elig = MatchEligibilityResult(
                match_decision="accepted",
                match_confidence=0.7,
                match_reason="legacy pattern match",
            )

        if elig.match_decision == "accepted":
            best_row = row
            best_eligibility = elig
            audit_row = row
            break

        if audit_row is None:
            audit_row = row
            best_eligibility = elig

    if (
        audit_collector
        and feed_label
        and week_start
        and week_end
        and audit_row is not None
        and best_eligibility is not None
    ):
        unit_price = normalize_unit_price(audit_row, matcher)
        audit_collector.add(
            AuditRecord(
                week_start=week_start,
                week_end=week_end,
                feed=feed_label,
                family_id=matcher.canonical_id,
                offer_text=audit_row.get("split_product_text")
                or audit_row.get("raw_offer_text")
                or "",
                price=unit_price,
                match_decision=best_eligibility.match_decision,
                match_confidence=best_eligibility.match_confidence,
                match_reason=best_eligibility.match_reason,
                reject_reason=best_eligibility.reject_reason,
                canonical_intent=best_eligibility.canonical_intent,
                ad_product_type=best_eligibility.ad_product_type,
                hard_negative_hits=list(best_eligibility.hard_negative_hits),
                output_class=best_eligibility.output_class,
                updated_tracker=best_eligibility.match_decision == "accepted",
                all_time_low_change=(
                    unit_price is not None
                    and historical_low is not None
                    and unit_price < historical_low
                    and best_eligibility.match_decision == "accepted"
                ),
                graph_preview_change=(
                    f"blocked ${unit_price} — {best_eligibility.reject_reason}"
                    if best_eligibility.match_decision != "accepted"
                    and unit_price is not None
                    else None
                ),
                **_audit_metadata_kwargs(best_eligibility),
            )
        )

    return best_row


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
    *,
    family_ids: set[str] | None = None,
) -> tuple[
    list[dict[str, str]],
    dict[str, dict[str, dict[str, object | None]]],
    dict[str, dict[str, dict[str, dict[str, object | None]]]],
]:
    target_families = family_ids if family_ids is not None else set(TRACKER_FAMILY_IDS)
    family_matchers = [m for m in FAMILY_MATCHERS if m.canonical_id in target_families]
    member_matchers = [m for m in FAMILY_MEMBER_MATCHERS if m.family_id in target_families]

    weeks: list[dict[str, str]] = []
    family_prices: dict[str, dict[str, dict[str, object | None]]] = {
        family_id: {} for family_id in target_families
    }
    member_prices: dict[str, dict[str, dict[str, dict[str, object | None]]]] = {
        family_id: {} for family_id in target_families
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

        for matcher in family_matchers:
            best = pick_best_row(week_rows, matcher)
            if best is None:
                family_prices[matcher.canonical_id][week_start] = {
                    "price": None,
                    "offerText": None,
                    "confidence": None,
                    "availabilityType": None,
                    "promoNote": None,
                }
                continue

            family_prices[matcher.canonical_id][week_start] = {
                "price": normalize_unit_price(best, matcher),
                "offerText": best.get("split_product_text")
                or best.get("raw_offer_text"),
                "confidence": match_confidence(best, matcher),
                "availabilityType": best.get("availability_type_guess") or None,
                "promoNote": best.get("promo_text") or None,
            }

        for matcher in member_matchers:
            member_bucket = member_prices.setdefault(matcher.family_id, {})
            member_weeks = member_bucket.setdefault(matcher.member_id, {})
            best = pick_best_member_row(week_rows, matcher)
            if best is None:
                member_weeks[week_start] = {
                    "price": None,
                    "offerText": None,
                    "confidence": None,
                    "availabilityType": None,
                    "promoNote": None,
                }
                continue

            pseudo = ProductMatcher(
                matcher.family_id,
                matcher.patterns,
                matcher.exclude_patterns,
                matcher.prefer_patterns,
            )
            member_weeks[week_start] = {
                "price": normalize_unit_price(best, pseudo),
                "offerText": best.get("split_product_text")
                or best.get("raw_offer_text"),
                "confidence": match_confidence(best, pseudo),
                "availabilityType": best.get("availability_type_guess") or None,
                "promoNote": best.get("promo_text") or None,
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
    *,
    product_ids: set[str] | None = None,
    eligibility: EligibilityIndex | None = None,
    audit_collector: CanonicalMatchAuditCollector | None = None,
) -> tuple[list[dict[str, str]], dict[str, dict[str, dict[str, object | None]]]]:
    target_ids = product_ids if product_ids is not None else set(TRACKER_CANONICAL_IDS)
    matchers = [m for m in MATCHERS if m.canonical_id in target_ids]

    weeks: list[dict[str, str]] = []
    prices: dict[str, dict[str, dict[str, object | None]]] = {
        canonical_id: {} for canonical_id in target_ids
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

        for matcher in matchers:
            prior = _prior_week_price(prices, matcher.canonical_id, week_start)
            hist_low = _historical_low(prices, matcher.canonical_id, week_start)
            best = pick_best_row(
                week_rows,
                matcher,
                eligibility=eligibility,
                feed_label=feed_label,
                week_start=week_start,
                week_end=week_end,
                prior_price=prior,
                historical_low=hist_low,
                audit_collector=audit_collector,
            )
            if best is None:
                prices[matcher.canonical_id][week_start] = {
                    "price": None,
                    "offerText": None,
                    "confidence": None,
                    "availabilityType": None,
                    "promoNote": None,
                }
                continue

            prices[matcher.canonical_id][week_start] = {
                "price": normalize_unit_price(best, matcher),
                "offerText": best.get("split_product_text")
                or best.get("raw_offer_text"),
                "confidence": match_confidence(best, matcher),
                "availabilityType": best.get("availability_type_guess") or None,
                "promoNote": best.get("promo_text") or None,
            }

    return weeks, prices


def merge_legacy_prices(
    prices: dict[str, dict[str, dict[str, object | None]]],
    legacy_prices: dict[str, dict[str, dict[str, object | None]]] | None,
) -> int:
    """Copy historical weekly rows from old canonical ids into mapped YAML families."""
    if not legacy_prices:
        return 0
    copied = 0
    for legacy_id, family_id in LEGACY_CANONICAL_TO_FAMILY.items():
        legacy_weeks = legacy_prices.get(legacy_id)
        if not legacy_weeks:
            continue
        target = prices.setdefault(family_id, {})
        for week_start, entry in legacy_weeks.items():
            if entry.get("price") is None:
                continue
            existing = target.get(week_start)
            if existing is None or existing.get("price") is None:
                target[week_start] = dict(entry)
                copied += 1
    return copied


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
  availabilityType?: string | null;
  promoNote?: string | null;
}};

export const {export_weeks}: WeeklyAdWeek[] = {weeks_json};

export const {export_prices}: Record<
  string,
  Record<string, GeneratedWeeklyAdPrice>
> = {prices_json};
"""


FAMILY_OUTPUT = ROOT / "src" / "data" / "familyWeeklyAdPrices.generated.ts"

FEED_TS_KEYS = {
    "Safeway": ("WEEKLY_AD_WEEKS", "WEEKLY_AD_PRICES"),
    "Vons": ("VONS_WEEKLY_AD_WEEKS", "VONS_WEEKLY_AD_PRICES"),
}


@dataclass
class RunOptions:
    product_ids: set[str] | None = None
    family_ids: set[str] | None = None
    full_rematch: bool = True
    new_only: bool = False
    dry_run: bool = False
    feeds: set[str] | None = None  # {"Safeway", "Vons"}
    as_of: date | None = None
    audit_collector: CanonicalMatchAuditCollector | None = None


def feed_weeks_key(feed_label: str) -> str:
    return FEED_TS_KEYS[feed_label][0]


def feed_prices_key(feed_label: str) -> str:
    return FEED_TS_KEYS[feed_label][1]


def resolve_run_options(args: argparse.Namespace) -> RunOptions:
    product_ids: set[str] | None = None
    family_ids: set[str] | None = None

    if args.product_id:
        product_ids = {args.product_id.strip()}
    if args.product_ids:
        product_ids = {p.strip() for p in args.product_ids.split(",") if p.strip()}
    if args.family_id:
        family_ids = {args.family_id.strip()}

    incremental = bool(product_ids or family_ids or args.new_only)
    full_rematch = args.full_rematch or not incremental

    if args.new_only and not product_ids:
        product_ids = set(TRACKER_CANONICAL_IDS)

    feeds: set[str] | None = None
    if args.feed and args.feed != "all":
        feeds = {args.feed.capitalize()}

    return RunOptions(
        product_ids=product_ids,
        family_ids=family_ids,
        full_rematch=full_rematch,
        new_only=args.new_only,
        dry_run=args.dry_run,
        feeds=feeds,
        as_of=date.fromisoformat(args.as_of) if args.as_of else None,
    )


def validate_product_ids(product_ids: set[str]) -> None:
    known = {m.canonical_id for m in MATCHERS}
    unknown = product_ids - known
    if unknown:
        raise SystemExit(
            f"Unknown product id(s): {', '.join(sorted(unknown))}. "
            "Add a ProductMatcher in generate_weekly_ad_prices.py first."
        )


def validate_family_ids(family_ids: set[str]) -> None:
    known = set(TRACKER_FAMILY_IDS)
    unknown = family_ids - known
    if unknown:
        raise SystemExit(
            f"Unknown family id(s): {', '.join(sorted(unknown))}. "
            "Add matchers in generate_weekly_ad_prices.py and trackerFamilies.ts."
        )


def print_run_header(options: RunOptions, split_path: Path) -> None:
    mode = "full rematch" if options.full_rematch else "incremental (cache search only)"
    print(f"Mode: {mode}")
    print(f"Extraction: none — reading cached offers from {split_path}")
    if options.product_ids:
        print(f"Products: {', '.join(sorted(options.product_ids))}")
    if options.family_ids:
        print(f"Families: {', '.join(sorted(options.family_ids))}")


def generate_feed(config: FeedConfig, options: RunOptions) -> MergeSummary:
    summary = MergeSummary()
    manifest = load_manifest(config.manifest_path)
    split_items = load_split_items(config.split_items_path, config.banner_filter)
    print_run_header(options, config.split_items_path)
    eligibility = EligibilityIndex()
    audit_collector = getattr(options, "audit_collector", None)

    weeks_key, prices_key = FEED_TS_KEYS[config.feed_label]
    product_ids = (
        set(TRACKER_CANONICAL_IDS)
        if options.full_rematch
        else (options.product_ids or set())
    )

    if not options.full_rematch and not product_ids:
        print(f"Skipping {config.feed_label} — no product ids to match")
        return summary

    if not options.full_rematch:
        validate_product_ids(product_ids)
        parsed = parse_ts_export(config.output_path, weeks_key, prices_key)
        if parsed is None:
            print(
                f"No existing {config.output_path.name} — falling back to full write "
                f"for {len(product_ids)} product(s)"
            )
            weeks, new_prices = build_prices(
                config.feed_label,
                manifest,
                split_items,
                product_ids=product_ids,
                eligibility=eligibility,
                audit_collector=audit_collector,
            )
            prices = {cid: {} for cid in TRACKER_CANONICAL_IDS}
            prices.update(new_prices)
            weeks = merge_weeks_list([], weeks)
        else:
            existing_weeks, existing_prices = parsed
            if options.new_only:
                product_ids = product_ids_missing_from_prices(
                    product_ids, existing_prices
                )
                if not product_ids:
                    print(f"No new products missing from {config.output_path.name}")
                    return summary
            weeks, new_prices = build_prices(
                config.feed_label,
                manifest,
                split_items,
                product_ids=product_ids,
                eligibility=eligibility,
                audit_collector=audit_collector,
            )
            prices = dict(existing_prices)
            for cid in TRACKER_CANONICAL_IDS:
                prices.setdefault(cid, {})
            merge_summary = merge_week_prices(prices, new_prices, product_ids)
            summary = merge_summary
            weeks = merge_weeks_list(existing_weeks, weeks)
    else:
        weeks_key, prices_key = FEED_TS_KEYS[config.feed_label]
        legacy_prices = None
        parsed = parse_ts_export(config.output_path, weeks_key, prices_key)
        if parsed:
            _, legacy_prices = parsed
        weeks, prices = build_prices(
            config.feed_label,
            manifest,
            split_items,
            eligibility=eligibility,
            audit_collector=audit_collector,
        )
        legacy_copied = merge_legacy_prices(prices, legacy_prices)
        if legacy_copied:
            print(
                f"Merged {legacy_copied} legacy weekly rows into YAML families "
                f"for {config.feed_label}"
            )
        summary.products_scanned = len(TRACKER_CANONICAL_IDS)
        summary.matched_weeks = sum(
            1
            for pid in prices
            for entry in prices[pid].values()
            if entry.get("price") is not None
        )

    if options.dry_run:
        print(
            f"[dry-run] {config.feed_label}: would write {len(weeks)} weeks, "
            f"inserted={summary.inserted} updated={summary.updated} "
            f"skipped={summary.skipped} matched_weeks={summary.matched_weeks}"
        )
        return summary

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
        f"({len(weeks)} weeks, {len(prices)} products) — "
        f"inserted={summary.inserted} updated={summary.updated} "
        f"skipped={summary.skipped} matched_weeks={summary.matched_weeks}"
    )
    return summary


def generate_family_prices(options: RunOptions) -> MergeSummary:
    summary = MergeSummary()
    safeway = FEEDS[0]
    vons = FEEDS[1]
    safeway_manifest = load_manifest(safeway.manifest_path)
    vons_manifest = load_manifest(vons.manifest_path)
    safeway_items = load_split_items(safeway.split_items_path, safeway.banner_filter)
    vons_items = load_split_items(vons.split_items_path, vons.banner_filter)

    if options.full_rematch and not options.family_ids:
        target_families: set[str] | None = None
    else:
        target_families = options.family_ids or set()
        if not target_families:
            return summary
        validate_family_ids(target_families)

    sw_weeks, sw_family, sw_members = build_family_prices(
        safeway.feed_label,
        safeway_manifest,
        safeway_items,
        family_ids=target_families,
    )
    vn_weeks, vn_family, vn_members = build_family_prices(
        vons.feed_label,
        vons_manifest,
        vons_items,
        family_ids=target_families,
    )

    if not options.full_rematch and FAMILY_OUTPUT.is_file():
        parsed = parse_family_ts(FAMILY_OUTPUT)
        if parsed:
            sw_existing = parsed["safeway"]
            vn_existing = parsed["vons"]
            sw_weeks = merge_weeks_list(sw_existing[0], sw_weeks)
            vn_weeks = merge_weeks_list(vn_existing[0], vn_weeks)
            merged_sw_family = dict(sw_existing[1])
            merged_vn_family = dict(vn_existing[1])
            merged_sw_members = dict(sw_existing[2])
            merged_vn_members = dict(vn_existing[2])
            assert target_families is not None
            summary.add(merge_week_prices(merged_sw_family, sw_family, target_families))
            summary.add(merge_week_prices(merged_vn_family, vn_family, target_families))
            sw_family = merged_sw_family
            vn_family = merged_vn_family
            for fid in target_families:
                if fid in sw_members:
                    bucket = merged_sw_members.setdefault(fid, {})
                    for member_id, weeks_map in sw_members[fid].items():
                        member_weeks = bucket.setdefault(member_id, {})
                        member_weeks.update(weeks_map)
                if fid in vn_members:
                    bucket = merged_vn_members.setdefault(fid, {})
                    for member_id, weeks_map in vn_members[fid].items():
                        member_weeks = bucket.setdefault(member_id, {})
                        member_weeks.update(weeks_map)
            sw_members = merged_sw_members
            vn_members = merged_vn_members

    if options.dry_run:
        count = len(target_families or TRACKER_FAMILY_IDS)
        print(f"[dry-run] families: would write {count} family id(s)")
        return summary

    FAMILY_OUTPUT.write_text(
        render_combined_family_ts(
            safeway.manifest_path,
            safeway.split_items_path,
            sw_weeks,
            sw_family,
            sw_members,
            vn_weeks,
            vn_family,
            vn_members,
        ),
        encoding="utf-8",
    )
    print(
        f"Wrote {FAMILY_OUTPUT.relative_to(ROOT)} "
        f"({len(target_families or TRACKER_FAMILY_IDS)} families)"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Match canonical products against cached weekly ad offers."
    )
    parser.add_argument("--product-id", help="Single canonical product id to match")
    parser.add_argument(
        "--product-ids",
        help="Comma-separated canonical product ids",
    )
    parser.add_argument(
        "--new-only",
        action="store_true",
        help="Products in MATCHERS but missing from existing generated output",
    )
    parser.add_argument("--family-id", help="Single tracker family id to match")
    parser.add_argument(
        "--full-rematch",
        action="store_true",
        help="Recompute all products (default when no incremental flags)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print summary without writing TS files",
    )
    parser.add_argument(
        "--feed",
        choices=("all", "safeway", "vons"),
        default="all",
        help="Limit to one feed (default: all)",
    )
    parser.add_argument(
        "--as-of",
        help="Override today's date for preview logging (YYYY-MM-DD)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    options = resolve_run_options(args)

    if options.new_only:
        parsed = parse_ts_export(
            FEEDS[0].output_path,
            feed_weeks_key("Safeway"),
            feed_prices_key("Safeway"),
        )
        existing = parsed[1] if parsed else None
        options.product_ids = product_ids_missing_from_prices(
            set(TRACKER_CANONICAL_IDS), existing
        )
        options.full_rematch = False
        if not options.product_ids:
            print("No new products missing from generated weekly ad prices.")
            return
        print(f"New-only products: {', '.join(sorted(options.product_ids))}")

    audit_collector = CanonicalMatchAuditCollector()
    options.audit_collector = audit_collector

    total = MergeSummary()
    feed_configs = FEEDS
    if options.feeds:
        feed_configs = tuple(c for c in FEEDS if c.feed_label in options.feeds)

    run_families = options.full_rematch or options.family_ids is not None

    for config in feed_configs:
        total.add(generate_feed(config, options))

    if run_families:
        total.add(generate_family_prices(options))

    tracked_ids = set(TRACKER_CANONICAL_IDS)
    for config in feed_configs:
        manifest = load_manifest(config.manifest_path)
        split_items = load_split_items(config.split_items_path, config.banner_filter)
        _, prices = build_prices(
            config.feed_label,
            manifest,
            split_items,
            eligibility=EligibilityIndex(),
            audit_collector=audit_collector,
        )
        validate_tracker_product_ids_unchanged(tracked_ids, prices.keys())
        summary = build_feed_preview_summary(
            config.feed_label,
            manifest,
            prices,
            tracked_ids,
            as_of=options.as_of,
            products_before=len(tracked_ids),
            products_after=len(prices),
        )
        if summary:
            print(format_preview_summary(summary))

    audit_paths = write_all_audits(audit_collector)
    for json_path, md_path in audit_paths:
        print(f"Wrote canonical match audit: {json_path.relative_to(ROOT)}")
        print(f"Wrote canonical match audit: {md_path.relative_to(ROOT)}")

    print(
        f"\nSummary: extraction=0 (cache only) | "
        f"products_scanned={total.products_scanned} | "
        f"matched_weeks={total.matched_weeks} | "
        f"inserted={total.inserted} updated={total.updated} skipped={total.skipped}"
    )


if __name__ == "__main__":
    main()
