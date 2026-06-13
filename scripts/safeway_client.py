"""Safeway web product search client (pgmsearch API)."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from requests import PreparedRequest
from requests.exceptions import RequestException, Timeout

from safeway_config import SafewaySearchConfig

SEARCH_URL = "https://www.safeway.com/abs/pub/xapi/pgmsearch/v1/search/products"

BASE_QUERY_PARAMS: dict[str, str] = {
    "url": "https://www.safeway.com",
    "pageurl": "https://www.safeway.com",
    "pagename": "search",
    "rows": "30",
    "start": "0",
    "search-type": "keyword",
    "storeid": "2843",
    "featured": "true",
    "sort": "",
    "timezone": "America/Los_Angeles",
    "dvid": "web-4.1search",
    "channel": "pickup",
    "pp": "true",
    "wineshopstoreid": "5799",
    "zipcode": "94044",
    "pgm": "wineshop,merch-banner",
    "includeOffer": "true",
    "banner": "safeway",
}

BROWSER_LIKE_ACCEPT_LANGUAGE = "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
DEFAULT_ACCEPT_LANGUAGE = "en-US,en;q=0.9"

SENSITIVE_HEADER_NAMES = frozenset({"cookie", "ocp-apim-subscription-key"})
SENSITIVE_QUERY_KEYS = frozenset({"visitorid", "uuid"})

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SearchOutcome:
    query: str
    status_code: int | None
    ok: bool
    payload: dict[str, Any] | list[Any] | None
    error: str | None = None
    request_url: str | None = None


def generate_request_id() -> str:
    """Browser-style long numeric request-id (not a UUID)."""
    # time_ns() is typically 19 digits, matching captures like 1621779662930545269
    return str(time.time_ns())


def build_search_params(query: str, config: SafewaySearchConfig) -> dict[str, str]:
    params = dict(BASE_QUERY_PARAMS)
    params["request-id"] = generate_request_id()
    params["q"] = query
    params["visitorId"] = config.visitor_id
    params["uuid"] = config.uuid
    return params


def _apply_sec_ch_headers(headers: dict[str, str], config: SafewaySearchConfig) -> None:
    """Only send sec-ch-ua* when configured — avoids conflicting with user-agent."""
    if config.sec_ch_ua:
        headers["sec-ch-ua"] = config.sec_ch_ua
    if config.sec_ch_ua_mobile:
        headers["sec-ch-ua-mobile"] = config.sec_ch_ua_mobile
    if config.sec_ch_ua_platform:
        headers["sec-ch-ua-platform"] = config.sec_ch_ua_platform


def build_headers(
    query: str,
    config: SafewaySearchConfig,
    *,
    browser_like: bool = False,
) -> dict[str, str]:
    referer = (
        "https://www.safeway.com/shop/search-results.html"
        f"?q={requests.utils.quote(query)}&tab=products"
    )
    headers: dict[str, str] = {
        "accept": "application/json, text/plain, */*",
        "ocp-apim-subscription-key": config.subscription_key,
        "referer": referer,
        "user-agent": config.user_agent,
    }

    if browser_like:
        headers["accept-language"] = BROWSER_LIKE_ACCEPT_LANGUAGE
        headers["sec-fetch-dest"] = "empty"
        headers["sec-fetch-mode"] = "cors"
        headers["sec-fetch-site"] = "same-origin"
        if config.sec_ch_ua:
            headers["sec-ch-ua"] = config.sec_ch_ua
        headers["sec-ch-ua-mobile"] = config.sec_ch_ua_mobile or "?0"
        headers["sec-ch-ua-platform"] = config.sec_ch_ua_platform or '"macOS"'
    else:
        headers["accept-language"] = DEFAULT_ACCEPT_LANGUAGE
        _apply_sec_ch_headers(headers, config)

    if config.extra_headers:
        headers.update(config.extra_headers)
    if config.cookie:
        headers["Cookie"] = config.cookie
    return headers


def prepare_request(
    session: requests.Session,
    query: str,
    config: SafewaySearchConfig,
    *,
    browser_like: bool = False,
) -> PreparedRequest:
    params = build_search_params(query, config)
    headers = build_headers(query, config, browser_like=browser_like)
    req = requests.Request("GET", SEARCH_URL, params=params, headers=headers)
    return session.prepare_request(req)


def redact_url(url: str) -> str:
    parts = urlsplit(url)
    query_pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            query_pairs.append((key, "<redacted>"))
        else:
            query_pairs.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment))


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADER_NAMES:
            redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    return redacted


def log_debug_request(prepared: PreparedRequest, config: SafewaySearchConfig) -> None:
    cookie_line = (
        "present (<redacted>)"
        if config.cookie
        else "not set"
    )
    print("--- debug request ---", flush=True)
    print(f"Cookie: {cookie_line}", flush=True)
    print(f"URL: {redact_url(prepared.url)}", flush=True)
    print("Headers:", flush=True)
    for key, value in sorted(redact_headers(dict(prepared.headers)).items()):
        print(f"  {key}: {value}", flush=True)
    print("---------------------", flush=True)


def _summarize_payload(payload: Any) -> str:
    if payload is None:
        return "empty body"
    if isinstance(payload, dict):
        for key in ("products", "productList", "items", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return f"{len(value)} result(s) under '{key}'"
        return f"keys: {', '.join(sorted(payload.keys())[:8])}"
    if isinstance(payload, list):
        return f"{len(payload)} top-level item(s)"
    return type(payload).__name__


def search_product(
    session: requests.Session,
    query: str,
    config: SafewaySearchConfig,
    *,
    timeout_sec: float,
    debug: bool = False,
    browser_like: bool = False,
) -> SearchOutcome:
    """Search Safeway products using the web pgmsearch endpoint."""
    prepared = prepare_request(
        session,
        query,
        config,
        browser_like=browser_like,
    )
    if debug:
        log_debug_request(prepared, config)

    try:
        response = session.send(prepared, timeout=timeout_sec)
    except Timeout as exc:
        logger.error(
            "timeout for q=%r after %.1fs: %s",
            query,
            timeout_sec,
            exc,
        )
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="timeout",
            request_url=prepared.url,
        )
    except RequestException as exc:
        logger.error("network failure for q=%r: %s", query, exc)
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="network",
            request_url=prepared.url,
        )

    status = response.status_code

    if status == 200:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            logger.warning(
                "200 for q=%r but response is not JSON (%d bytes)",
                query,
                len(response.content),
            )
            return SearchOutcome(
                query=query,
                status_code=status,
                ok=False,
                payload=None,
                error="invalid_json",
                request_url=prepared.url,
            )
        logger.info("200 success for q=%r — %s", query, _summarize_payload(payload))
        return SearchOutcome(
            query=query,
            status_code=status,
            ok=True,
            payload=payload,
            request_url=prepared.url,
        )

    if status in (401, 403):
        logger.warning(
            "%d auth/bot/session failure for q=%r — body preview: %s",
            status,
            query,
            (response.text or "")[:200],
        )
        return SearchOutcome(
            query=query,
            status_code=status,
            ok=False,
            payload=None,
            error="auth",
            request_url=prepared.url,
        )

    if status == 429:
        retry_after = response.headers.get("Retry-After", "unknown")
        logger.warning(
            "429 rate limited for q=%r — Retry-After: %s",
            query,
            retry_after,
        )
        return SearchOutcome(
            query=query,
            status_code=status,
            ok=False,
            payload=None,
            error="rate_limit",
            request_url=prepared.url,
        )

    logger.warning(
        "unexpected HTTP %d for q=%r — body preview: %s",
        status,
        query,
        (response.text or "")[:200],
    )
    return SearchOutcome(
        query=query,
        status_code=status,
        ok=False,
        payload=None,
        error=f"http_{status}",
        request_url=prepared.url,
    )
