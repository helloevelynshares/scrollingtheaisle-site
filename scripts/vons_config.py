"""Load Vons search credentials from environment (never commit scripts/.env)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


DEFAULT_VISITOR_ID = "7ca2d6cc-5fb9-4151-afe8-5d370681bca5"
DEFAULT_STORE_ID = "2053"
DEFAULT_ZIPCODE = "92110"
DEFAULT_CHANNEL = "instore"
DEFAULT_TIMEOUT_SEC = 45.0
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3.1 Safari/605.1.15"
)


@dataclass(frozen=True)
class VonsSearchConfig:
    subscription_key: str
    user_agent: str
    visitor_id: str
    store_id: str
    zipcode: str
    channel: str
    uuid: str | None = None
    cookie: str | None = None
    sec_ch_ua: str | None = None
    sec_ch_ua_platform: str | None = None
    sec_ch_ua_mobile: str | None = None
    extra_headers: dict[str, str] | None = None

    def missing_fields(self) -> list[str]:
        required = {
            "SAFEWAY_SUBSCRIPTION_KEY or VONS_SUBSCRIPTION_KEY": self.subscription_key,
            "VONS_USER_AGENT or SAFEWAY_USER_AGENT": self.user_agent,
            "VONS_VISITOR_ID": self.visitor_id,
        }
        return [name for name, value in required.items() if not value.strip()]

    @classmethod
    def from_env(cls) -> VonsSearchConfig:
        """Load from scripts/.env; raises ValueError if cookie or required fields missing."""
        from pathlib import Path

        from dotenv import load_dotenv

        env_path = Path(__file__).resolve().parent / ".env"
        load_dotenv(env_path)
        config = load_config()
        if not config.cookie:
            raise ValueError(
                "Set VONS_COOKIE in scripts/.env from vons.com DevTools → Network → pgmsearch "
                "(Safeway cookies are not interchangeable)"
            )
        missing = config.missing_fields()
        if missing:
            raise ValueError("Missing Vons pgmsearch credentials: " + ", ".join(missing))
        return config


def parse_extra_headers(raw: str | None) -> dict[str, str]:
    if not raw or not raw.strip():
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("VONS_EXTRA_HEADERS must be a JSON object")
    return {str(k): str(v) for k, v in parsed.items()}


def _optional_env(name: str) -> str | None:
    value = (os.getenv(name) or "").strip()
    return value or None


def load_timeout_seconds() -> float:
    """VONS_TIMEOUT_SECONDS (preferred), else Safeway timeout env vars, else 45s."""
    raw = os.getenv("VONS_TIMEOUT_SECONDS")
    if raw and raw.strip():
        return float(raw.strip())
    for key in ("SAFEWAY_TIMEOUT_SECONDS", "SAFEWAY_TIMEOUT_SEC"):
        raw = os.getenv(key)
        if raw and raw.strip():
            return float(raw.strip())
    return DEFAULT_TIMEOUT_SEC


def _cookie_value(cookie_header: str, name: str) -> str | None:
    prefix = name + "="
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith(prefix):
            return part[len(prefix) :]
    return None


def _visitor_uuid_from_cookie(cookie_header: str) -> tuple[str | None, str | None]:
    visitor = _cookie_value(cookie_header, "absVisitorId")
    uuid: str | None = None
    raw_pii = _cookie_value(cookie_header, "SWY_SHARED_PII_SESSION_INFO")
    if raw_pii:
        try:
            from urllib.parse import unquote

            payload = json.loads(unquote(raw_pii))
            uuid = str(payload.get("uuid") or "") or None
        except (json.JSONDecodeError, TypeError, ValueError):
            uuid = None
    return visitor, uuid


def load_config() -> VonsSearchConfig:
    subscription_key = (
        (os.getenv("VONS_SUBSCRIPTION_KEY") or "").strip()
        or (os.getenv("SAFEWAY_SUBSCRIPTION_KEY") or "").strip()
    )
    cookie = _optional_env("VONS_COOKIE")

    visitor_id = (os.getenv("VONS_VISITOR_ID") or "").strip()
    uuid_raw = (os.getenv("VONS_UUID") or "").strip()
    uuid = uuid_raw or None
    if cookie and not visitor_id:
        from_cookie_visitor, from_cookie_uuid = _visitor_uuid_from_cookie(cookie)
        if from_cookie_visitor:
            visitor_id = from_cookie_visitor
        if not uuid and from_cookie_uuid:
            uuid = from_cookie_uuid

    user_agent = (
        (os.getenv("VONS_USER_AGENT") or "").strip()
        or (os.getenv("SAFEWAY_USER_AGENT") or "").strip()
        or DEFAULT_USER_AGENT
    )

    return VonsSearchConfig(
        subscription_key=subscription_key,
        user_agent=user_agent,
        visitor_id=visitor_id or DEFAULT_VISITOR_ID,
        uuid=uuid,
        store_id=(os.getenv("VONS_STORE_ID") or DEFAULT_STORE_ID).strip(),
        zipcode=(os.getenv("VONS_ZIPCODE") or DEFAULT_ZIPCODE).strip(),
        channel=(os.getenv("VONS_CHANNEL") or DEFAULT_CHANNEL).strip(),
        cookie=cookie,
        sec_ch_ua=_optional_env("SAFEWAY_SEC_CH_UA"),
        sec_ch_ua_platform=_optional_env("SAFEWAY_SEC_CH_UA_PLATFORM"),
        sec_ch_ua_mobile=_optional_env("SAFEWAY_SEC_CH_UA_MOBILE"),
        extra_headers=parse_extra_headers(os.getenv("VONS_EXTRA_HEADERS")) or None,
    )
