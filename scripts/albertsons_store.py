"""Albertsons-family store configs (Safeway, Vons, etc.) for pgmsearch Playwright seeding."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

SCRIPT_DIR = Path(__file__).resolve().parent

SEARCH_API_PATH = "/abs/pub/xapi/pgmsearch/v1/search/products"


@dataclass(frozen=True)
class AlbertsonsStore:
    key: str
    host: str
    banner: str
    cookie_env: str
    profile_dir: Path
    cookie_domain: str
    region_label: str

    def origin(self) -> str:
        return f"https://{self.host}"

    def search_page_url(self, query: str) -> str:
        return (
            f"{self.origin()}/shop/search-results.html"
            f"?q={quote(query)}&tab=products"
        )


VONS_SOCAL = AlbertsonsStore(
    key="vons",
    host="www.vons.com",
    banner="vons",
    cookie_env="VONS_COOKIE",
    profile_dir=SCRIPT_DIR / ".playwright-profile-vons",
    cookie_domain=".vons.com",
    region_label="SoCal",
)

SAFEWAY_BAY_AREA = AlbertsonsStore(
    key="safeway",
    host="www.safeway.com",
    banner="safeway",
    cookie_env="SAFEWAY_COOKIE",
    profile_dir=SCRIPT_DIR / ".playwright-profile",
    cookie_domain=".safeway.com",
    region_label="Bay Area",
)

STORES: dict[str, AlbertsonsStore] = {
    VONS_SOCAL.key: VONS_SOCAL,
    SAFEWAY_BAY_AREA.key: SAFEWAY_BAY_AREA,
}
