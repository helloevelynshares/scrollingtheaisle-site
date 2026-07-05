#!/usr/bin/env python3
"""Orchestrate incremental add of a canonical price-tracker product.

Approves a user-suggested item into the offline pipeline without re-extracting
historical weekly ads (uses cached split_offer_items.csv) or re-crawling all baselines.

Prerequisites (manual, one-time per product):
  1. Add row to src/data/canonicalProducts.ts (id, displayName, searchAliases, sortOrder)
  2. Add ProductMatcher in scripts/generate_weekly_ad_prices.py (+ TRACKER_CANONICAL_IDS)
  3. Append row to data/canonical/price_tracker_baseline_queries.csv
  4. Append row to data/canonical/price_tracker_baseline_queries_new_only.csv (same row)
  5. If Costco-comparable: add CanonicalPackageMeta in scripts/price_comparison/canonical_metadata.py

Then run this script (or the individual commands in docs/PRICE_TRACKER_ADD_RUNBOOK.md).

Usage:
  python3 scripts/add_tracker_product.py --product-id grapes --dry-run
  python3 scripts/add_tracker_product.py --product-id grapes --run-baseline --run-backfill
  python3 scripts/add_tracker_product.py --product-id grapes --all
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.artifacts import load_baseline_queries  # noqa: E402

NEW_ONLY_QUERIES = ROOT / "data" / "canonical" / "price_tracker_baseline_queries_new_only.csv"
CANONICAL_TS = ROOT / "src" / "data" / "canonicalProducts.ts"
GENERATE_WEEKLY = SCRIPT_DIR / "generate_weekly_ad_prices.py"
SEED_SAFEWAY = SCRIPT_DIR / "seed_safeway_baseline.py"
SEED_VONS = SCRIPT_DIR / "seed_vons_baseline_playwright.py"
GEN_SAFEWAY_MATCHES = SCRIPT_DIR / "generate_safeway_feed_matches.py"
GEN_VONS_MATCHES = SCRIPT_DIR / "generate_vons_feed_matches.py"
BACKFILL_COSTCO = SCRIPT_DIR / "backfill_price_comparisons.py"
VERIFY_BUILD = ROOT / "scripts" / "verify-price-tracker-build.mjs"


def run(cmd: list[str], *, dry_run: bool, label: str) -> int:
    print(f"\n--- {label} ---")
    print("$", " ".join(cmd))
    if dry_run:
        print("[dry-run] skipped")
        return 0
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def canonical_in_ts(product_id: str) -> bool:
    if not CANONICAL_TS.is_file():
        return False
    text = CANONICAL_TS.read_text(encoding="utf-8")
    return f'id: "{product_id}"' in text or f"id: '{product_id}'" in text


def matcher_in_generate(product_id: str) -> bool:
    gen = SCRIPT_DIR / "generate_weekly_ad_prices.py"
    text = gen.read_text(encoding="utf-8")
    return f'"{product_id}"' in text and "ProductMatcher(" in text


def query_in_new_only(product_id: str) -> bool:
    if not NEW_ONLY_QUERIES.is_file():
        return False
    return any(r["canonical_id"] == product_id for r in load_baseline_queries(NEW_ONLY_QUERIES))


def validate_metadata(product_id: str) -> list[str]:
    missing: list[str] = []
    if not canonical_in_ts(product_id):
        missing.append(f"src/data/canonicalProducts.ts — add id: {product_id!r}")
    if not matcher_in_generate(product_id):
        missing.append(
            f"scripts/generate_weekly_ad_prices.py — add ProductMatcher + TRACKER_CANONICAL_IDS"
        )
    if not query_in_new_only(product_id):
        missing.append(
            f"data/canonical/price_tracker_baseline_queries_new_only.csv — add search row"
        )
    return missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Incremental price tracker product add.")
    parser.add_argument("--product-id", required=True, help="Canonical product id")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate metadata and print commands without running crawls",
    )
    parser.add_argument(
        "--run-baseline",
        action="store_true",
        help="Crawl Safeway + Vons baselines for this product only (requires cookies)",
    )
    parser.add_argument(
        "--run-backfill",
        action="store_true",
        help="Match historical weekly ads from cache for this product",
    )
    parser.add_argument(
        "--run-costco",
        action="store_true",
        help="Update Costco comparison TS for this product",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run verify-price-tracker-build.mjs after backfill",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="run-baseline + run-backfill + run-costco + validate",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    product_id = args.product_id.strip()

    if args.all:
        args.run_baseline = True
        args.run_backfill = True
        args.run_costco = True
        args.validate = True

    missing = validate_metadata(product_id)
    if missing:
        print(f"Missing metadata for {product_id!r}:")
        for line in missing:
            print(f"  - {line}")
        print("\nComplete the checklist above, then re-run this script.")
        return 1

    print(f"Metadata OK for {product_id!r}")
    print("Historical weekly ads: cached split_offer_items.csv (no PDF re-extraction)")

    rc = 0
    py = sys.executable

    if args.run_baseline:
        rc |= run(
            [
                py,
                str(SEED_SAFEWAY),
                "--browser-like",
                "--product-id",
                product_id,
                "--input",
                str(NEW_ONLY_QUERIES.relative_to(ROOT)),
                "--csv",
                "data/processed/safeway_baseline_candidates_new_only.csv",
                "--merge-csv",
                "data/processed/safeway_baseline_candidates_v1.csv",
            ],
            dry_run=args.dry_run,
            label="Safeway baseline (new product only)",
        )
        rc |= run(
            [py, str(GEN_SAFEWAY_MATCHES), "--merge-fallback"],
            dry_run=args.dry_run,
            label="Merge Safeway baseline into priceTrackerFallback.ts",
        )
        rc |= run(
            [
                py,
                str(SEED_VONS),
                "--http-only",
                "--product-id",
                product_id,
                "--input",
                str(NEW_ONLY_QUERIES.relative_to(ROOT)),
                "--csv",
                "data/processed/vons_baseline_candidates_new_only.csv",
                "--merge-csv",
                "data/processed/vons_baseline_candidates_v1.csv",
            ],
            dry_run=args.dry_run,
            label="Vons baseline (new product only)",
        )
        rc |= run(
            [py, str(GEN_VONS_MATCHES)],
            dry_run=args.dry_run,
            label="Regenerate vonsBaseline.generated.ts (merges new_only CSV)",
        )

    if args.run_backfill or not any(
        [args.run_baseline, args.run_backfill, args.run_costco, args.validate]
    ):
        rc |= run(
            [
                py,
                str(GENERATE_WEEKLY),
                "--product-id",
                product_id,
            ],
            dry_run=args.dry_run,
            label="Historical weekly ad backfill (cache search only)",
        )

    if args.run_costco:
        rc |= run(
            [py, str(BACKFILL_COSTCO), "--product-id", product_id],
            dry_run=args.dry_run,
            label="Costco comparison (scoped to product)",
        )

    if args.validate:
        rc |= run(
            ["node", str(VERIFY_BUILD)],
            dry_run=args.dry_run,
            label="Verify price tracker build bundle",
        )

    if not any(
        [args.run_baseline, args.run_backfill, args.run_costco, args.validate]
    ):
        print(
            "\nTip: pass --run-baseline --run-backfill --run-costco --validate "
            "or --all to execute the full incremental pipeline."
        )

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
