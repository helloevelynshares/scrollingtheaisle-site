"""Load Safeway search credentials from environment (never commit scripts/.env)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


DEFAULT_STORE_ID = "4601"
DEFAULT_ZIPCODE = "94111"
DEFAULT_CHANNEL = "pickup"


@dataclass(frozen=True)
class SafewaySearchConfig:
    subscription_key: str
    user_agent: str
    visitor_id: str
    uuid: str
    store_id: str
    zipcode: str
    channel: str
    cookie: str | None = None
    sec_ch_ua: str | None = None
    sec_ch_ua_platform: str | None = None
    sec_ch_ua_mobile: str | None = None
    extra_headers: dict[str, str] | None = None

    def missing_fields(self) -> list[str]:
        required = {
            "SAFEWAY_SUBSCRIPTION_KEY": self.subscription_key,
            "SAFEWAY_USER_AGENT": self.user_agent,
        }
        return [name for name, value in required.items() if not value.strip()]


def parse_extra_headers(raw: str | None) -> dict[str, str]:
    if not raw or not raw.strip():
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("SAFEWAY_EXTRA_HEADERS must be a JSON object")
    return {str(k): str(v) for k, v in parsed.items()}


def _optional_env(name: str) -> str | None:
    value = (os.getenv(name) or "").strip()
    return value or None


DEFAULT_TIMEOUT_SEC = 30.0


def load_timeout_seconds() -> float:
    """SAFEWAY_TIMEOUT_SECONDS (preferred) or legacy SAFEWAY_TIMEOUT_SEC."""
    for key in ("SAFEWAY_TIMEOUT_SECONDS", "SAFEWAY_TIMEOUT_SEC"):
        raw = os.getenv(key)
        if raw and raw.strip():
            return float(raw.strip())
    return DEFAULT_TIMEOUT_SEC


def load_config() -> SafewaySearchConfig:
    return SafewaySearchConfig(
        subscription_key=os.getenv("SAFEWAY_SUBSCRIPTION_KEY", "").strip(),
        user_agent=os.getenv("SAFEWAY_USER_AGENT", "").strip(),
        visitor_id=os.getenv("SAFEWAY_VISITOR_ID", "").strip(),
        uuid=os.getenv("SAFEWAY_UUID", "").strip(),
        store_id=(os.getenv("SAFEWAY_STORE_ID") or DEFAULT_STORE_ID).strip(),
        zipcode=(os.getenv("SAFEWAY_ZIPCODE") or DEFAULT_ZIPCODE).strip(),
        channel=(os.getenv("SAFEWAY_CHANNEL") or DEFAULT_CHANNEL).strip(),
        cookie=_optional_env("SAFEWAY_COOKIE"),
        sec_ch_ua=_optional_env("SAFEWAY_SEC_CH_UA"),
        sec_ch_ua_platform=_optional_env("SAFEWAY_SEC_CH_UA_PLATFORM"),
        sec_ch_ua_mobile=_optional_env("SAFEWAY_SEC_CH_UA_MOBILE"),
        extra_headers=parse_extra_headers(os.getenv("SAFEWAY_EXTRA_HEADERS")) or None,
    )
