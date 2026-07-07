#!/usr/bin/env python3
"""Validate generated weekly ad prices for sanity.

Reads src/data/weeklyAdPrices.generated.ts, vonsWeeklyAdPrices.generated.ts, and
data/canonical_tracker_families.yaml. Checks each non-null price entry for:

  1. Keyword sanity   — offerText must contain at least one token from the
                        family's include list; must NOT match keep_separate_from.
  2. Price outlier    — price > 2× median (baseline) OR > 3× prior week OR
                        < 0.5× prior week (when prior exists).
  3. Per-lb plausibility — for per-lb families, price should be $0.25–$50/lb.
  4. High confidence + bad keyword = immediate fail.

Output: data/review/weekly_price_sanity_{YYYY-MM-DD}.csv

Usage:
  python3 scripts/validate_weekly_ad_prices.py
  python3 scripts/validate_weekly_ad_prices.py --fail-on-error
  python3 scripts/validate_weekly_ad_prices.py --family-id ruffles_regular_bags
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.canonical_families import TrackerFamily, load_families  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SAFEWAY_TS = ROOT / "src" / "data" / "weeklyAdPrices.generated.ts"
VONS_TS = ROOT / "src" / "data" / "vonsWeeklyAdPrices.generated.ts"
REVIEW_DIR = ROOT / "data" / "review"

PER_LB_MIN = 0.25
PER_LB_MAX = 50.0
BASELINE_OUTLIER_FACTOR = 2.0
PRIOR_WEEK_HIGH_FACTOR = 3.0
PRIOR_WEEK_LOW_FACTOR = 0.5

OUTPUT_COLUMNS = [
    "family_id",
    "store",
    "week",
    "price",
    "offerText",
    "confidence",
    "check_failed",
    "reason",
]


# ---------------------------------------------------------------------------
# TS file parser
# ---------------------------------------------------------------------------

def parse_prices_ts(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Extract the WEEKLY_AD_PRICES dict from a generated TS file.

    The file contains a TypeScript const whose value is a JSON-compatible
    object literal.  We strip the `export const ... = ` header and the
    trailing `;` then parse as JSON.
    """
    text = path.read_text(encoding="utf-8")
    # Find the last `= {` and take from the `{` to the end
    match = re.search(r">\s*=\s*(\{)", text, re.DOTALL)
    if not match:
        # Fallback: find any `= {`
        match = re.search(r"=\s*(\{)", text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not locate price object in {path}")
    start = match.start(1)
    raw = text[start:].rstrip()
    # Strip trailing semicolon
    if raw.endswith(";"):
        raw = raw[:-1]
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Keyword sanity helpers
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "and", "or", "the", "a", "an", "of", "in", "at", "to", "for",
    "oz", "lb", "ct", "pk", "fl", "oz.", "lb.", "ct.", "pk.", "ea", "ea.",
}


def _tokens_from_phrase(phrase: str) -> list[str]:
    """Extract meaningful lower-case word tokens from a phrase."""
    words = re.split(r"[\s,/&\-']+", phrase.lower())
    return [w for w in words if w and len(w) >= 3 and w not in _STOPWORDS]


def _include_tokens(family: TrackerFamily) -> list[str]:
    """All meaningful tokens from the family include list."""
    tokens: set[str] = set()
    all_phrases = list(family.include) + [family.canonical_tracker_family]
    for phrase in all_phrases:
        tokens.update(_tokens_from_phrase(phrase))
    return sorted(tokens)


def keyword_sanity_check(
    offer_text: str | None,
    family: TrackerFamily,
) -> tuple[bool, str]:
    """Return (passed, reason).

    passed=True means the entry is fine.
    """
    if not offer_text:
        return False, "offerText is null/empty"

    text_lower = offer_text.lower()

    # Check keep_separate_from — any match is a failure
    for pattern in family.exclude_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return False, f"offerText matches keep_separate_from pattern: {pattern!r}"

    # Check at least one include token appears
    tokens = _include_tokens(family)
    if not any(tok in text_lower for tok in tokens):
        return False, (
            f"offerText {offer_text!r} contains no include token "
            f"(expected one of: {tokens[:5]}…)"
        )

    return True, ""


# ---------------------------------------------------------------------------
# Price outlier helpers
# ---------------------------------------------------------------------------

def _compute_median_baseline(prices: list[float]) -> float | None:
    nonnull = [p for p in prices if p is not None and p > 0]
    if len(nonnull) < 2:
        return None
    return median(nonnull)


def price_outlier_check(
    price: float,
    all_prices: list[float],
    prior_price: float | None,
) -> tuple[bool, str]:
    """Return (passed, reason)."""
    baseline = _compute_median_baseline(all_prices)

    if baseline is not None and price > BASELINE_OUTLIER_FACTOR * baseline:
        return False, (
            f"price ${price:.2f} > {BASELINE_OUTLIER_FACTOR}× "
            f"median baseline ${baseline:.2f}"
        )

    if prior_price is not None and prior_price > 0:
        if price > PRIOR_WEEK_HIGH_FACTOR * prior_price:
            return False, (
                f"price ${price:.2f} > {PRIOR_WEEK_HIGH_FACTOR}× "
                f"prior week ${prior_price:.2f}"
            )
        if price < PRIOR_WEEK_LOW_FACTOR * prior_price:
            return False, (
                f"price ${price:.2f} < {PRIOR_WEEK_LOW_FACTOR}× "
                f"prior week ${prior_price:.2f}"
            )

    return True, ""


def per_lb_check(price: float, family: TrackerFamily) -> tuple[bool, str]:
    """For per-lb families, flag prices outside the plausible range."""
    if "per lb" not in family.size_format_subtitle.lower():
        return True, ""
    if price < PER_LB_MIN:
        return False, f"per-lb price ${price:.2f} < minimum ${PER_LB_MIN:.2f}/lb"
    if price > PER_LB_MAX:
        return False, f"per-lb price ${price:.2f} > maximum ${PER_LB_MAX:.2f}/lb"
    return True, ""


# ---------------------------------------------------------------------------
# Main validation loop
# ---------------------------------------------------------------------------

def _sorted_weeks(week_data: dict[str, dict]) -> list[str]:
    """Return weeks in chronological order."""
    return sorted(week_data.keys())


def validate_feed(
    prices: dict[str, dict[str, dict[str, Any]]],
    families_by_id: dict[str, TrackerFamily],
    store_label: str,
    filter_family_id: str | None = None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for family_id, week_data in prices.items():
        if filter_family_id and family_id != filter_family_id:
            continue
        family = families_by_id.get(family_id)
        if family is None:
            continue  # unknown family — skip

        sorted_wks = _sorted_weeks(week_data)
        all_prices: list[float] = [
            week_data[w]["price"]
            for w in sorted_wks
            if week_data[w].get("price") is not None
        ]

        prior_price: float | None = None

        for week in sorted_wks:
            entry = week_data[week]
            price = entry.get("price")
            offer_text = entry.get("offerText")
            confidence = entry.get("confidence")

            if price is None:
                prior_price = None
                continue

            failures: list[str] = []

            # 1. Keyword sanity
            kw_ok, kw_reason = keyword_sanity_check(offer_text, family)
            if not kw_ok:
                # High confidence + bad keyword = definite failure
                sev = "FAIL" if confidence == "high" else "WARN"
                failures.append(f"[keyword/{sev}] {kw_reason}")

            # 2. Price outlier
            out_ok, out_reason = price_outlier_check(price, all_prices, prior_price)
            if not out_ok:
                failures.append(f"[outlier] {out_reason}")

            # 3. Per-lb plausibility
            lb_ok, lb_reason = per_lb_check(price, family)
            if not lb_ok:
                failures.append(f"[per_lb] {lb_reason}")

            if failures:
                rows.append(
                    {
                        "family_id": family_id,
                        "store": store_label,
                        "week": week,
                        "price": str(price),
                        "offerText": offer_text or "",
                        "confidence": confidence or "",
                        "check_failed": "true",
                        "reason": "; ".join(failures),
                    }
                )

            prior_price = price

    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate generated weekly ad prices"
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 if any check fails",
    )
    parser.add_argument(
        "--family-id",
        default=None,
        help="Validate only this family id",
    )
    parser.add_argument(
        "--out-date",
        default=None,
        help="Override output date string (default: today YYYY-MM-DD)",
    )
    args = parser.parse_args(argv)

    out_date = args.out_date or date.today().isoformat()

    families = load_families()
    families_by_id = {f.id: f for f in families}

    all_rows: list[dict[str, str]] = []

    for ts_path, store_label in [
        (SAFEWAY_TS, "safeway"),
        (VONS_TS, "vons"),
    ]:
        if not ts_path.is_file():
            print(f"Warning: {ts_path} not found — skipping {store_label}")
            continue
        prices = parse_prices_ts(ts_path)
        rows = validate_feed(
            prices, families_by_id, store_label, args.family_id
        )
        all_rows.extend(rows)

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REVIEW_DIR / f"weekly_price_sanity_{out_date}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    total = len(all_rows)
    fails = sum(1 for r in all_rows if r["check_failed"] == "true")
    print(f"Validation complete: {fails} flagged rows across {total} total checks")
    print(f"Output: {out_path}")

    if all_rows:
        print("\nFlagged rows:")
        for r in all_rows[:20]:
            print(
                f"  [{r['store']}] {r['family_id']} {r['week']} "
                f"${r['price']} — {r['reason']}"
            )
        if len(all_rows) > 20:
            print(f"  ... and {len(all_rows) - 20} more (see CSV)")

    if args.fail_on_error and fails > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
