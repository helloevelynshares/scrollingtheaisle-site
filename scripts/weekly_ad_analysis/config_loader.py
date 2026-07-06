"""Weekly ad analysis — shared types and config loading."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"

CANONICAL_DISPLAY: dict[str, tuple[str, str, str]] = {
    "strawberries": ("Strawberries", "Produce", "berries"),
    "avocados": ("Hass Avocados", "Produce", "avocados"),
    "doritos_nacho_cheese": ("Doritos Nacho Cheese", "Snacks", "chips"),
    "cheetos_crunchy": ("Cheetos Crunchy", "Snacks", "chips"),
    "coke_zero": ("Coke Zero", "Drinks", "soda 12-packs"),
    "chobani_greek_yogurt": ("Chobani Greek Yogurt", "Dairy", "Greek yogurt tubs"),
    "cheerios": ("Cheerios", "Snacks", "cereal"),
    "tillamook_ice_cream": ("Tillamook Ice Cream", "Frozen", "ice cream"),
    "mission_tortilla_chips": ("Mission Tortilla Chips", "Snacks", "tortilla chips"),
    "nature_valley_bars": ("Nature Valley Bars", "Snacks", "snack bars"),
    "fage_greek_yogurt": ("Fage Greek Yogurt", "Dairy", "Greek yogurt tubs"),
    "frito_lay_multipack_chips": ("Frito-Lay Multipack Chips", "Snacks", "party chips"),
    "haagen_dazs_ice_cream": ("Häagen-Dazs Ice Cream", "Frozen", "ice cream"),
    "grapes": ("Grapes", "Produce", "grapes"),
    "eggs_18_count": ("Eggs, 18-count", "Protein", "eggs"),
    "oreos_sandwich_cookies": ("Oreos / Sandwich Cookies", "Snacks", "cookies"),
    "protein_bars": ("Protein Bars", "Snacks", "snack bars"),
    "kettle_brand_chips": ("Kettle Brand Chips", "Snacks", "chips"),
}

FAMILY_DISPLAY: dict[str, tuple[str, str, str]] = {
    "ben_jerrys_ice_cream": ("Ben & Jerry's Ice Cream", "Frozen", "ice cream"),
    "ritz_crackers_snacks": ("Ritz Crackers & Snacks", "Snacks", "crackers"),
}


@dataclass(frozen=True)
class MarketConfig:
    id: str
    display_name: str
    primary_grocer: str
    grocer_ad_label: str
    retailer_label: str
    costco_comparison_label: str
    output_content_label: str
    grocery_feed_id: str
    costco_region_id: str
    costco_region_slug: str
    ad_pdf_filename: str
    banner_filter: str
    default_input_folder_pattern: str
    default_output_folder_pattern: str


@dataclass(frozen=True)
class ContentWatchlistEntry:
    canonical_product_id: str | None
    canonical_category_id: str | None
    market: str
    include_in_weekly_ad_brief: bool
    content_priority: str
    shopper_popularity_score: int
    content_clarity_score: int
    default_content_angle: str
    track_costco_comp: bool
    track_historical_low: bool
    notes: str


def load_markets() -> dict[str, MarketConfig]:
    data = json.loads((CONFIG_DIR / "markets.json").read_text(encoding="utf-8"))
    markets: dict[str, MarketConfig] = {}
    for row in data["markets"]:
        markets[row["id"]] = MarketConfig(**row)
    return markets


def load_content_watchlist() -> list[ContentWatchlistEntry]:
    path = CONFIG_DIR / "content_watchlist_overrides.csv"
    entries: list[ContentWatchlistEntry] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            entries.append(
                ContentWatchlistEntry(
                    canonical_product_id=row["canonical_product_id"] or None,
                    canonical_category_id=row["canonical_category_id"] or None,
                    market=row["market"],
                    include_in_weekly_ad_brief=row["include_in_weekly_ad_brief"].lower() == "true",
                    content_priority=row["content_priority"],
                    shopper_popularity_score=int(row["shopper_popularity_score"]),
                    content_clarity_score=int(row["content_clarity_score"]),
                    default_content_angle=row["default_content_angle"],
                    track_costco_comp=row["track_costco_comp"].lower() == "true",
                    track_historical_low=row["track_historical_low"].lower() == "true",
                    notes=row.get("notes", ""),
                )
            )
    return entries


def eligible_watchlist(
    entries: list[ContentWatchlistEntry],
    market_id: str,
) -> list[ContentWatchlistEntry]:
    return [
        entry
        for entry in entries
        if entry.include_in_weekly_ad_brief
        and entry.market in {"all", market_id}
    ]
