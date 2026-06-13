"""Playwright session helpers — inject Albertsons-family cookies from scripts/.env."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"

logger = logging.getLogger("playwright_session")

BANNER_COOKIE = "ACI_S_ECommBanner"


def parse_cookie_header(cookie_header: str, domain: str) -> list[dict[str, str]]:
    """Parse a browser Cookie request header into Playwright cookie dicts."""
    cookies: list[dict[str, str]] = []
    for part in cookie_header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, _, value = part.partition("=")
        name = name.strip()
        if not name:
            continue
        cookies.append(
            {
                "name": name,
                "value": value.strip(),
                "domain": domain,
                "path": "/",
            }
        )
    return cookies


def load_env_cookie_string(env_name: str, *, fallback_env: str | None = None) -> str | None:
    load_dotenv(ENV_PATH)
    raw = (os.getenv(env_name) or "").strip()
    if raw:
        return raw
    if fallback_env:
        return (os.getenv(fallback_env) or "").strip() or None
    return None


def cookie_banner_value(cookie_header: str) -> str | None:
    prefix = BANNER_COOKIE + "="
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith(prefix):
            return part[len(prefix) :].strip().lower()
    return None


def validate_cookie_for_store(cookie_header: str, store: Any) -> list[str]:
    """Return human-readable warnings when a cookie looks wrong for this store."""
    warnings: list[str] = []
    banner = cookie_banner_value(cookie_header)
    expected = store.banner.lower()
    if banner and banner != expected:
        warnings.append(
            f"Cookie banner is {banner!r} but {store.host} expects {expected!r} — "
            f"copy Cookie from DevTools on {store.host}, not another Albertsons site."
        )
    if expected == "vons" and "visid_incap_1610353" in cookie_header:
        warnings.append(
            "Cookie looks like safeway.com (visid_incap_1610353) — set VONS_COOKIE from vons.com pgmsearch."
        )
    if expected == "safeway" and "visid_incap_1610354" in cookie_header:
        warnings.append(
            "Cookie looks like vons.com (visid_incap_1610354) — set SAFEWAY_COOKIE from safeway.com pgmsearch."
        )
    if not banner and store.key == "vons":
        warnings.append(
            f"Cookie missing {BANNER_COOKIE} — paste a fresh Cookie header from {store.host} pgmsearch."
        )
    return warnings


def resolve_store_cookie_header(store: Any) -> tuple[str | None, str | None]:
    """Return (cookie_header, source_env_name). Vons does not silently reuse Safeway cookies."""
    primary = load_env_cookie_string(store.cookie_env)
    if primary:
        return primary, store.cookie_env
    if store.key == "vons":
        return None, None
    fallback = load_env_cookie_string("SAFEWAY_COOKIE")
    if fallback:
        return fallback, "SAFEWAY_COOKIE"
    return None, None


def wait_for_enter(prompt: str) -> None:
    if not sys.stdin.isatty():
        logger.warning(
            "%s (non-interactive terminal — continuing after 15s; use --headful in a real terminal)",
            prompt,
        )
        import time

        time.sleep(15)
        return
    try:
        input(prompt)
    except EOFError:
        logger.warning("No stdin — continuing without pause")


def pause_for_manual_setup(store: Any, *, manual_session: bool) -> None:
    if manual_session:
        logger.info(
            "Manual session on %s: sign in, set store/zip, dismiss modals. "
            "Session persists under %s",
            store.host,
            store.profile_dir,
        )
        wait_for_enter("Press Enter when store is set and homepage looks ready … ")
        return
    logger.info(
        "Headful setup: confirm store/zip on %s if prompted, then press Enter to continue.",
        store.host,
    )
    wait_for_enter("Press Enter when store is set (or homepage is ready) … ")


def apply_store_cookies_to_context(
    context: Any,
    page: Any,
    *,
    store: Any,
    use_env_cookies: bool = True,
    reload_after: bool = True,
) -> int:
    """
    Load store cookie from scripts/.env into the Playwright browser context.

    Vons uses VONS_COOKIE only (no Safeway fallback). Safeway uses SAFEWAY_COOKIE.
    """
    if not use_env_cookies:
        return 0

    cookie_header, source_env = resolve_store_cookie_header(store)
    if not cookie_header:
        logger.warning(
            "No %s in scripts/.env — search may hang on infinite loading. "
            "Paste Cookie from Chrome DevTools → Network → pgmsearch on %s.",
            store.cookie_env,
            store.host,
        )
        return 0

    for warning in validate_cookie_for_store(cookie_header, store):
        logger.warning(warning)
    if source_env and source_env != store.cookie_env:
        logger.warning(
            "Using %s because %s is unset — prefer a store-specific cookie.",
            source_env,
            store.cookie_env,
        )

    cookies = parse_cookie_header(cookie_header, domain=store.cookie_domain)
    if not cookies:
        return 0

    logger.info(
        "Applying %d cookie(s) from scripts/.env (%s) for %s (values not logged)",
        len(cookies),
        source_env or store.cookie_env,
        store.host,
    )
    context.add_cookies(cookies)
    if reload_after:
        page.reload(wait_until="commit", timeout=60_000)
    return len(cookies)


def prepare_store_session(
    context: Any,
    page: Any,
    *,
    store: Any,
    headful: bool,
    use_env_cookies: bool = True,
    manual_session: bool = False,
    pause_before_search: bool = False,
    inject_cookies_first: bool = False,
) -> int:
    """
    Open the store homepage and optionally inject Imperva/session cookies.

    Headful default: load homepage with profile cookies only, let the user set
    store/zip, then inject VONS_COOKIE/SAFEWAY_COOKIE and reload. Use
    --inject-cookies-first to restore the old inject-before-store behavior.
    """
    manual_session = manual_session or not use_env_cookies

    if manual_session:
        logger.info("Opening %s for manual login (no .env cookie injection)", store.host)
        page.goto(store.origin(), wait_until="commit", timeout=60_000)
        pause_for_manual_setup(store, manual_session=True)
        return 0

    page.goto(store.origin(), wait_until="commit", timeout=60_000)

    if headful and not inject_cookies_first:
        pause_for_manual_setup(store, manual_session=False)

    cookie_count = apply_store_cookies_to_context(
        context,
        page,
        store=store,
        use_env_cookies=use_env_cookies,
        reload_after=True,
    )

    if pause_before_search and headful:
        wait_for_enter("Press Enter to start search capture … ")

    return cookie_count


def reset_playwright_profile(profile_dir: Path) -> None:
    if profile_dir.is_dir():
        logger.info("Removing Playwright profile at %s", profile_dir)
        shutil.rmtree(profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)


def load_env_cookie_string_legacy() -> str | None:
    return load_env_cookie_string("SAFEWAY_COOKIE")


def apply_env_cookies_to_context(
    context: Any,
    page: Any,
    *,
    use_env_cookies: bool = True,
) -> int:
    """Safeway wrapper — kept for existing seed scripts."""
    from albertsons_store import SAFEWAY_BAY_AREA

    return apply_store_cookies_to_context(
        context,
        page,
        store=SAFEWAY_BAY_AREA,
        use_env_cookies=use_env_cookies,
    )
