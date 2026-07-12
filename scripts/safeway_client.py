"""Safeway web product search client (pgmsearch API)."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

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
    "featured": "true",
    "sort": "",
    "timezone": "America/Los_Angeles",
    "dvid": "web-4.1search",
    "pp": "true",
    "wineshopstoreid": "5799",
    "pgm": "wineshop,merch-banner",
    "includeOffer": "true",
    "banner": "safeway",
}

BROWSER_LIKE_ACCEPT_LANGUAGE = "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
DEFAULT_ACCEPT_LANGUAGE = "en-US,en;q=0.9"

SENSITIVE_HEADER_NAMES = frozenset({"cookie", "ocp-apim-subscription-key"})
SENSITIVE_QUERY_KEYS = frozenset({"visitorid", "uuid"})

logger = logging.getLogger(__name__)


DEFAULT_TIMEOUT_SEC = 30.0

PGMSEARCH_COOKIE_HINT = (
    "refresh SAFEWAY_COOKIE in scripts/.env from Chrome DevTools → Network → "
    "pgmsearch on safeway.com"
)


def timeout_message(timeout_sec: float, *, query: str | None = None) -> str:
    q = f" for q={query!r}" if query else ""
    return (
        f"Safeway pgmsearch timed out after {timeout_sec:g}s{q}: {PGMSEARCH_COOKIE_HINT}"
    )


def auth_message(status_code: int, *, query: str | None = None) -> str:
    q = f" for q={query!r}" if query else ""
    return (
        f"Safeway pgmsearch returned HTTP {status_code}{q} (session/auth): "
        f"{PGMSEARCH_COOKIE_HINT}"
    )


def empty_response_message(*, query: str | None = None) -> str:
    q = f" for q={query!r}" if query else ""
    return f"Safeway pgmsearch returned HTTP 200 with an empty body{q}"


def stuck_loading_message(api_timeout_sec: float, *, query: str | None = None) -> str:
    q = f" for q={query!r}" if query else ""
    return (
        f"Safeway search stuck loading, no pgmsearch response after {api_timeout_sec:g}s{q}: "
        f"{PGMSEARCH_COOKIE_HINT}, or run --headful to sign in and set store"
    )


@dataclass(frozen=True)
class SearchOutcome:
    query: str
    status_code: int | None
    ok: bool
    payload: dict[str, Any] | list[Any] | None
    error: str | None = None
    request_url: str | None = None
    message: str | None = None


def generate_request_id() -> str:
    """Browser-style request-id: 628 + epoch-ms + 3-digit suffix (19 digits total)."""
    ms = str(int(time.time() * 1000))
    suffix = str(time.time_ns() % 1000).zfill(3)
    return f"628{ms}{suffix}"


def _build_pgmsearch_query_string(params: dict[str, str]) -> str:
    """Build query string keeping commas in pgm= unencoded (matches Chrome DevTools)."""
    parts: list[str] = []
    for key, value in params.items():
        if key == "pgm":
            parts.append(f"{quote(key, safe='')}={value}")
        else:
            parts.append(f"{quote(key, safe='')}={quote(value, safe='')}")
    return "&".join(parts)


def build_pgmsearch_url(query: str, config: SafewaySearchConfig) -> str:
    params = build_search_params(query, config)
    return f"{SEARCH_URL}?{_build_pgmsearch_query_string(params)}"


def build_search_params(query: str, config: SafewaySearchConfig) -> dict[str, str]:
    params = dict(BASE_QUERY_PARAMS)
    params["request-id"] = generate_request_id()
    params["q"] = query
    params["visitorId"] = config.visitor_id
    if config.uuid:
        params["uuid"] = config.uuid
    params["storeid"] = config.store_id
    params["zipcode"] = config.zipcode
    params["channel"] = config.channel
    return params


def _apply_sec_ch_headers(headers: dict[str, str], config: SafewaySearchConfig) -> None:
    """Only send sec-ch-ua* when configured, avoids conflicting with user-agent."""
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
    """Search Safeway products using the web pgmsearch endpoint (curl transport)."""
    outcome = _search_via_curl(
        query,
        config=config,
        timeout_sec=timeout_sec,
        browser_like=browser_like,
    )
    if outcome.ok or outcome.error != "curl_unavailable":
        if debug and outcome.request_url:
            print(f"URL: {redact_url(outcome.request_url)}", flush=True)
        return outcome
    return _search_via_requests(
        session,
        query,
        config,
        timeout_sec=min(timeout_sec, 10.0),
        debug=debug,
        browser_like=browser_like,
    )


def _search_via_curl(
    query: str,
    *,
    config: SafewaySearchConfig,
    timeout_sec: float,
    browser_like: bool,
) -> SearchOutcome:
    """Use system curl, matches working Chrome DevTools captures; requests often times out."""
    url = build_pgmsearch_url(query, config)
    headers = build_headers(query, config, browser_like=browser_like)
    cmd = [
        "curl",
        "-sS",
        "--compressed",
        "-w",
        "\n__HTTP_CODE__:%{http_code}",
        "--max-time",
        str(max(1, int(timeout_sec))),
        url,
    ]
    for name, value in headers.items():
        cmd.extend(["-H", f"{name}: {value}"])

    try:
        completed = subprocess.run(cmd, capture_output=True, check=False)
    except OSError as exc:
        msg = f"Safeway pgmsearch curl unavailable for q={query!r}: {exc}"
        logger.error("%s", msg)
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="curl_unavailable",
            request_url=url,
            message=msg,
        )

    if completed.returncode == 28:
        msg = timeout_message(timeout_sec, query=query)
        logger.error("%s (curl exit 28)", msg)
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="timeout",
            request_url=url,
            message=msg,
        )
    if completed.returncode != 0:
        stderr = (completed.stderr or b"").decode("utf-8", errors="replace").strip()
        msg = (
            f"Safeway pgmsearch curl failed for q={query!r} (exit {completed.returncode})"
            + (f": {stderr[:200]}" if stderr else "")
        )
        logger.error("%s", msg)
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error=f"curl_{completed.returncode}",
            request_url=url,
            message=msg,
        )

    raw = completed.stdout
    marker = b"\n__HTTP_CODE__:"
    if marker in raw:
        body, _, code_bytes = raw.rpartition(marker)
        try:
            status_code = int(code_bytes.decode("ascii", errors="ignore").strip())
        except ValueError:
            status_code = None
    else:
        body = raw
        status_code = None

    if status_code in (401, 403):
        msg = auth_message(status_code, query=query)
        logger.warning("%s", msg)
        return SearchOutcome(
            query=query,
            status_code=status_code,
            ok=False,
            payload=None,
            error="auth",
            request_url=url,
            message=msg,
        )
    if status_code is not None and status_code != 200:
        preview = body[:200].decode("utf-8", errors="replace")
        msg = f"Safeway pgmsearch returned HTTP {status_code} for q={query!r}"
        logger.warning("%s, body preview: %s", msg, preview)
        return SearchOutcome(
            query=query,
            status_code=status_code,
            ok=False,
            payload=None,
            error=f"http_{status_code}",
            request_url=url,
            message=msg,
        )
    if not body.strip():
        msg = empty_response_message(query=query)
        logger.warning("%s", msg)
        return SearchOutcome(
            query=query,
            status_code=status_code or 200,
            ok=False,
            payload=None,
            error="empty_response",
            request_url=url,
            message=msg,
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        msg = (
            f"Safeway pgmsearch returned HTTP 200 but invalid JSON for q={query!r} "
            f"({len(body)} bytes)"
        )
        logger.warning("%s", msg)
        return SearchOutcome(
            query=query,
            status_code=200,
            ok=False,
            payload=None,
            error="invalid_json",
            request_url=url,
            message=msg,
        )

    logger.info("200 success for q=%r via curl: %s", query, _summarize_payload(payload))
    return SearchOutcome(
        query=query,
        status_code=200,
        ok=True,
        payload=payload,
        request_url=url,
    )


def _search_via_requests(
    session: requests.Session,
    query: str,
    config: SafewaySearchConfig,
    *,
    timeout_sec: float,
    debug: bool = False,
    browser_like: bool = False,
) -> SearchOutcome:
    """Fallback when curl is unavailable."""
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
        msg = timeout_message(timeout_sec, query=query)
        logger.error("%s (%s)", msg, exc)
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="timeout",
            request_url=prepared.url,
            message=msg,
        )
    except RequestException as exc:
        msg = f"Safeway pgmsearch network error for q={query!r}: {exc}"
        logger.error("%s", msg)
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="network",
            request_url=prepared.url,
            message=msg,
        )

    status = response.status_code

    if status == 200:
        try:
            payload = response.json()
        except json.JSONDecodeError:
            body_len = len(response.content)
            if body_len == 0:
                msg = empty_response_message(query=query)
                err = "empty_response"
            else:
                msg = (
                    f"Safeway pgmsearch returned HTTP 200 but invalid JSON for q={query!r} "
                    f"({body_len} bytes)"
                )
                err = "invalid_json"
            logger.warning("%s", msg)
            return SearchOutcome(
                query=query,
                status_code=status,
                ok=False,
                payload=None,
                error=err,
                request_url=prepared.url,
                message=msg,
            )
        logger.info("200 success for q=%r: %s", query, _summarize_payload(payload))
        return SearchOutcome(
            query=query,
            status_code=status,
            ok=True,
            payload=payload,
            request_url=prepared.url,
        )

    if status in (401, 403):
        msg = auth_message(status, query=query)
        logger.warning(
            "%s, body preview: %s",
            msg,
            (response.text or "")[:200],
        )
        return SearchOutcome(
            query=query,
            status_code=status,
            ok=False,
            payload=None,
            error="auth",
            request_url=prepared.url,
            message=msg,
        )

    if status == 429:
        retry_after = response.headers.get("Retry-After", "unknown")
        logger.warning(
            "429 rate limited for q=%r: Retry-After: %s",
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
        "unexpected HTTP %d for q=%r, body preview: %s",
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
