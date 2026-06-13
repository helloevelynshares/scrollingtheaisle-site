#!/usr/bin/env python3
"""
Audit optional TikTok / Safeway workflow inputs (food-only lens).

Usage:
  python scripts/audit_tiktok_food_inputs.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from tiktok_food_config import is_non_food_query

MANUAL_CANONICAL = REPO_ROOT / "data/canonical/manual_canonical_50.csv"
SEARCH_SEED = REPO_ROOT / "scripts/output/safeway_search_seed.jsonl"
BULK_TRANSCRIPTS = (
    REPO_ROOT / "bulk_transcripts.csv",
    REPO_ROOT / "data/raw/bulk_transcripts.csv",
)
MENTIONS_OUT = REPO_ROOT / "data/processed/tiktok_item_mentions.csv"
LEDGER = REPO_ROOT / "data/canonical/safeway_tracked_items_v1.csv"


def audit_manual_canonical() -> None:
    print("## manual_canonical_50.csv")
    if not MANUAL_CANONICAL.is_file():
        print("  (not found)\n")
        return
    food: list[str] = []
    excluded: list[str] = []
    with MANUAL_CANONICAL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        col = "query" if reader.fieldnames and "query" in reader.fieldnames else reader.fieldnames[0]
        for row in reader:
            q = (row.get(col) or "").strip()
            if not q:
                continue
            if is_non_food_query(q):
                excluded.append(q)
            else:
                food.append(q)
    print(f"  food queries kept: {len(food)}")
    print(f"  non-food excluded: {len(excluded)}")
    if excluded:
        print("  excluded:", ", ".join(excluded))
    print()


def audit_search_seed() -> None:
    print("## safeway_search_seed.jsonl")
    if not SEARCH_SEED.is_file():
        print("  (not found)\n")
        return
    ok_food = ok_nonfood = fail = 0
    with SEARCH_SEED.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            q = (row.get("query") or "").strip()
            nonfood = is_non_food_query(q)
            if row.get("ok"):
                if nonfood:
                    ok_nonfood += 1
                else:
                    ok_food += 1
            else:
                fail += 1
    print(f"  successful food searches: {ok_food}")
    print(f"  successful non-food (legacy): {ok_nonfood}")
    print(f"  failures: {fail}")
    print("  → TikTok ledger replaces staples; non-food rows are deprecated.\n")


def audit_bulk_transcripts() -> None:
    print("## bulk_transcripts.csv")
    found = next((p for p in BULK_TRANSCRIPTS if p.is_file()), None)
    if not found:
        print("  (not found — add at repo root or data/raw/)")
        print("  Run: python scripts/extract_tiktok_food_mentions.py\n")
        return
    with found.open(newline="", encoding="utf-8") as handle:
        rows = sum(1 for _ in csv.DictReader(handle))
    print(f"  path: {found.relative_to(REPO_ROOT)}")
    print(f"  video rows: {rows}")
    print("  Run: python scripts/extract_tiktok_food_mentions.py\n")


def audit_mentions_and_ledger() -> None:
    print("## tiktok_item_mentions.csv")
    if MENTIONS_OUT.is_file():
        with MENTIONS_OUT.open(newline="", encoding="utf-8") as handle:
            rows = sum(1 for _ in csv.DictReader(handle))
        print(f"  mention rows: {rows}")
    else:
        print("  (not found)")
    print()

    print("## safeway_tracked_items_v1.csv")
    if LEDGER.is_file():
        with LEDGER.open(newline="", encoding="utf-8") as handle:
            items = list(csv.DictReader(handle))
        needs = sum(1 for r in items if r.get("status") == "needs_selection")
        print(f"  ledger items: {len(items)} ({needs} needs_selection)")
        print("  Fetch candidates:")
        print("    python scripts/seed_safeway_tracked_playwright.py --headful")
    else:
        print("  (not found)")
    print()


def main() -> int:
    print("TikTok food-only Safeway workflow audit\n")
    audit_manual_canonical()
    audit_search_seed()
    audit_bulk_transcripts()
    audit_mentions_and_ledger()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
