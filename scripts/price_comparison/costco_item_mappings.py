"""Load canonical product → Costco item number mappings."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPPINGS_PATH = ROOT / "config" / "costco_item_mappings.csv"


@dataclass(frozen=True)
class CostcoItemMapping:
    canonical_id: str
    warehouse: str | None
    item_number: str
    notes: str | None = None


@lru_cache(maxsize=1)
def load_item_mappings() -> tuple[CostcoItemMapping, ...]:
    if not MAPPINGS_PATH.is_file():
        return ()
    rows: list[CostcoItemMapping] = []
    with MAPPINGS_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            canonical_id = (row.get("canonical_id") or "").strip()
            item_number = (row.get("item_number") or "").strip()
            if not canonical_id or not item_number:
                continue
            warehouse = (row.get("warehouse") or "").strip() or None
            notes = (row.get("notes") or "").strip() or None
            rows.append(
                CostcoItemMapping(
                    canonical_id=canonical_id,
                    warehouse=warehouse,
                    item_number=item_number,
                    notes=notes,
                ),
            )
    return tuple(rows)


def item_numbers_for_product(
    canonical_id: str,
    warehouse: str | None = None,
) -> list[str]:
    """Return item numbers for a canonical product, scoped to warehouse when set."""
    numbers: list[str] = []
    for mapping in load_item_mappings():
        if mapping.canonical_id != canonical_id:
            continue
        if mapping.warehouse is not None and warehouse is not None:
            if mapping.warehouse != warehouse:
                continue
        elif mapping.warehouse is not None and warehouse is None:
            continue
        if mapping.item_number not in numbers:
            numbers.append(mapping.item_number)
    return numbers


def resolve_item_number(
    canonical_id: str,
    warehouse: str,
) -> str | None:
    """Prefer warehouse-specific item numbers; return latest-available in catalog context."""
    nums = item_numbers_for_product(canonical_id, warehouse)
    if nums:
        return nums[0]
    global_nums = item_numbers_for_product(canonical_id, None)
    return global_nums[0] if global_nums else None


def all_item_numbers_for_product(canonical_id: str, warehouse: str) -> list[str]:
    """All mapped item numbers for history tracking (warehouse-specific + global)."""
    specific = item_numbers_for_product(canonical_id, warehouse)
    if specific:
        return specific
    return item_numbers_for_product(canonical_id, None)
