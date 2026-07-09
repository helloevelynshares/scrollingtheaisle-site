#!/usr/bin/env python3
"""Detect possible *missed* weekly-ad deals for tracked families.

Failure mode this guards against
--------------------------------
The weekly-ad pipeline can silently drop a deal for a tracked family in a given
week even though the ad clearly advertised it. Two documented causes:

  1. A tile is extracted into ``raw_offer_cards.csv`` but never promoted into
     ``split_offer_items.csv`` (Kettle Brand 7/1, Coca-Cola B2G3F 7/1).
  2. A tile is present but the family's include pattern does not match the ad
     wording (e.g. "Nabisco **Family Size** Snack Crackers" vs the
     "Nabisco snack crackers" include) — now largely fixed by the robust
     qualifier-tolerant matcher, but new wordings can still slip through.

In both cases the generated TS keeps a ``null`` price and the chart falls back
to baseline. This detector cross-checks the extraction data against the
generated prices and flags family/weeks where the ad text *does* mention the
family (with a price) but no price was written.

What it CANNOT catch
--------------------
If a tile was dropped *before* text extraction (no row anywhere in raw or
split — e.g. the Oreo 7/8 half of a combined coupon tile, whose word "oreo"
never appeared in any CSV), there is no textual signal to key off. That class
needs vision-pipeline coverage / a manual PDF audit and is out of scope here.

Output
------
``data/review/missed_deal_candidates_{YYYY-MM-DD}.csv`` and a ``.md`` summary.

Usage
-----
  python3 scripts/detect_missed_deals.py
  python3 scripts/detect_missed_deals.py --feed safeway --week 2026-07-08
  python3 scripts/detect_missed_deals.py --family-id oreo_family_size
  python3 scripts/detect_missed_deals.py --fail-on-high   # CI gate
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.canonical_families import TrackerFamily, load_families  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = Path.home() / "Documents" / "scrolling-the-aisle"
DATA_ROOT = Path(os.environ.get("SCROLLING_THE_AISLE_ROOT", DEFAULT_DATA_ROOT))
OUTPUTS_ROOT = DATA_ROOT / "outputs"
REVIEW_DIR = ROOT / "data" / "review"
AUDIT_DIR = ROOT / "output" / "weekly_deals"

# CSV field size can be large for long combined-offer rows.
csv.field_size_limit(10_000_000)


@dataclass(frozen=True)
class Feed:
    label: str  # lowercase key used in the report ("safeway" / "vons")
    banner: str  # value found in the CSV `banner` column ("Safeway" / "Vons")
    dir_prefix: str  # product_discovery_{prefix}* dirs to scan for raw cards
    consolidated_dir: str  # canonical split_offer_items.csv location
    ts_path: Path
    ts_prices_key: str


FEEDS: tuple[Feed, ...] = (
    Feed(
        label="safeway",
        banner="Safeway",
        dir_prefix="product_discovery_safeway",
        consolidated_dir="product_discovery_safeway",
        ts_path=ROOT / "src" / "data" / "weeklyAdPrices.generated.ts",
        ts_prices_key="WEEKLY_AD_PRICES",
    ),
    Feed(
        label="vons",
        banner="Vons",
        dir_prefix="product_discovery_vons",
        consolidated_dir="product_discovery_vons",
        ts_path=ROOT / "src" / "data" / "vonsWeeklyAdPrices.generated.ts",
        ts_prices_key="VONS_WEEKLY_AD_PRICES",
    ),
)

OUTPUT_COLUMNS = [
    "feed",
    "week",
    "family_id",
    "severity",
    "candidate_price",
    "in_raw_cards",
    "in_split_items",
    "audit_disposition",
    "example_text",
    "reason",
]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_prices_ts(path: Path, prices_key: str) -> dict[str, dict[str, dict]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"export const {prices_key}[^=]*=\s*(\{{.*?\}});", text, re.S)
    if not match:
        raise ValueError(f"Could not locate {prices_key} in {path}")
    return json.loads(match.group(1))


def parse_price(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = str(value).replace("$", "").strip()
    if cleaned in {"", "-"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_raw_cards(feed: Feed) -> dict[str, list[dict[str, str]]]:
    """All raw_offer_cards rows for a feed, keyed by week_start (deduped)."""
    by_week: dict[str, list[dict[str, str]]] = {}
    seen: set[tuple] = set()
    if not OUTPUTS_ROOT.is_dir():
        return by_week
    for card_path in sorted(OUTPUTS_ROOT.glob(f"{feed.dir_prefix}*/raw_offer_cards.csv")):
        for row in _read_csv_rows(card_path):
            if (row.get("banner") or "").strip() != feed.banner:
                continue
            week = (row.get("week_start") or "").strip()
            if not week:
                continue
            key = (
                week,
                row.get("page_number", ""),
                row.get("offer_index_on_page", ""),
                (row.get("raw_offer_text") or "")[:120],
            )
            if key in seen:
                continue
            seen.add(key)
            by_week.setdefault(week, []).append(row)
    return by_week


def load_split_items(feed: Feed) -> dict[str, list[dict[str, str]]]:
    by_week: dict[str, list[dict[str, str]]] = {}
    path = OUTPUTS_ROOT / feed.consolidated_dir / "split_offer_items.csv"
    if not path.is_file():
        return by_week
    for row in _read_csv_rows(path):
        if (row.get("banner") or "").strip() != feed.banner:
            continue
        week = (row.get("week_start") or "").strip()
        if week:
            by_week.setdefault(week, []).append(row)
    return by_week


def load_audit_dispositions() -> dict[tuple[str, str, str], set[str]]:
    """(feed_label, family_id, week) -> set of match_decisions from audits."""
    out: dict[tuple[str, str, str], set[str]] = {}
    if not AUDIT_DIR.is_dir():
        return out
    for audit_path in AUDIT_DIR.glob("*/canonical_match_audit.json"):
        try:
            doc = json.loads(audit_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        for bucket in ("accepted", "rejected", "manual_review"):
            for rec in doc.get(bucket) or []:
                key = (
                    (rec.get("feed") or "").strip().lower(),
                    rec.get("family_id") or "",
                    rec.get("week_start") or "",
                )
                out.setdefault(key, set()).add(rec.get("match_decision") or bucket)
    return out


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _match_text(row: dict[str, str]) -> str:
    """The specific product-name field to match against.

    We deliberately match only the split/product-name field, NOT the full
    ``raw_offer_text`` (which, for multi-product blocks, lists many unrelated
    brands and would produce spurious keyword hits — e.g. a Cheez-It mention
    buried in a long "or" list on an unrelated tile).
    """
    for key in ("split_product_text", "verified_raw_product_text", "raw_product_text"):
        value = (row.get(key) or "").strip()
        if value:
            return value.lower()
    return ""


def _row_price(row: dict[str, str]) -> float | None:
    return parse_price(row.get("verified_advertised_price")) or parse_price(
        row.get("advertised_price")
    )


def family_matches(text: str, family: TrackerFamily) -> bool:
    if not any(re.search(p, text) for p in family.patterns):
        return False
    return not any(re.search(p, text) for p in family.exclude_patterns)


def _looks_multi_product(text: str) -> bool:
    """Heuristic: does this product text list several distinct products?

    Multi-brand "or" blocks ("Doritos, Ruffles, Smartfood, SunChips …") carry a
    single "up to" price that rarely maps to one tracked family, so they are
    lower-confidence candidates than a focused single-product tile.
    """
    return text.count(",") >= 2 or "\n" in text or len(re.findall(r"\boz\b", text)) >= 2


@dataclass
class Candidate:
    feed: str
    week: str
    family_id: str
    prices: list[float] = field(default_factory=list)
    in_raw: bool = False
    in_split: bool = False
    example_text: str = ""
    audit: set[str] = field(default_factory=set)
    multi_product: bool = True

    @property
    def candidate_price(self) -> float | None:
        return min(self.prices) if self.prices else None

    @property
    def severity(self) -> str:
        # Deliberately blocked by the eligibility gate → informational only.
        if self.audit & {"rejected", "manual_review"}:
            return "info"
        # Present in raw extraction but never promoted to split.
        if self.in_raw and not self.in_split:
            # Focused single-product tile → highest signal; multi-brand block → medium.
            return "medium" if self.multi_product else "high"
        # Matched a split row but no price written and not audit-rejected.
        if self.in_split:
            return "medium"
        return "high" if not self.multi_product else "medium"

    @property
    def reason(self) -> str:
        block = " (multi-product block — lower confidence)" if self.multi_product else ""
        if self.audit & {"rejected", "manual_review"}:
            return (
                "ad text mentions family with a price but it was intentionally "
                f"blocked by the eligibility gate ({', '.join(sorted(self.audit))})"
            )
        if self.in_raw and not self.in_split:
            return (
                "family + price present in raw_offer_cards but NOT in "
                "split_offer_items — likely dropped during tile promotion; "
                f"add a split row (manually_added_missed_tile) and regenerate{block}"
            )
        if self.in_split:
            return (
                "family + price present in split_offer_items but no price written "
                f"to the generated TS — re-run generate_weekly_ad_prices for this family{block}"
            )
        return f"family + price present in extraction but no tracker price for this week{block}"


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def detect_for_feed(
    feed: Feed,
    families: list[TrackerFamily],
    audit: dict[tuple[str, str, str], set[str]],
    *,
    week_filter: str | None,
    family_filter: str | None,
) -> list[Candidate]:
    if not feed.ts_path.is_file():
        print(f"Warning: {feed.ts_path} missing — skipping {feed.label}")
        return []
    prices = parse_prices_ts(feed.ts_path, feed.ts_prices_key)
    tracked_weeks = {wk for weeks in prices.values() for wk in weeks}

    raw_by_week = load_raw_cards(feed)
    split_by_week = load_split_items(feed)

    candidates: dict[tuple[str, str], Candidate] = {}

    def consider(source_rows: dict[str, list[dict[str, str]]], is_raw: bool) -> None:
        for week, rows in source_rows.items():
            if week not in tracked_weeks:
                continue
            if week_filter and week != week_filter:
                continue
            for family in families:
                if family_filter and family.id != family_filter:
                    continue
                current = prices.get(family.id, {}).get(week, {})
                if current.get("price") is not None:
                    continue  # already covered
                for row in rows:
                    price = _row_price(row)
                    if price is None:
                        continue
                    text = _match_text(row)
                    if not text or not family_matches(text, family):
                        continue
                    key = (week, family.id)
                    cand = candidates.get(key)
                    if cand is None:
                        cand = Candidate(feed=feed.label, week=week, family_id=family.id)
                        cand.audit = audit.get((feed.label, family.id, week), set())
                        candidates[key] = cand
                    cand.prices.append(price)
                    if is_raw:
                        cand.in_raw = True
                    else:
                        cand.in_split = True
                    if not _looks_multi_product(text):
                        cand.multi_product = False
                    if text and (not cand.example_text or len(text) < len(cand.example_text)):
                        cand.example_text = text[:160]

    consider(raw_by_week, is_raw=True)
    consider(split_by_week, is_raw=False)
    return list(candidates.values())


_SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect possible missed weekly-ad deals")
    parser.add_argument("--feed", choices=[f.label for f in FEEDS], default=None)
    parser.add_argument("--week", default=None, help="Only this week_start (YYYY-MM-DD)")
    parser.add_argument("--family-id", default=None)
    parser.add_argument("--out-date", default=None)
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit 1 if any high-severity candidate is found",
    )
    args = parser.parse_args(argv)

    out_date = args.out_date or date.today().isoformat()
    families = load_families()
    audit = load_audit_dispositions()

    all_candidates: list[Candidate] = []
    for feed in FEEDS:
        if args.feed and feed.label != args.feed:
            continue
        all_candidates.extend(
            detect_for_feed(
                feed,
                families,
                audit,
                week_filter=args.week,
                family_filter=args.family_id,
            )
        )

    all_candidates.sort(
        key=lambda c: (_SEVERITY_ORDER.get(c.severity, 9), c.feed, c.week, c.family_id)
    )

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = REVIEW_DIR / f"missed_deal_candidates_{out_date}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for cand in all_candidates:
            writer.writerow(
                {
                    "feed": cand.feed,
                    "week": cand.week,
                    "family_id": cand.family_id,
                    "severity": cand.severity,
                    "candidate_price": (
                        f"{cand.candidate_price:.2f}" if cand.candidate_price is not None else ""
                    ),
                    "in_raw_cards": "true" if cand.in_raw else "false",
                    "in_split_items": "true" if cand.in_split else "false",
                    "audit_disposition": ",".join(sorted(cand.audit)) or "absent",
                    "example_text": cand.example_text,
                    "reason": cand.reason,
                }
            )

    md_path = REVIEW_DIR / f"missed_deal_candidates_{out_date}.md"
    highs = [c for c in all_candidates if c.severity == "high"]
    mediums = [c for c in all_candidates if c.severity == "medium"]
    infos = [c for c in all_candidates if c.severity == "info"]
    with md_path.open("w", encoding="utf-8") as handle:
        handle.write(f"# Missed weekly-ad deal candidates — {out_date}\n\n")
        handle.write(
            f"- **High** (in raw, not promoted to split): {len(highs)}\n"
            f"- **Medium** (in split, no TS price, not audit-rejected): {len(mediums)}\n"
            f"- **Info** (intentionally blocked by eligibility gate): {len(infos)}\n\n"
        )
        for title, group in (("High severity", highs), ("Medium severity", mediums)):
            if not group:
                continue
            handle.write(f"## {title}\n\n")
            for c in group:
                price = f"${c.candidate_price:.2f}" if c.candidate_price is not None else "?"
                handle.write(
                    f"- `{c.family_id}` ({c.feed}, {c.week}): {price} — "
                    f"{c.example_text!r}\n  - {c.reason}\n"
                )
            handle.write("\n")

    print(
        f"Missed-deal scan complete: {len(highs)} high, {len(mediums)} medium, "
        f"{len(infos)} info candidate(s)"
    )
    print(f"Output: {csv_path}")
    for c in (highs + mediums)[:25]:
        price = f"${c.candidate_price:.2f}" if c.candidate_price is not None else "?"
        print(
            f"  [{c.severity}] {c.feed} {c.week} {c.family_id} {price} — {c.example_text!r}"
        )

    if args.fail_on_high and highs:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
