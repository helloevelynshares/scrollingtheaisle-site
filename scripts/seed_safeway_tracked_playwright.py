#!/usr/bin/env python3
"""
Fetch Safeway search candidates for TikTok-informed tracked items (ledger v1).

Runs Playwright for each ledger search_query with status=needs_selection (default).
Writes:
  - scripts/output/safeway_tracked_candidates.jsonl (full API payloads)
  - data/processed/safeway_tracked_candidates_v1.csv (top N candidates per item for manual SKU pick)

Setup:
  pip install -r scripts/requirements.txt
  playwright install chromium

Examples:
  python scripts/seed_safeway_tracked_playwright.py --query oreo --headful
  python scripts/seed_safeway_tracked_playwright.py --headful
  python scripts/seed_safeway_tracked_playwright.py --headful --delay 3 --resume
  python scripts/seed_safeway_tracked_playwright.py --max-items 5 --delay 3
  python scripts/seed_safeway_tracked_playwright.py --status all
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from ledger import load_tracked_items
from safeway_candidates import (
    CANDIDATE_CSV_FIELDS,
    doc_to_candidate_row,
    extract_product_docs,
)
from seed_safeway_search_playwright import (
    PROFILE_DIR,
    capture_search,
    configure_logging,
)

DEFAULT_LEDGER = REPO_ROOT / "data/canonical/safeway_tracked_items_v1.csv"
DEFAULT_JSONL = SCRIPT_DIR / "output" / "safeway_tracked_candidates.jsonl"
DEFAULT_CANDIDATES_CSV = REPO_ROOT / "data/processed/safeway_tracked_candidates_v1.csv"

logger = logging.getLogger("seed_safeway_tracked_playwright")


def resolve_ledger_items(
    all_items: list[dict[str, str]],
    *,
    query_filter: str | None,
) -> list[dict[str, str]]:
    """Match --query to canonical_id, else substring in id/name/search_query."""
    if not query_filter:
        return all_items

    needle = query_filter.strip().lower()
    exact = [r for r in all_items if r.get("canonical_id", "").lower() == needle]
    if exact:
        return exact

    partial = [
        r
        for r in all_items
        if needle in r.get("canonical_id", "").lower()
        or needle in r.get("display_name", "").lower()
        or needle in r.get("search_query", "").lower()
    ]
    if partial:
        return partial

    logger.warning(
        "No ledger row matched %r — running one-off search (not saved to ledger)",
        query_filter,
    )
    return [
        {
            "canonical_id": "adhoc_query",
            "content_theme": "adhoc",
            "display_name": query_filter,
            "search_query": query_filter,
            "priority": "",
            "status": "",
        }
    ]


def load_existing_results(jsonl_path: Path) -> dict[str, dict]:
    """Load prior JSONL rows keyed by canonical_id (last line wins per id)."""
    by_id: dict[str, dict] = {}
    if not jsonl_path.is_file():
        return by_id
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        canonical_id = record.get("canonical_id")
        if canonical_id:
            by_id[canonical_id] = record
    return by_id


def select_items_to_run(
    items: list[dict[str, str]],
    existing: dict[str, dict],
    *,
    resume: bool,
    retry_failed: bool,
) -> tuple[list[dict[str, str]], int]:
    """Return items to fetch and count skipped (already ok)."""
    if not resume:
        return items, 0

    to_run: list[dict[str, str]] = []
    skipped = 0
    for item in items:
        canonical_id = item.get("canonical_id", "")
        prior = existing.get(canonical_id)
        if prior and prior.get("ok"):
            skipped += 1
            logger.info("Skipping %s (already succeeded)", canonical_id)
            continue
        if prior and not prior.get("ok") and not retry_failed:
            skipped += 1
            logger.info("Skipping %s (failed previously; use --retry-failed)", canonical_id)
            continue
        to_run.append(item)
    return to_run, skipped


def enrich_record(record: dict, item: dict[str, str], query: str) -> dict:
    record["canonical_id"] = item.get("canonical_id", "")
    record["display_name"] = item.get("display_name", "")
    record["content_theme"] = item.get("content_theme", "")
    record["search_query"] = query
    record["ledger_priority"] = item.get("priority", "")
    record["ledger_status"] = item.get("status", "")
    return record


def write_merged_outputs(
    items: list[dict[str, str]],
    merged: dict[str, dict],
    *,
    jsonl_path: Path,
    candidates_csv: Path,
    top_n: int,
) -> int:
    """Write JSONL in ledger order and rebuild candidates CSV from all ok rows."""
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    candidates_csv.parent.mkdir(parents=True, exist_ok=True)

    candidate_rows = 0
    with jsonl_path.open("w", encoding="utf-8") as jsonl_file:
        with candidates_csv.open("w", newline="", encoding="utf-8") as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=CANDIDATE_CSV_FIELDS)
            csv_writer.writeheader()
            for item in items:
                canonical_id = item.get("canonical_id", "")
                record = merged.get(canonical_id)
                if not record:
                    continue
                jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                if record.get("ok") and isinstance(record.get("response"), dict):
                    candidate_rows += append_candidate_rows(
                        csv_writer,
                        item=item,
                        payload=record["response"],
                        top_n=top_n,
                    )
    return candidate_rows


def append_candidate_rows(
    handle: csv.DictWriter,
    *,
    item: dict[str, str],
    payload: dict,
    top_n: int,
) -> int:
    docs = extract_product_docs(payload)[:top_n]
    for rank, doc in enumerate(docs, start=1):
        handle.writerow(
            doc_to_candidate_row(
                doc,
                rank=rank,
                canonical_id=item.get("canonical_id", ""),
                display_name=item.get("display_name", ""),
                search_query=item.get("search_query", ""),
                content_theme=item.get("content_theme", ""),
            )
        )
    return len(docs)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Playwright Safeway search for TikTok-informed tracked-item ledger.",
    )
    parser.add_argument(
        "--query",
        help="Run one item: match canonical_id or substring (e.g. oreo → oreo_original_family_size)",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help="Tracked items CSV (default: data/canonical/safeway_tracked_items_v1.csv)",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Show browser; use once to set store/session in scripts/.playwright-profile",
    )
    parser.add_argument(
        "--new-page-each",
        action="store_true",
        help="Open a fresh tab per search (helps if a modal left the previous page stuck)",
    )
    parser.add_argument(
        "--no-env-cookies",
        action="store_true",
        help="Do not inject SAFEWAY_COOKIE from scripts/.env",
    )
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between searches")
    parser.add_argument("--max-items", type=int, default=0, help="Limit items (0 = all)")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_JSONL,
        help="JSONL output with full API response per ledger row",
    )
    parser.add_argument(
        "--candidates-csv",
        type=Path,
        default=DEFAULT_CANDIDATES_CSV,
        help="Flat CSV of top candidates for manual accepted_pid/upc selection",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=15,
        help="Max Safeway product candidates per ledger row in CSV (default: 15)",
    )
    parser.add_argument("--navigation-timeout", type=int, default=90)
    parser.add_argument("--api-timeout", type=int, default=90)
    parser.add_argument(
        "--status",
        default="needs_selection",
        help="Only rows with this status (default: needs_selection; use 'all' for every row)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip canonical_ids that already succeeded in the output JSONL; merge results",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="With --resume, re-run items that failed previously (default: only run missing)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)

    ledger_path = args.ledger if args.ledger.is_absolute() else REPO_ROOT / args.ledger
    if not ledger_path.is_file():
        logger.error("Ledger not found: %s", ledger_path)
        return 1

    statuses = None if args.status.lower() == "all" else (args.status.lower(),)
    try:
        all_items = load_tracked_items(ledger_path, statuses=statuses)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    items = resolve_ledger_items(all_items, query_filter=args.query)
    if args.query and len(items) > 1:
        logger.info(
            "--query %r matched %d ledger row(s); running all matches",
            args.query,
            len(items),
        )

    if args.max_items > 0:
        items = items[: args.max_items]

    if not items:
        logger.error("No ledger rows to search (status=%s)", args.status)
        return 1

    existing = load_existing_results(args.output) if args.resume else {}
    to_run, skipped_ok = select_items_to_run(
        items,
        existing,
        resume=args.resume,
        retry_failed=args.retry_failed,
    )
    merged: dict[str, dict] = dict(existing) if args.resume else {}

    if args.resume:
        logger.info(
            "Resume: %d item(s) in scope, %d already ok (skipped), %d to run",
            len(items),
            skipped_ok,
            len(to_run),
        )
    if not to_run:
        logger.info("Nothing to run — all scoped items already succeeded.")
        if args.resume and items:
            candidate_rows = write_merged_outputs(
                items,
                merged,
                jsonl_path=args.output,
                candidates_csv=args.candidates_csv,
                top_n=args.top_n,
            )
            logger.info("Refreshed outputs — %d candidate rows", candidate_rows)
        return 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Install Playwright: pip install playwright && playwright install chromium")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.candidates_csv.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    nav_ms = args.navigation_timeout * 1000
    api_ms = args.api_timeout * 1000
    run_successes = 0
    run_failures = 0

    logger.info(
        "Running %d search(es) from %s; delay=%.1fs; top_n=%d",
        len(to_run),
        ledger_path.name,
        args.delay,
        args.top_n,
    )

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=not args.headful,
            channel="chromium",
            viewport={"width": 1280, "height": 720},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()

        from playwright_session import apply_env_cookies_to_context

        apply_env_cookies_to_context(
            context,
            page,
            use_env_cookies=not args.no_env_cookies,
        )

        def page_for_search() -> Any:
            if args.new_page_each:
                return context.new_page()
            return page

        for index, item in enumerate(to_run):
            if index > 0:
                time.sleep(args.delay)

            query = item["search_query"]
            search_page = page_for_search()
            try:
                record = capture_search(
                    search_page,
                    query,
                    navigation_timeout_ms=nav_ms,
                    api_timeout_ms=api_ms,
                )
            finally:
                if args.new_page_each and search_page is not page:
                    search_page.close()

            enrich_record(record, item, query)
            merged[item["canonical_id"]] = record
            if record["ok"]:
                run_successes += 1
            else:
                run_failures += 1

        context.close()

    candidate_rows = write_merged_outputs(
        items,
        merged,
        jsonl_path=args.output,
        candidates_csv=args.candidates_csv,
        top_n=args.top_n,
    )
    total_ok = sum(
        1 for item in items if merged.get(item["canonical_id"], {}).get("ok")
    )
    total_fail = len(items) - total_ok

    logger.info(
        "This run — %d success, %d failure",
        run_successes,
        run_failures,
    )
    logger.info(
        "Merged scope — %d/%d ok — jsonl: %s — candidates: %s (%d rows)",
        total_ok,
        len(items),
        args.output,
        args.candidates_csv,
        candidate_rows,
    )
    logger.info(
        "Copy accepted_pid/upc from %s into %s after manual review",
        args.candidates_csv.name,
        ledger_path.name,
    )
    return 0 if total_fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
