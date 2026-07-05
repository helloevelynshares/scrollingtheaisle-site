"""Parse and merge generated TypeScript price-tracker artifacts."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MergeSummary:
    """Counts for incremental upsert operations."""

    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    matched_weeks: int = 0
    products_scanned: int = 0

    def add(self, other: MergeSummary) -> None:
        self.inserted += other.inserted
        self.updated += other.updated
        self.skipped += other.skipped
        self.matched_weeks += other.matched_weeks
        self.products_scanned += other.products_scanned


def parse_ts_export(path: Path, weeks_key: str, prices_key: str) -> tuple[list[dict], dict] | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    weeks_match = re.search(rf"export const {weeks_key}.*?=\s*(\[.*?\]);", text, re.S)
    prices_match = re.search(rf"export const {prices_key}.*?=\s*(\{{.*?\}});", text, re.S)
    if not weeks_match or not prices_match:
        return None
    return json.loads(weeks_match.group(1)), json.loads(prices_match.group(1))


def parse_family_ts(path: Path) -> dict[str, tuple[list[dict], dict, dict]] | None:
    """Return per-feed (weeks, family_prices, member_prices) from familyWeeklyAdPrices.generated.ts."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    keys = [
        ("FAMILY_WEEKLY_AD_WEEKS", "FAMILY_WEEKLY_AD_PRICES", "FAMILY_MEMBER_WEEKLY_AD_PRICES"),
        ("VONS_FAMILY_WEEKLY_AD_WEEKS", "VONS_FAMILY_WEEKLY_AD_PRICES", "VONS_FAMILY_MEMBER_WEEKLY_AD_PRICES"),
    ]
    out: dict[str, tuple[list[dict], dict, dict]] = {}
    for weeks_key, prices_key, members_key in keys:
        weeks_m = re.search(rf"export const {weeks_key}.*?=\s*(\[.*?\]);", text, re.S)
        prices_m = re.search(rf"export const {prices_key}.*?=\s*(\{{.*?\}});", text, re.S)
        members_m = re.search(rf"export const {members_key}.*?=\s*(\{{.*?\}});", text, re.S)
        if not weeks_m or not prices_m or not members_m:
            return None
        feed = "safeway" if weeks_key.startswith("FAMILY_") else "vons"
        out[feed] = (
            json.loads(weeks_m.group(1)),
            json.loads(prices_m.group(1)),
            json.loads(members_m.group(1)),
        )
    return out


def merge_week_prices(
    existing: dict[str, dict[str, dict]],
    updates: dict[str, dict[str, dict]],
    product_ids: set[str],
) -> MergeSummary:
    """Upsert week-level price entries for selected product ids."""
    summary = MergeSummary(products_scanned=len(product_ids))
    for product_id in product_ids:
        existing_weeks = existing.setdefault(product_id, {})
        update_weeks = updates.get(product_id, {})
        for week_start, entry in update_weeks.items():
            prior = existing_weeks.get(week_start)
            if prior == entry:
                summary.skipped += 1
                continue
            if prior is None:
                summary.inserted += 1
            else:
                summary.updated += 1
            if entry.get("price") is not None:
                summary.matched_weeks += 1
            existing_weeks[week_start] = entry
    return summary


def merge_weeks_list(existing: list[dict], manifest_weeks: list[dict]) -> list[dict]:
    """Keep full week metadata from manifest; preserve any extra weeks already in output."""
    by_start = {w["weekStart"]: w for w in existing}
    for week in manifest_weeks:
        by_start[week["weekStart"]] = week
    return sorted(by_start.values(), key=lambda w: w["weekStart"])


def load_baseline_queries(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            canonical_id = (row.get("canonical_id") or "").strip()
            search_query = (row.get("search_query") or "").strip()
            display_name = (row.get("display_name") or canonical_id).strip()
            if canonical_id and search_query:
                rows.append(
                    {
                        "canonical_id": canonical_id,
                        "display_name": display_name,
                        "search_query": search_query,
                    }
                )
    return rows


def merge_candidate_csv(
    existing_path: Path,
    new_rows: list[dict[str, str]],
    *,
    fieldnames: list[str],
) -> tuple[int, int]:
    """Upsert candidate rows by canonical_id (replace all ranks for that id)."""
    existing: dict[str, list[dict[str, str]]] = {}
    if existing_path.is_file():
        with existing_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                existing.setdefault(row["canonical_id"], []).append(row)

    touched = {row["canonical_id"] for row in new_rows}
    for cid in touched:
        existing[cid] = [r for r in new_rows if r["canonical_id"] == cid]

    merged: list[dict[str, str]] = []
    for rows in existing.values():
        merged.extend(rows)
    merged.sort(key=lambda r: (r["canonical_id"], int(r.get("candidate_rank") or 99)))

    existing_path.parent.mkdir(parents=True, exist_ok=True)
    with existing_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)

    inserted = len(touched)
    updated = 0
    return inserted, updated


def product_ids_missing_from_prices(
    all_product_ids: set[str],
    prices: dict | None,
) -> set[str]:
    if not prices:
        return set(all_product_ids)
    missing: set[str] = set()
    for product_id in all_product_ids:
        if product_id not in prices:
            missing.add(product_id)
    return missing
