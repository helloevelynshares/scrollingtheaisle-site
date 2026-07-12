#!/usr/bin/env python3
"""Import read-only Costco warehouse CSVs into a normalized local cache.

Reads from costco-mvp/costco_data (override with COSTCO_DATA_ROOT).
Writes to data/processed/costco/ inside this repo, never modifies costco-mvp.

Usage:
  python3 scripts/price_comparison/import_costco_data.py
  COSTCO_DATA_ROOT=/path/to/costco_data python3 scripts/price_comparison/import_costco_data.py
  python3 scripts/price_comparison/import_costco_data.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from price_comparison.canonical_metadata import DEFAULT_COSTCO_DATA_ROOT  # noqa: E402
from price_comparison.costco_loader import (  # noqa: E402
    costco_data_root,
    load_all_observations_from_paths,
    parse_costco_filename,
)
from price_comparison.costco_warehouse_mapping import costco_warehouses  # noqa: E402

CACHE_DIR = ROOT / "data" / "processed" / "costco"
OBSERVATIONS_PATH = CACHE_DIR / "observations.json"
MANIFEST_PATH = CACHE_DIR / "manifest.json"


def observation_to_dict(obs) -> dict:
    return {
        "date": obs.date,
        "warehouse": obs.region,
        "itemNumber": obs.item_number,
        "productName": obs.product_name,
        "price": obs.price,
        "availability": obs.availability,
        "sourceFile": obs.source_file,
        "timestamp": obs.timestamp,
    }


def build_manifest(source_root: Path, source_files: list[Path]) -> dict:
    by_warehouse: dict[str, list[str]] = {w: [] for w in costco_warehouses()}
    dates_by_warehouse: dict[str, set[str]] = {w: set() for w in costco_warehouses()}

    for path in source_files:
        parsed = parse_costco_filename(path)
        if parsed is None:
            continue
        file_date, warehouse = parsed
        by_warehouse.setdefault(warehouse, []).append(path.name)
        dates_by_warehouse.setdefault(warehouse, set()).add(file_date)

    return {
        "importedAt": datetime.now(timezone.utc).isoformat(),
        "sourceRoot": str(source_root),
        "observationCount": 0,
        "filesByWarehouse": {
            wh: sorted(set(names)) for wh, names in by_warehouse.items() if names
        },
        "dateRangeByWarehouse": {
            wh: {"min": min(dates), "max": max(dates)} if dates else None
            for wh, dates in dates_by_warehouse.items()
            if dates
        },
    }


def import_costco_data(*, dry_run: bool = False) -> dict:
    source_root = costco_data_root()
    if not source_root.is_dir():
        alt = Path("/Users/kunal/Documents/costco-mvp/costco_data")
        if alt.is_dir():
            source_root = alt
        else:
            raise FileNotFoundError(
                f"Costco data not found at {source_root} or {alt}. "
                "Set COSTCO_DATA_ROOT to costco-mvp/costco_data.",
            )

    source_files = [
        p
        for p in sorted(source_root.iterdir())
        if p.is_file() and parse_costco_filename(p) is not None
    ]
    observations = load_all_observations_from_paths(source_files, source_root)
    manifest = build_manifest(source_root, source_files)
    manifest["observationCount"] = len(observations)

    if dry_run:
        print(f"[dry-run] Would import {len(observations)} observations from {source_root}")
        for wh, info in manifest.get("dateRangeByWarehouse", {}).items():
            if info:
                print(f"  {wh}: {info['min']} → {info['max']} ({len(manifest['filesByWarehouse'].get(wh, []))} files)")
        return manifest

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = [observation_to_dict(obs) for obs in observations]
    OBSERVATIONS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    try:
        rel_obs = OBSERVATIONS_PATH.relative_to(ROOT)
    except ValueError:
        rel_obs = OBSERVATIONS_PATH
    print(f"Wrote {rel_obs} ({len(payload)} observations)")
    try:
        rel_manifest = MANIFEST_PATH.relative_to(ROOT)
    except ValueError:
        rel_manifest = MANIFEST_PATH
    print(f"Wrote {rel_manifest}")
    print(f"Source: {source_root}")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Costco warehouse CSVs to local cache.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    import_costco_data(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
