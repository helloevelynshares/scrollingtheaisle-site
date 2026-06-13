"""Vons (Albertsons SoCal) pgmsearch client."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any

import requests
from requests.exceptions import RequestException, Timeout

from safeway_client import SearchOutcome
from vons_config import VonsSearchConfig, load_config

VONS_BASE_QUERY_PARAMS: dict[str, str] = {
    "url": "https://www.vons.com",
    "pageurl": "https://www.vons.com",
    "pagename": "search",
    "rows": "30",
    "start": "0",
    "search-type": "keyword",
    "featured": "true",
    "sort": "",
    "timezone": "America/Los_Angeles",
    "dvid": "web-4.1search",
    "wineshopstoreid": "5799",
    "pgm": "wineshop,merch-banner",
    "includeOffer": "true",
    "banner": "vons",
}

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"

VONS_SEARCH_URL = "https://www.vons.com/abs/pub/xapi/pgmsearch/v1/search/products"


def generate_vons_request_id() -> str:
    """Browser-style request-id: 628 + epoch-ms + 3-digit suffix (19 digits total)."""
    ms = str(int(time.time() * 1000))
    suffix = str(time.time_ns() % 1000).zfill(3)
    return f"628{ms}{suffix}"


def _build_pgmsearch_query_string(params: dict[str, str]) -> str:
    """Build query string keeping commas in pgm= unencoded (matches Safari DevTools)."""
    from urllib.parse import quote

    parts: list[str] = []
    for key, value in params.items():
        if key == "pgm":
            parts.append(f"{quote(key, safe='')}={value}")
        else:
            parts.append(f"{quote(key, safe='')}={quote(value, safe='')}")
    return "&".join(parts)


def build_vons_search_params(query: str, config: VonsSearchConfig) -> dict[str, str]:
    params = dict(VONS_BASE_QUERY_PARAMS)
    params["request-id"] = generate_vons_request_id()
    params["storeid"] = config.store_id
    params["featured"] = "true"
    params["q"] = query
    params["channel"] = config.channel
    params["zipcode"] = config.zipcode
    params["visitorId"] = config.visitor_id
    if config.uuid:
        params["uuid"] = config.uuid
    return params


def build_vons_headers(query: str, config: VonsSearchConfig) -> dict[str, str]:
    headers: dict[str, str] = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "ocp-apim-subscription-key": config.subscription_key,
        "priority": "u=3, i",
        "referer": (
            f"https://www.vons.com/shop/search-results.html"
            f"?q={requests.utils.quote(query)}&tab=products"
        ),
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": config.user_agent,
    }
    if config.extra_headers:
        headers.update(config.extra_headers)
    if config.cookie:
        headers["Cookie"] = config.cookie
    return headers


def _search_via_curl(
    query: str,
    *,
    timeout_sec: float,
    config: VonsSearchConfig,
) -> SearchOutcome:
    """Use system curl — matches working Safari DevTools captures; requests often times out."""
    url = build_pgmsearch_url(query, config)
    headers = build_vons_headers(query, config)
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
        completed = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
        )
    except OSError:
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="curl_unavailable",
            request_url=url,
        )

    if completed.returncode == 28:
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="timeout",
            request_url=url,
        )
    if completed.returncode != 0:
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error=f"curl_{completed.returncode}",
            request_url=url,
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

    if status_code != 200:
        return SearchOutcome(
            query=query,
            status_code=status_code,
            ok=False,
            payload=None,
            error=f"http_{status_code}" if status_code else "http_error",
            request_url=url,
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return SearchOutcome(
            query=query,
            status_code=200,
            ok=False,
            payload=None,
            error="invalid_json",
            request_url=url,
        )

    return SearchOutcome(
        query=query,
        status_code=200,
        ok=True,
        payload=payload,
        request_url=url,
    )


def _search_via_requests(
    query: str,
    *,
    timeout_sec: float,
    config: VonsSearchConfig,
) -> SearchOutcome:
    """Fallback when curl is unavailable."""
    url = build_pgmsearch_url(query, config)
    headers = build_vons_headers(query, config)
    session = requests.Session()
    try:
        response = session.get(
            url,
            headers=headers,
            timeout=timeout_sec,
        )
    except Timeout:
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="timeout",
            request_url=VONS_SEARCH_URL,
        )
    except RequestException as exc:
        return SearchOutcome(
            query=query,
            status_code=None,
            ok=False,
            payload=None,
            error="network",
            request_url=str(exc),
        )

    if response.status_code != 200:
        return SearchOutcome(
            query=query,
            status_code=response.status_code,
            ok=False,
            payload=None,
            error=f"http_{response.status_code}",
            request_url=response.url,
        )

    try:
        payload = response.json()
    except json.JSONDecodeError:
        return SearchOutcome(
            query=query,
            status_code=200,
            ok=False,
            payload=None,
            error="invalid_json",
            request_url=response.url,
        )

    return SearchOutcome(
        query=query,
        status_code=200,
        ok=True,
        payload=payload,
        request_url=response.url,
    )


def search_vons_product(
    query: str,
    *,
    timeout_sec: float = 30.0,
    config: VonsSearchConfig | None = None,
) -> SearchOutcome:
    """Direct HTTP pgmsearch for Vons (curl transport; requests fallback if curl missing)."""
    cfg = config or VonsSearchConfig.from_env()
    outcome = _search_via_curl(query, timeout_sec=timeout_sec, config=cfg)
    if outcome.ok or outcome.error != "curl_unavailable":
        return outcome
    return _search_via_requests(query, timeout_sec=min(timeout_sec, 10.0), config=cfg)


def outcome_to_record(outcome: SearchOutcome, *, source: str) -> dict[str, Any]:
    return {
        "query": outcome.query,
        "ok": outcome.ok,
        "status_code": outcome.status_code,
        "url": outcome.request_url,
        "error": outcome.error,
        "response": outcome.payload,
        "capture_source": source,
    }


def build_pgmsearch_url(query: str, config: VonsSearchConfig | None = None) -> str:
    cfg = config or VonsSearchConfig.from_env()
    params = build_vons_search_params(query, cfg)
    return f"{VONS_SEARCH_URL}?{_build_pgmsearch_query_string(params)}"


IN_BROWSER_FETCH_JS = """
async ({ url, subscriptionKey }) => {
  const headers = { accept: "application/json, text/plain, */*" };
  if (subscriptionKey) {
    headers["ocp-apim-subscription-key"] = subscriptionKey;
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 45000);
  try {
    const response = await fetch(url, {
      credentials: "include",
      headers,
      signal: controller.signal,
    });
    const text = await response.text();
    let payload = null;
    try {
      payload = text ? JSON.parse(text) : null;
    } catch (_) {
      return { status: response.status, error: "invalid_json", preview: text.slice(0, 200) };
    }
    return { status: response.status, payload };
  } catch (error) {
    return { status: null, error: String(error) };
  } finally {
    clearTimeout(timer);
  }
}
"""
