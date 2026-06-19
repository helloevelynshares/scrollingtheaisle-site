#!/usr/bin/env python3
"""
Fetch Vons (Albertsons SoCal) baseline prices — HTTP first, Playwright fallback.

Uses the same search UI/API as Safeway:
  https://www.vons.com/shop/search-results.html?q=grapes&tab=products

Setup:
  pip install -r scripts/requirements.txt
  python3 -m playwright install chromium  # fallback if HTTP times out

  scripts/.env: VONS_COOKIE, VONS_VISITOR_ID, VONS_UUID, VONS_STORE_ID, VONS_ZIPCODE
  Reuse SAFEWAY_SUBSCRIPTION_KEY + SAFEWAY_USER_AGENT (see scripts/.env.example)

Examples:
  python scripts/seed_vons_baseline_playwright.py
  python scripts/seed_vons_baseline_playwright.py --headful --channel chrome --delay 3
  python scripts/seed_vons_baseline_playwright.py --headful --manual-session --fresh-profile
  python scripts/seed_vons_baseline_playwright.py --http-only --query grapes
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

from albertsons_store import SEARCH_API_PATH, VONS_SOCAL
from safeway_candidates import (
    CANDIDATE_CSV_FIELDS,
    doc_to_candidate_row,
    extract_product_docs,
)
from vons_client import (
    IN_BROWSER_FETCH_JS,
    auth_message,
    build_pgmsearch_url,
    build_vons_headers,
    outcome_to_record,
    search_vons_product,
    stuck_loading_message,
    timeout_message,
)
from vons_config import VonsSearchConfig, load_timeout_seconds

DEFAULT_QUERIES = REPO_ROOT / "data/canonical/price_tracker_baseline_queries.csv"
DEFAULT_JSONL = SCRIPT_DIR / "output/vons_baseline_candidates.jsonl"
DEFAULT_CSV = REPO_ROOT / "data/processed/vons_baseline_candidates_v1.csv"
FEED_ID = "vons_albertsons_socal"

logger = logging.getLogger("seed_vons_baseline")


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


def is_product_search_response(url: str) -> bool:
    return SEARCH_API_PATH in url


def _page_debug_hint(page: Any) -> str:
    try:
        return f"url={page.url} title={page.title()!r}"
    except Exception:
        return "url/title unavailable"


STUCK_LOADING_HINT = (
    "Search UI stuck loading (pgmsearch never fired). "
    "Refresh VONS_COOKIE from vons.com DevTools → Network → pgmsearch; "
    "confirm VONS_STORE_ID/VONS_ZIPCODE/VONS_CHANNEL match that request "
    "(defaults: store 2053, zip 92110, channel instore). "
    "Or run --headful --channel chrome --manual-session --fresh-profile."
)

STUCK_LOADING_JS = """
() => {
  const spinners = document.querySelectorAll(
    '[class*="loading"], [class*="spinner"], [class*="Loader"], [aria-busy="true"]'
  );
  const products = document.querySelectorAll(
    '[data-qa="prd-itm"], [data-qa="product-card"], .product-card'
  );
  const bodyText = (document.body && document.body.innerText) || "";
  const mentionsLoading = /loading|please wait/i.test(bodyText.slice(0, 4000));
  return {
    spinnerCount: spinners.length,
    productCount: products.length,
    mentionsLoading,
  };
}
"""


def _page_loading_state(page: Any) -> dict[str, Any]:
    try:
        state = page.evaluate(STUCK_LOADING_JS)
        if isinstance(state, dict):
            return state
    except Exception:
        pass
    return {}


def _stuck_loading_message(page: Any) -> str | None:
    state = _page_loading_state(page)
    if not state:
        return None
    if state.get("productCount", 0) > 0:
        return None
    if state.get("spinnerCount", 0) > 0 or state.get("mentionsLoading"):
        return STUCK_LOADING_HINT
    return None


def _record_from_payload(
    query: str,
    *,
    status_code: int | None,
    payload: Any,
    api_url: str,
    source: str,
    error: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    if error is None and status_code == 200 and payload is not None:
        ok = True
    else:
        ok = False
        error = error or (None if ok else "empty_response")
    record: dict[str, Any] = {
        "query": query,
        "ok": ok,
        "status_code": status_code,
        "url": api_url,
        "error": error,
        "response": payload,
        "capture_source": source,
    }
    if message:
        record["message"] = message
    return record


def _capture_via_xhr(
    page: Any,
    query: str,
    *,
    navigation_timeout_ms: int,
    api_timeout_ms: int,
    reload_page: bool = False,
) -> dict[str, Any]:
    page_url = VONS_SOCAL.search_page_url(query)
    error: str | None = None
    status_code: int | None = None
    api_url: str | None = None
    payload: Any = None
    message: str | None = None
    api_timeout_sec = api_timeout_ms / 1000.0

    try:
        if reload_page:
            nav_action = lambda: page.reload(wait_until="commit", timeout=navigation_timeout_ms)
        else:
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
        response = response_info.value
        status_code = response.status
        api_url = response.url
        try:
            payload = response.json()
        except Exception as exc:
            error = "invalid_json"
            logger.warning("Could not parse JSON for q=%r: %s", query, exc)
        if status_code != 200:
            error = error or f"http_{status_code}"
            if status_code in (401, 403):
                message = auth_message(status_code, query=query)
                logger.warning("%s", message)
            else:
                message = f"Vons pgmsearch returned HTTP {status_code} for q={query!r}"
                logger.warning("%s", message)
        elif payload is None:
            error = error or "empty_response"
            message = f"Vons pgmsearch returned HTTP 200 with empty JSON for q={query!r}"
            logger.warning("%s", message)
    except Exception as exc:
        exc_name = type(exc).__name__
        hint = _page_debug_hint(page)
        if "Timeout" in exc_name:
            error = "api_timeout"
            message = stuck_loading_message(api_timeout_sec, query=query)
            stuck_hint = _stuck_loading_message(page)
            logger.error("%s (%s). %s", message, hint, stuck_hint or STUCK_LOADING_HINT)
        else:
            error = "navigation"
            message = f"Vons search navigation failed for q={query!r}: {exc}"
            logger.error("%s (%s)", message, hint)

    return _record_from_payload(
        query,
        status_code=status_code,
        payload=payload,
        api_url=api_url or page_url,
        source="playwright_xhr",
        error=error,
        message=message,
    )


def _capture_via_playwright_request(
    context: Any,
    query: str,
    config: VonsSearchConfig,
    *,
    timeout_ms: int,
) -> dict[str, Any]:
    url = build_pgmsearch_url(query, config)
    headers = build_vons_headers(query, config)
    # Cookie jar is already populated on the browser context — duplicating Cookie
    # in APIRequestContext can confuse Imperva and bloat error logs.
    headers.pop("Cookie", None)
    try:
        response = context.request.get(
            url,
            headers=headers,
            timeout=timeout_ms,
        )
        status_code = response.status
        try:
            payload = response.json()
        except Exception:
            return _record_from_payload(
                query,
                status_code=status_code,
                payload=None,
                api_url=url,
                source="playwright_request",
                error="invalid_json",
            )
        return _record_from_payload(
            query,
            status_code=status_code,
            payload=payload,
            api_url=url,
            source="playwright_request",
            error=None if status_code == 200 else f"http_{status_code}",
        )
    except Exception as exc:
        logger.warning("Playwright request fallback failed for q=%r: %s", query, exc)
        return _record_from_payload(
            query,
            status_code=None,
            payload=None,
            api_url=url,
            source="playwright_request",
            error="request_failed",
        )


def _capture_via_in_browser_fetch(
    page: Any,
    query: str,
    config: VonsSearchConfig,
) -> dict[str, Any]:
    url = build_pgmsearch_url(query, config)
    try:
        result = page.evaluate(
            IN_BROWSER_FETCH_JS,
            {"url": url, "subscriptionKey": config.subscription_key},
        )
    except Exception as exc:
        logger.warning("In-browser fetch failed for q=%r: %s", query, exc)
        return _record_from_payload(
            query,
            status_code=None,
            payload=None,
            api_url=url,
            source="in_browser_fetch",
            error="evaluate_failed",
        )

    status_code = result.get("status")
    if result.get("error"):
        return _record_from_payload(
            query,
            status_code=status_code,
            payload=result.get("payload"),
            api_url=url,
            source="in_browser_fetch",
            error=str(result.get("error")),
        )
    return _record_from_payload(
        query,
        status_code=status_code,
        payload=result.get("payload"),
        api_url=url,
        source="in_browser_fetch",
        error=None if status_code == 200 else f"http_{status_code}",
    )


def capture_vons_search(
    page: Any,
    context: Any,
    query: str,
    config: VonsSearchConfig,
    *,
    navigation_timeout_ms: int,
    api_timeout_ms: int,
    http_timeout_sec: float,
    reload_page: bool = False,
) -> dict[str, Any]:
    record = _capture_via_xhr(
        page,
        query,
        navigation_timeout_ms=navigation_timeout_ms,
        api_timeout_ms=api_timeout_ms,
        reload_page=reload_page,
    )
    if record["ok"]:
        logger.info("Captured pgmsearch via XHR for %r", query)
        return record

    logger.info("Trying Playwright request context for %r …", query)
    record = _capture_via_playwright_request(
        context,
        query,
        config,
        timeout_ms=max(api_timeout_ms, 60_000),
    )
    if record["ok"]:
        logger.info("Captured pgmsearch via Playwright request for %r", query)
        return record

    logger.info("Trying in-browser fetch for %r …", query)
    record = _capture_via_in_browser_fetch(page, query, config)
    if record["ok"]:
        logger.info("Captured pgmsearch via in-browser fetch for %r", query)
        return record

    logger.info("Trying direct HTTP for %r …", query)
    outcome = search_vons_product(query, timeout_sec=http_timeout_sec, config=config)
    record = outcome_to_record(outcome, source="http_requests")
    if record["ok"]:
        logger.info("Captured pgmsearch via HTTP for %r", query)
    else:
        logger.error(
            "All capture methods failed for q=%r (last error=%s). %s",
            query,
            record.get("error"),
            record.get("message")
            or timeout_message(http_timeout_sec, query=query),
        )
    return record


def flatten_candidates(
    record: dict[str, Any],
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


def run_http_first_with_playwright_fallback(
    items: list[dict[str, str]],
    config: VonsSearchConfig,
    *,
    output: Path,
    csv_path: Path,
    top_n: int,
    delay: float,
    http_timeout_sec: float,
    headful: bool,
    nav_ms: int,
    api_ms: int,
    no_env_cookies: bool,
    channel: str = "chromium",
    fresh_profile: bool = False,
    manual_session: bool = False,
    pause_before_search: bool = False,
    inject_cookies_first: bool = False,
) -> tuple[int, int, int, int]:
    """HTTP for all items; Playwright for HTTP failures."""
    from playwright.sync_api import sync_playwright

    records_by_index: list[dict[str, Any] | None] = [None] * len(items)
    http_ok = 0
    playwright_ok = 0
    playwright_needed: list[tuple[int, dict[str, str]]] = []
    request_delay = delay

    for index, item in enumerate(items):
        if index > 0:
            time.sleep(request_delay)
        query = item["search_query"]
        logger.info("HTTP search for %r (%s)", query, item["canonical_id"])
        outcome = search_vons_product(query, timeout_sec=http_timeout_sec, config=config)
        record = outcome_to_record(outcome, source="http")
        records_by_index[index] = record
        if record["ok"]:
            http_ok += 1
        else:
            playwright_needed.append((index, item))
            if record.get("message"):
                logger.error("%s", record["message"])
            elif record.get("error") == "timeout":
                logger.error("%s", timeout_message(http_timeout_sec, query=query))

    if playwright_needed:
        with sync_playwright() as playwright:
            context, page, _profile = launch_vons_browser(
                playwright,
                headful=headful,
                channel=channel,
                fresh_profile=fresh_profile,
            )

            prepare_vons_playwright_session(
                context,
                page,
                headful=headful,
                no_env_cookies=no_env_cookies,
                manual_session=manual_session,
                pause_before_search=pause_before_search,
                inject_cookies_first=inject_cookies_first,
            )

            for pw_index, (index, item) in enumerate(playwright_needed):
                if pw_index > 0:
                    time.sleep(delay)
                query = item["search_query"]
                logger.info("Playwright fallback for %r (%s)", query, item["canonical_id"])
                record = capture_vons_search(
                    page,
                    context,
                    query,
                    config,
                    navigation_timeout_ms=nav_ms,
                    api_timeout_ms=api_ms,
                    http_timeout_sec=http_timeout_sec,
                )
                if not record["ok"] and record.get("error") in ("api_timeout", "search_stuck_loading"):
                    record = capture_vons_search(
                        page,
                        context,
                        query,
                        config,
                        navigation_timeout_ms=nav_ms,
                        api_timeout_ms=api_ms,
                        http_timeout_sec=http_timeout_sec,
                        reload_page=True,
                    )
                records_by_index[index] = record
                if record["ok"]:
                    playwright_ok += 1

            context.close()

    all_csv_rows: list[dict[str, str]] = []
    successes = 0
    failures = 0

    with output.open("w", encoding="utf-8") as out_file:
        for index, item in enumerate(items):
            record = records_by_index[index]
            if record is None:
                record = {
                    "query": item["search_query"],
                    "ok": False,
                    "error": "skipped",
                    "capture_source": "none",
                }
            record["canonical_id"] = item["canonical_id"]
            record["display_name"] = item["display_name"]
            record["feed_id"] = FEED_ID
            out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            if record["ok"]:
                successes += 1
                all_csv_rows.extend(flatten_candidates(record, item, top_n=top_n))
            else:
                failures += 1

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_csv_rows)

    return successes, failures, http_ok, playwright_ok


def run_http_only(
    items: list[dict[str, str]],
    *,
    output: Path,
    csv_path: Path,
    top_n: int,
    delay: float,
    timeout_sec: float,
) -> tuple[int, int, list[dict[str, str]]]:
    config = VonsSearchConfig.from_env()
    all_csv_rows: list[dict[str, str]] = []
    successes = 0
    failures = 0

    with output.open("w", encoding="utf-8") as out_file:
        for index, item in enumerate(items):
            if index > 0:
                time.sleep(delay)
            query = item["search_query"]
            logger.info("HTTP search Vons for %r (%s)", query, item["canonical_id"])
            outcome = search_vons_product(query, timeout_sec=timeout_sec, config=config)
            record = outcome_to_record(outcome, source="http_only")
            record["canonical_id"] = item["canonical_id"]
            record["display_name"] = item["display_name"]
            record["feed_id"] = FEED_ID
            out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            if record["ok"]:
                successes += 1
                all_csv_rows.extend(flatten_candidates(record, item, top_n=top_n))
            else:
                failures += 1
                if record.get("message"):
                    logger.error("%s", record["message"])
                elif record.get("error") == "timeout":
                    logger.error("%s", timeout_message(timeout_sec, query=query))

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_csv_rows)

    return successes, failures, all_csv_rows


def launch_vons_browser(
    playwright: Any,
    *,
    headful: bool,
    channel: str,
    fresh_profile: bool,
) -> tuple[Any, Any, Path]:
    from playwright_session import reset_playwright_profile

    profile_dir = VONS_SOCAL.profile_dir
    if fresh_profile:
        reset_playwright_profile(profile_dir)
    else:
        profile_dir.mkdir(parents=True, exist_ok=True)

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=not headful,
        channel=channel,
        viewport={"width": 1280, "height": 720},
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.pages[0] if context.pages else context.new_page()
    return context, page, profile_dir


def prepare_vons_playwright_session(
    context: Any,
    page: Any,
    *,
    headful: bool,
    no_env_cookies: bool,
    manual_session: bool,
    pause_before_search: bool,
    inject_cookies_first: bool,
) -> None:
    from playwright_session import prepare_store_session

    prepare_store_session(
        context,
        page,
        store=VONS_SOCAL,
        headful=headful,
        use_env_cookies=not no_env_cookies and not manual_session,
        manual_session=manual_session,
        pause_before_search=pause_before_search,
        inject_cookies_first=inject_cookies_first,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Vons baseline prices via Playwright.")
    parser.add_argument("--query", help="Single search term (e.g. grapes)")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_QUERIES,
        help="CSV with canonical_id, search_query",
    )
    parser.add_argument("--headful", action="store_true")
    parser.add_argument("--http-only", action="store_true", help="Skip Playwright fallback")
    parser.add_argument(
        "--playwright-only",
        action="store_true",
        help="Skip HTTP; use Playwright capture chain only",
    )
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--max-items", type=int, default=0)
    parser.add_argument("--top", type=int, default=5, help="Candidates per item in CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--navigation-timeout", type=int, default=60)
    parser.add_argument("--api-timeout", type=int, default=45)
    parser.add_argument(
        "--http-timeout",
        type=int,
        default=None,
        help="HTTP/curl timeout seconds (default: VONS_TIMEOUT_SECONDS or 45)",
    )
    parser.add_argument(
        "--channel",
        default="chromium",
        choices=("chromium", "chrome"),
        help="Browser channel (try chrome if chromium is blocked)",
    )
    parser.add_argument("--no-env-cookies", action="store_true")
    parser.add_argument(
        "--manual-session",
        action="store_true",
        help="Headful: skip .env cookies; log in and set store manually (saved in profile)",
    )
    parser.add_argument(
        "--fresh-profile",
        action="store_true",
        help="Delete scripts/.playwright-profile-vons before launch (fixes corrupted sessions)",
    )
    parser.add_argument(
        "--pause-before-search",
        action="store_true",
        help="Headful: wait for Enter after store setup before first search",
    )
    parser.add_argument(
        "--inject-cookies-first",
        action="store_true",
        help="Inject VONS_COOKIE before store setup (legacy; can cause stuck loading in headful)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    configure_logging(args.verbose)

    if args.manual_session and not args.headful:
        logger.error("--manual-session requires --headful")
        return 1

    if args.query:
        items = [
            {
                "canonical_id": "adhoc_query",
                "display_name": args.query,
                "search_query": args.query.strip(),
            }
        ]
    else:
        input_path = args.input if args.input.is_absolute() else REPO_ROOT / args.input
        if not input_path.is_file():
            logger.error("Missing %s", input_path)
            return 1
        items = load_baseline_queries(input_path)

    if args.max_items > 0:
        items = items[: args.max_items]

    if not items:
        logger.error("No queries to run")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)

    from dotenv import load_dotenv

    load_dotenv(SCRIPT_DIR / ".env")
    http_timeout = (
        float(args.http_timeout)
        if args.http_timeout is not None
        else load_timeout_seconds()
    )

    try:
        config = VonsSearchConfig.from_env()
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    if args.http_only:
        successes, failures, _ = run_http_only(
            items,
            output=args.output,
            csv_path=args.csv,
            top_n=args.top,
            delay=args.delay,
            timeout_sec=http_timeout,
        )
        logger.info(
            "Done — %d success, %d failure — wrote %s and %s (http_timeout=%.0fs)",
            successes,
            failures,
            args.output,
            args.csv,
            http_timeout,
        )
        return 0 if failures == 0 else 2

    if not args.playwright_only:
        try:
            successes, failures, http_ok, playwright_ok = run_http_first_with_playwright_fallback(
                items,
                config,
                output=args.output,
                csv_path=args.csv,
                top_n=args.top,
                delay=args.delay,
                http_timeout_sec=http_timeout,
                headful=args.headful,
                nav_ms=args.navigation_timeout * 1000,
                api_ms=args.api_timeout * 1000,
                no_env_cookies=args.no_env_cookies,
                channel=args.channel,
                fresh_profile=args.fresh_profile,
                manual_session=args.manual_session,
                pause_before_search=args.pause_before_search,
                inject_cookies_first=args.inject_cookies_first,
            )
            logger.info(
                "Done — %d success (%d HTTP, %d Playwright), %d failure — wrote %s and %s",
                successes,
                http_ok,
                playwright_ok,
                failures,
                args.output,
                args.csv,
            )
            return 0 if failures == 0 else 2
        except Exception as exc:
            if "Executable doesn't exist" not in str(exc):
                raise
            logger.warning(
                "Playwright browser missing (%s) — retrying HTTP-only for remaining items",
                exc,
            )
            successes, failures, _ = run_http_only(
                items,
                output=args.output,
                csv_path=args.csv,
                top_n=args.top,
                delay=args.delay,
                timeout_sec=http_timeout,
            )
            logger.info(
                "Done — %d success, %d failure — wrote %s and %s (http_timeout=%.0fs)",
                successes,
                failures,
                args.output,
                args.csv,
                http_timeout,
            )
            return 0 if failures == 0 else 2

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Install playwright: pip install playwright && python3 -m playwright install chromium")
        return 1

    nav_ms = args.navigation_timeout * 1000
    api_ms = args.api_timeout * 1000

    all_csv_rows: list[dict[str, str]] = []
    successes = 0
    failures = 0

    with sync_playwright() as playwright:
        context, page, profile_dir = launch_vons_browser(
            playwright,
            headful=args.headful,
            channel=args.channel,
            fresh_profile=args.fresh_profile,
        )
        if args.headful:
            logger.info(
                "Headful Playwright; profile=%s. If search spins forever, try "
                "--manual-session --fresh-profile or refresh VONS_COOKIE.",
                profile_dir,
            )

        prepare_vons_playwright_session(
            context,
            page,
            headful=args.headful,
            no_env_cookies=args.no_env_cookies,
            manual_session=args.manual_session,
            pause_before_search=args.pause_before_search,
            inject_cookies_first=args.inject_cookies_first,
        )

        with args.output.open("w", encoding="utf-8") as out_file:
            for index, item in enumerate(items):
                if index > 0:
                    time.sleep(args.delay)

                query = item["search_query"]
                logger.info("Searching Vons for %r (%s)", query, item["canonical_id"])
                record = capture_vons_search(
                    page,
                    context,
                    query,
                    config,
                    navigation_timeout_ms=nav_ms,
                    api_timeout_ms=api_ms,
                    http_timeout_sec=http_timeout,
                )
                if not record["ok"] and record.get("error") in ("api_timeout", "search_stuck_loading"):
                    logger.info("Retrying %r after reload …", query)
                    record = capture_vons_search(
                        page,
                        context,
                        query,
                        config,
                        navigation_timeout_ms=nav_ms,
                        api_timeout_ms=api_ms,
                        http_timeout_sec=http_timeout,
                        reload_page=True,
                    )

                record["canonical_id"] = item["canonical_id"]
                record["display_name"] = item["display_name"]
                record["feed_id"] = FEED_ID
                out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_file.flush()

                if record["ok"]:
                    successes += 1
                    all_csv_rows.extend(
                        flatten_candidates(record, item, top_n=args.top)
                    )
                else:
                    failures += 1
                    if record.get("message"):
                        logger.error("%s", record["message"])

        context.close()

    with args.csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_csv_rows)

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
