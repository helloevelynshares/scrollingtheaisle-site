"""Centralized Costco warehouse mapping, single source for Python pipeline."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "costco_warehouse_mapping.json"


@lru_cache(maxsize=1)
def load_mapping_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def costco_warehouses() -> tuple[str, ...]:
    return tuple(load_mapping_config()["warehouses"])


def normalize_warehouse_slug(filename_slug: str) -> str | None:
    """Map filename region slug (e.g. san-francisco) to canonical warehouse key."""
    return load_mapping_config()["filename_slug_to_warehouse"].get(filename_slug)


def grocery_tracker_to_warehouse(grocery_tracker: str) -> str | None:
    return load_mapping_config()["grocery_tracker_to_warehouse"].get(grocery_tracker)


def feed_id_to_warehouse(feed_id: str) -> str | None:
    return load_mapping_config()["feed_id_to_warehouse"].get(feed_id)


def warehouse_label(warehouse: str) -> str:
    labels = load_mapping_config()["warehouse_labels"]
    return labels.get(warehouse, warehouse.replace("_", " ").title())


def warehouse_for_grocery_feed(feed_id: str) -> str | None:
    """Return paired Costco warehouse for a grocery feed, never cross-fallback."""
    return feed_id_to_warehouse(feed_id)


GROCERY_TRACKER_TO_COSTCO_REGION = load_mapping_config()["grocery_tracker_to_warehouse"]
COSTCO_REGIONS = costco_warehouses()
