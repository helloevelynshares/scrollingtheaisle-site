"""Load and match Costco warehouse CSV data."""

from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .canonical_metadata import CANONICAL_PACKAGES, CanonicalPackageMeta, DEFAULT_COSTCO_DATA_ROOT
from .unit_normalize import ParsedPackage, parse_item_sign


@dataclass(frozen=True)
class CostcoItem:
    item_number: str
    item_sign: str
    sell_price: float
    timestamp: str
    source_file: str
    parsed: ParsedPackage | None


def costco_data_root() -> Path:
    return Path(os.environ.get("COSTCO_DATA_ROOT", DEFAULT_COSTCO_DATA_ROOT))


def load_location_catalog(location_slug: str, data_root: Path | None = None) -> list[CostcoItem]:
    root = data_root or costco_data_root()
    if not root.is_dir():
        raise FileNotFoundError(f"Costco data directory not found: {root}")

    pattern = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}}_{re.escape(location_slug)}_.*\.csv$")
    files = sorted(
        [p for p in root.iterdir() if p.is_file() and pattern.match(p.name)],
        key=lambda p: p.name,
    )
    if not files:
        raise FileNotFoundError(f"No Costco CSV files for location '{location_slug}' in {root}")

    by_item: dict[str, CostcoItem] = {}
    for path in files:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                item_number = (row.get("itemNumber") or "").strip()
                if not item_number:
                    continue
                try:
                    price = float(row.get("sellPrice") or 0)
                except ValueError:
                    continue
                if price <= 0:
                    continue
                ts = row.get("timestamp") or path.name[:10]
                item = CostcoItem(
                    item_number=item_number,
                    item_sign=(row.get("itemSign") or "").strip(),
                    sell_price=price,
                    timestamp=ts,
                    source_file=path.name,
                    parsed=None,
                )
                existing = by_item.get(item_number)
                if existing is None or _ts_key(ts) >= _ts_key(existing.timestamp):
                    by_item[item_number] = item

    return list(by_item.values())


def _ts_key(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def _score_match(text: str, meta: CanonicalPackageMeta) -> int:
    lower = text.lower()
    if any(re.search(p, lower) for p in meta.costco_exclude):
        return -1
    if not any(re.search(p, lower) for p in meta.costco_include):
        return 0
    score = 10
    for idx, pref in enumerate(meta.costco_prefer):
        if re.search(pref, lower):
            score += (len(meta.costco_prefer) - idx) * 5
    return score


def match_costco_item(
    canonical_id: str,
    catalog: list[CostcoItem],
) -> tuple[CostcoItem | None, str | None]:
    meta = CANONICAL_PACKAGES.get(canonical_id)
    if meta is None:
        return None, "Unknown canonical product"

    candidates: list[tuple[int, CostcoItem]] = []
    for item in catalog:
        score = _score_match(item.item_sign, meta)
        if score > 0:
            parsed = parse_item_sign(item.item_sign, meta.comparable_unit)
            enriched = CostcoItem(
                item.item_number,
                item.item_sign,
                item.sell_price,
                item.timestamp,
                item.source_file,
                parsed,
            )
            candidates.append((score, enriched))

    if not candidates:
        return None, None

    candidates.sort(key=lambda pair: pair[0], reverse=True)
    best_score, best = candidates[0]
    if best_score < 10:
        return None, f"Low-confidence Costco match: {best.item_sign}"
    if best.parsed is None:
        best = CostcoItem(
            best.item_number,
            best.item_sign,
            best.sell_price,
            best.timestamp,
            best.source_file,
            parse_item_sign(best.item_sign, meta.comparable_unit),
        )
    return best, None
