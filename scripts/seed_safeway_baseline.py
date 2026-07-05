#!/usr/bin/env python3
"""
Fetch Safeway baseline prices via HTTP (pgmsearch / safeway_client).

Examples:
  python scripts/seed_safeway_baseline.py --query goldfish --browser-like
  python scripts/seed_safeway_baseline.py --browser-like \\
    --input data/canonical/price_tracker_baseline_queries_new_only.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import requests
from dotenv import load_dotenv

from safeway_candidates import (
    CANDIDATE_CSV_FIELDS,
    doc_to_candidate_row,
    extract_product_docs,
)
from safeway_client import search_product
from safeway_config import load_config, load_timeout_seconds
from price_tracker.artifacts import merge_candidate_csv

DEFAULT_QUERIES = REPO_ROOT / "data/canonical/price_tracker_baseline_queries.csv"
DEFAULT_JSONL = SCRIPT_DIR / "output/safeway_baseline_candidates.jsonl"
DEFAULT_CSV = REPO_ROOT / "data/processed/safeway_baseline_candidates_v1.csv"
FEED_ID = "safeway_bay_area"

logger = logging.getLogger("seed_safeway_baseline")


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


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


def flatten_candidates(
    record: dict,
    item: dict[str, str],
    *,
    top_n: int,
) -> list[dict[str, str]]:
    docs = extract_product_docs(record.get("response"))
    rows: list[dict[str, str]] = []
    for rank, doc in enumerate(docs[:top_n], start=1):
        rows.append(
            doc_to_candidate_row(
                doc,
                rank=rank,
                canonical_id=item["canonical_id"],
                display_name=item["display_name"],
                search_query=item["search_query"],
                content_theme="price_tracker_baseline",
            )
        )
    return rows


def run_http(
    items: list[dict[str, str]],
    *,
    output: Path,
    csv_path: Path,
    top_n: int,
    delay: float,
    timeout_sec: float,
    browser_like: bool,
) -> tuple[int, int]:
    config = load_config()
    missing = config.missing_fields()
    if missing:
        raise ValueError("Missing Safeway credentials: " + ", ".join(missing))

    session = requests.Session()
    all_csv_rows: list[dict[str, str]] = []
    successes = 0
    failures = 0

    with output.open("w", encoding="utf-8") as out_file:
        for index, item in enumerate(items):
            if index > 0:
                time.sleep(delay)
            query = item["search_query"]
            logger.info(
                "HTTP search Safeway for %r (%s) store=%s zip=%s",
                query,
                item["canonical_id"],
                config.store_id,
                config.zipcode,
            )
            outcome = search_product(
                session,
                query,
                config,
                timeout_sec=timeout_sec,
                browser_like=browser_like,
            )
            record = {
                "query": outcome.query,
                "ok": outcome.ok,
                "status_code": outcome.status_code,
                "error": outcome.error,
                "response": outcome.payload,
                "capture_source": "http",
            }
            if outcome.message:
                record["message"] = outcome.message
            record["canonical_id"] = item["canonical_id"]
            record["display_name"] = item["display_name"]
            record["feed_id"] = FEED_ID
            out_file.write(json.dumps(record, ensure_ascii=False) + "\n")

            if outcome.ok:
                successes += 1
                all_csv_rows.extend(flatten_candidates(record, item, top_n=top_n))
            else:
                failures += 1
                if outcome.message:
                    logger.error("%s", outcome.message)

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_csv_rows)

    return successes, failures, all_csv_rows


def main() -> int:
    load_dotenv(SCRIPT_DIR / ".env")

    parser = argparse.ArgumentParser(description="Seed Safeway baseline prices via HTTP.")
    parser.add_argument("--query", help="Single search term (e.g. goldfish)")
    parser.add_argument(
        "--product-id",
        help="Run only this canonical_id from --input CSV",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_QUERIES,
        help="CSV with canonical_id, search_query",
    )
    parser.add_argument("--browser-like", action="store_true")
    parser.add_argument("--delay", type=float, default=2.5)
    parser.add_argument("--max-items", type=int, default=0)
    parser.add_argument("--top", type=int, default=5, help="Candidates per item in CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument(
        "--merge-csv",
        type=Path,
        default=None,
        help="Upsert results into this CSV (preserves other canonical_ids)",
    )
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)

    if args.query:
        items = [
            {
                "canonical_id": "adhoc_query",
                "display_name": args.query,
                "search_query": args.query.strip(),
            }
        ]
        if args.csv == DEFAULT_CSV:
            args.csv = REPO_ROOT / "data/processed/safeway_baseline_candidates_adhoc.csv"
        if args.output == DEFAULT_JSONL:
            args.output = SCRIPT_DIR / "output/safeway_baseline_candidates_adhoc.jsonl"
    else:
        input_path = args.input if args.input.is_absolute() else REPO_ROOT / args.input
        if not input_path.is_file():
            logger.error("Missing %s", input_path)
            return 1
        items = load_baseline_queries(input_path)

    if args.product_id:
        items = [i for i in items if i["canonical_id"] == args.product_id.strip()]
        if not items:
            logger.error("No row for canonical_id=%r in input CSV", args.product_id)
            return 1

    if args.max_items > 0:
        items = items[: args.max_items]

    if not items:
        logger.error("No queries to run")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)

    timeout_sec = args.timeout if args.timeout is not None else load_timeout_seconds()

    try:
        successes, failures, csv_rows = run_http(
            items,
            output=args.output,
            csv_path=args.csv,
            top_n=args.top,
            delay=args.delay,
            timeout_sec=timeout_sec,
            browser_like=args.browser_like,
        )
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    if args.merge_csv:
        merge_target = (
            args.merge_csv if args.merge_csv.is_absolute() else REPO_ROOT / args.merge_csv
        )
        inserted, _ = merge_candidate_csv(
            merge_target, csv_rows, fieldnames=CANDIDATE_CSV_FIELDS
        )
        logger.info("Merged %d canonical_id(s) into %s", inserted, merge_target)

    logger.info(
        "Done — %d success, %d failure — wrote %s and %s",
        successes,
        failures,
        args.output,
        args.csv,
    )
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
