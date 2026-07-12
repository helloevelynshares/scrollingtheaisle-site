#!/usr/bin/env python3
"""
Safeway product search seeding via Playwright (browser TLS/session).

Use when raw Python requests time out but Chrome DevTools returns 200 for pgmsearch.

Setup:
  pip install -r scripts/requirements.txt
  playwright install chromium

Examples:
  python scripts/seed_safeway_search_playwright.py --query oreo --headful
  python scripts/seed_safeway_search_playwright.py \\
    --input data/canonical/manual_canonical_50.csv --max-items 5 --headful

Persistent profile: scripts/.playwright-profile
Also loads SAFEWAY_COOKIE from scripts/.env (same fix as requests, stops infinite loading)
Output: scripts/output/safeway_search_seed.jsonl
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
from urllib.parse import quote

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROFILE_DIR = SCRIPT_DIR / ".playwright-profile"
DEFAULT_OUTPUT = SCRIPT_DIR / "output" / "safeway_search_seed.jsonl"
SEARCH_API_PATH = "/abs/pub/xapi/pgmsearch/v1/search/products"

from safeway_client import auth_message, stuck_loading_message

QUERY_CSV_COLUMNS = ("search_query", "query", "canonical_item", "item", "name", "canonical")

logger = logging.getLogger("seed_safeway_playwright")


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def search_page_url(query: str) -> str:
    return (
        "https://www.safeway.com/shop/search-results.html"
        f"?q={quote(query)}&tab=products"
    )


def load_queries_from_csv(path: Path) -> list[str]:
    queries: list[str] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"No header row in {path}")
        column = next(
            (name for name in QUERY_CSV_COLUMNS if name in reader.fieldnames),
            None,
        )
        if not column:
            raise ValueError(
                f"{path} needs a column named one of: {', '.join(QUERY_CSV_COLUMNS)}"
            )
        for row in reader:
            value = (row.get(column) or "").strip()
            if value:
                queries.append(value)
    return queries


def resolve_queries(args: argparse.Namespace) -> list[str]:
    if args.query:
        return [args.query.strip()]
    if args.input:
        path = Path(args.input)
        if not path.is_absolute():
            path = REPO_ROOT / path
        if not path.is_file():
            raise FileNotFoundError(path)
        return load_queries_from_csv(path)
    raise SystemExit("Provide --query or --input")


def is_product_search_response(url: str) -> bool:
    return SEARCH_API_PATH in url


def _page_debug_hint(page: Any) -> str:
    try:
        return f"url={page.url} title={page.title()!r}"
    except Exception:
        return "url/title unavailable"


def _capture_search_once(
    page: Any,
    query: str,
    *,
    navigation_timeout_ms: int,
    api_timeout_ms: int,
    reload_page: bool = False,
) -> dict[str, Any]:
    page_url = search_page_url(query)
    error: str | None = None
    status_code: int | None = None
    api_url: str | None = None
    payload: Any = None
    message: str | None = None
    api_timeout_sec = api_timeout_ms / 1000.0

    try:
        if reload_page:
            logger.info("Reloading search page for %r …", query)
            nav_action = lambda: page.reload(wait_until="commit", timeout=navigation_timeout_ms)
        else:
            logger.info("Navigating for %r …", query)
            nav_action = lambda: page.goto(
                page_url,
                wait_until="commit",
                timeout=navigation_timeout_ms,
            )
        with page.expect_response(
            lambda response: is_product_search_response(response.url),
            timeout=api_timeout_ms,
        ) as response_info:
            nav_action()
        logger.info("Captured pgmsearch API for %r", query)
        response = response_info.value
        status_code = response.status
        api_url = response.url
        try:
            payload = response.json()
        except Exception as exc:
            logger.warning("Could not parse JSON for q=%r: %s", query, exc)
            error = "invalid_json"
        if status_code != 200:
            error = error or f"http_{status_code}"
            if status_code in (401, 403):
                message = auth_message(status_code, query=query)
                logger.warning("%s", message)
            elif status_code == 429:
                message = f"Safeway pgmsearch rate limited (429) for q={query!r}"
                logger.warning("%s", message)
        elif payload is None:
            error = error or "empty_response"
            message = f"Safeway pgmsearch returned HTTP 200 with empty JSON for q={query!r}"
            logger.warning("%s", message)
    except Exception as exc:
        exc_name = type(exc).__name__
        hint = _page_debug_hint(page)
        if "Timeout" in exc_name:
            error = "api_timeout"
            message = stuck_loading_message(api_timeout_sec, query=query)
            logger.error("%s (%s)", message, hint)
        else:
            error = "navigation"
            message = f"Safeway search navigation failed for q={query!r}: {exc}"
            logger.error("%s (%s)", message, hint)

    ok = status_code == 200 and payload is not None and error is None
    if ok:
        logger.info("200 success for q=%r: %s", query, api_url or page_url)

    record: dict[str, Any] = {
        "query": query,
        "ok": ok,
        "status_code": status_code,
        "url": api_url or page_url,
        "error": error,
        "response": payload,
    }
    if message:
        record["message"] = message
    return record


def capture_search(
    page: Any,
    query: str,
    *,
    navigation_timeout_ms: int,
    api_timeout_ms: int,
    allow_reload_retry: bool = True,
) -> dict[str, Any]:
    """
    Load Safeway search results and capture the pgmsearch XHR.

    Uses wait_until=commit (not domcontentloaded) because Safeway often never
    finishes DOM load while analytics keep running, that made runs look stuck.
    """
    record = _capture_search_once(
        page,
        query,
        navigation_timeout_ms=navigation_timeout_ms,
        api_timeout_ms=api_timeout_ms,
    )
    if record.get("error") == "api_timeout" and allow_reload_retry:
        logger.info("Retrying %r after reload (session cookies may need a moment) …", query)
        record = _capture_search_once(
            page,
            query,
            navigation_timeout_ms=navigation_timeout_ms,
            api_timeout_ms=api_timeout_ms,
            reload_page=True,
        )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed Safeway search results via Playwright Chromium.",
    )
    parser.add_argument("--query", help="Single search term (e.g. oreo)")
    parser.add_argument(
        "--input",
        type=str,
        help="CSV path with query/canonical_item column (repo-relative OK)",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Show browser; use once to log in and set store/location (saved in profile)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Seconds between sequential searches (default: 3)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="Limit number of queries (0 = all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="JSONL output path",
    )
    parser.add_argument(
        "--navigation-timeout",
        type=int,
        default=60,
        help="Page load timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--api-timeout",
        type=int,
        default=45,
        help="Wait for pgmsearch response in seconds (default: 45)",
    )
    parser.add_argument(
        "--no-env-cookies",
        action="store_true",
        help="Do not inject SAFEWAY_COOKIE from scripts/.env",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)

    try:
        queries = resolve_queries(args)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        return 1

    if args.max_items > 0:
        queries = queries[: args.max_items]

    if not queries:
        logger.error("No queries to run")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
        return 1

    nav_ms = args.navigation_timeout * 1000
    api_ms = args.api_timeout * 1000
    successes = 0
    failures = 0

    logger.info(
        "Starting Playwright (%s); %d query(ies); delay=%.1fs; profile=%s",
        "headful" if args.headful else "headless",
        len(queries),
        args.delay,
        PROFILE_DIR,
    )
    if args.headful:
        logger.info(
            "Headful mode: set store/location or sign in in the browser if prompted. "
            "Session is saved under scripts/.playwright-profile"
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

        with args.output.open("w", encoding="utf-8") as out_file:
            for index, query in enumerate(queries):
                if index > 0:
                    time.sleep(args.delay)

                record = capture_search(
                    page,
                    query,
                    navigation_timeout_ms=nav_ms,
                    api_timeout_ms=api_ms,
                )
                out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_file.flush()

                if record["ok"]:
                    successes += 1
                else:
                    failures += 1
                    if record.get("message"):
                        logger.error("%s", record["message"])

        context.close()

    logger.info(
        "Done: %d success, %d failure, wrote %s",
        successes,
        failures,
        args.output,
    )
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
