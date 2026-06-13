#!/usr/bin/env python3
"""
Seed Safeway product search for canonical grocery items (web pgmsearch API).

Single-query test (Chrome-like headers recommended):
  python scripts/seed_safeway_search.py --query oreo --browser-like --debug

Full canonical seed (requires scripts/.env — never commit):
  python scripts/seed_safeway_search.py --browser-like

Timeout: set SAFEWAY_TIMEOUT_SECONDS in scripts/.env (legacy: SAFEWAY_TIMEOUT_SEC).

If Python requests still time out while the same URL works in Chrome, Safeway may be
blocking non-browser TLS/client fingerprints. The next fallback is Playwright: drive a
real Chromium session, perform the search in-page, and read the JSON response (or
intercept the pgmsearch network call) instead of raw requests.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import requests
from dotenv import load_dotenv

from canonical_items import CANONICAL_ITEMS
from safeway_client import search_product
from safeway_config import load_config, load_timeout_seconds

DEFAULT_OUTPUT = SCRIPT_DIR / "output" / "safeway_search_seed.jsonl"


def configure_logging(verbose: bool, debug: bool) -> None:
    level = logging.DEBUG if verbose or debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    load_dotenv(SCRIPT_DIR / ".env")

    parser = argparse.ArgumentParser(
        description="Safeway web product search seeding.",
        epilog=(
            "If requests time out but Chrome succeeds, use --browser-like and SAFEWAY_COOKIE; "
            "if it still fails, use Playwright (real browser TLS fingerprint)."
        ),
    )
    parser.add_argument(
        "--query",
        help="Run a single search instead of the canonical 50 items",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print final URL (q visible), Cookie presence, headers with secrets redacted",
    )
    parser.add_argument(
        "--browser-like",
        "--copy-browser-mode",
        action="store_true",
        dest="browser_like",
        help="Send headers close to a successful Chrome search request",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=float(os.getenv("SAFEWAY_REQUEST_DELAY_SEC", "2.5")),
        help="Seconds between sequential requests (default: 2.5)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Per-request timeout seconds (default: SAFEWAY_TIMEOUT_SECONDS or 30)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output path (default for batch: scripts/output/safeway_search_seed.jsonl)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max canonical items to query (0 = all)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose, args.debug)
    log = logging.getLogger("seed_safeway_search")

    try:
        config = load_config()
    except (json.JSONDecodeError, ValueError) as exc:
        log.error("Invalid SAFEWAY_EXTRA_HEADERS: %s", exc)
        return 1

    missing = config.missing_fields()
    if missing:
        log.error(
            "Missing required .env value(s): %s — copy scripts/.env.example to scripts/.env",
            ", ".join(missing),
        )
        return 1

    timeout_sec = args.timeout if args.timeout is not None else load_timeout_seconds()

    if config.cookie:
        log.info("Cookie header will be sent (value not logged)")
    else:
        log.info("No SAFEWAY_COOKIE set")
    if config.extra_headers:
        log.info("Merging %d extra header(s) from SAFEWAY_EXTRA_HEADERS", len(config.extra_headers))
    if args.browser_like:
        log.info("Using browser-like header set")
        if not config.sec_ch_ua:
            log.warning(
                "SAFEWAY_SEC_CH_UA not set — sec-ch-ua omitted; "
                "set it to match your Chrome user-agent for best results"
            )

    if args.query:
        items = [args.query]
        output_path = args.output
    else:
        items = list(CANONICAL_ITEMS)
        if args.limit > 0:
            items = items[: args.limit]
        output_path = args.output or Path(
            os.getenv("SAFEWAY_OUTPUT_PATH", str(DEFAULT_OUTPUT))
        )

    session = requests.Session()
    successes = 0
    failures = 0
    records: list[dict] = []

    log.info(
        "Searching %d item(s); delay=%.1fs; timeout=%.1fs",
        len(items),
        args.delay,
        timeout_sec,
    )

    for index, item in enumerate(items):
        if index > 0:
            time.sleep(args.delay)

        outcome = search_product(
            session,
            item,
            config,
            timeout_sec=timeout_sec,
            debug=args.debug,
            browser_like=args.browser_like,
        )

        record = {
            "query": outcome.query,
            "ok": outcome.ok,
            "status_code": outcome.status_code,
            "error": outcome.error,
            "response": outcome.payload,
        }
        records.append(record)

        if outcome.ok:
            successes += 1
            if args.query and not output_path:
                print(json.dumps(outcome.payload, indent=2, ensure_ascii=False)[:4000])
        else:
            failures += 1
            if outcome.error == "timeout":
                log.warning(
                    "Request timed out — try --browser-like, SAFEWAY_COOKIE, or Playwright "
                    "if Chrome returns 200 for the same search"
                )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as out_file:
            for record in records:
                out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        log.info("Wrote %s", output_path)

    log.info("Done — %d success, %d failure", successes, failures)
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
