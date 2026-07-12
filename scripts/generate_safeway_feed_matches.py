#!/usr/bin/env python3
"""Generate Safeway baseline entries for priceTrackerFallback.ts from candidates CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "processed" / "safeway_baseline_candidates_v1.csv"
FALLBACK_TS = ROOT / "src" / "data" / "priceTrackerFallback.ts"
SOURCE_LABEL = "Safeway search result CSV"

sys.path.insert(0, str(ROOT / "scripts"))
from price_tracker.baseline_per_lb import normalize_baseline_price


def parse_price(raw: str) -> float | None:
    cleaned = raw.replace("$", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def load_rank1(path: Path) -> dict[str, dict[str, str]]:
    best: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            cid = row["canonical_id"]
            rank = int(row.get("candidate_rank") or 99)
            if cid not in best or rank < int(best[cid].get("candidate_rank") or 99):
                best[cid] = row
    return best


def ts_entry(row: dict[str, str], price: float) -> str:
    name = row.get("product_name") or row["canonical_id"]
    return (
        f"  {json.dumps(row['canonical_id'])}: {{\n"
        f"    price: {price},\n"
        f"    source: {json.dumps(SOURCE_LABEL)},\n"
        f"    retailerProductName: {json.dumps(name)},\n"
        f"  }}"
    )


def effective_price(cid: str, product_name: str, raw_price: float) -> float:
    """Return the per-lb price for per-lb families; otherwise return raw_price."""
    normalized, was_normalized = normalize_baseline_price(cid, product_name, raw_price)
    if was_normalized:
        print(f"  [per-lb] {cid}: ${raw_price} / product '{product_name}' → ${normalized}/lb")
    return normalized


def merge_into_fallback(new_entries: dict[str, dict[str, str]]) -> None:
    text = FALLBACK_TS.read_text(encoding="utf-8")
    marker = "SAFEWAY_BASELINES"
    start = text.index(marker)
    value_marker = "= {"
    brace_start = text.index(value_marker, start) + len(value_marker) - 1
    depth = 0
    end = brace_start
    for index, char in enumerate(text[brace_start:], start=brace_start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index
                break
    existing_block = text[brace_start + 1 : end]
    existing_ids = set()
    for line in existing_block.splitlines():
        stripped = line.strip()
        if stripped.endswith(":") or stripped.endswith(": {"):
            continue
        if ":" in stripped and stripped[0].isalpha() or stripped.startswith('"'):
            key = stripped.split(":", 1)[0].strip().rstrip(",")
            if key.startswith('"') and key.endswith('"'):
                existing_ids.add(json.loads(key))

    additions: list[str] = []
    for cid, row in sorted(new_entries.items()):
        if cid in existing_ids:
            continue
        raw_price = parse_price(row.get("price", ""))
        if raw_price is None:
            continue
        price = effective_price(cid, row.get("product_name", ""), raw_price)
        additions.append(ts_entry(row, price))

    if not additions:
        print("No new Safeway baselines to merge")
        return

    insert_at = end
    prefix = ",\n" if existing_block.strip() else "\n"
    updated = text[:insert_at] + prefix + ",\n".join(additions) + text[insert_at:]
    FALLBACK_TS.write_text(updated, encoding="utf-8")
    print(f"Merged {len(additions)} Safeway baseline(s) into {FALLBACK_TS.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge Safeway baseline CSV into fallback TS.")
    parser.add_argument("--input", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--merge-fallback", action="store_true")
    args = parser.parse_args()

    path = args.input if args.input.is_absolute() else ROOT / args.input
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}. Run: python scripts/seed_safeway_baseline.py --browser-like")

    rank1 = load_rank1(path)
    if not rank1:
        raise RuntimeError(f"No rank-1 rows in {path}")

    for cid, row in sorted(rank1.items()):
        raw_price = parse_price(row.get("price", ""))
        price = effective_price(cid, row.get("product_name", ""), raw_price) if raw_price is not None else None
        print(f"{cid}: {price}: {row.get('product_name', '')[:60]}")

    if args.merge_fallback:
        merge_into_fallback(rank1)


if __name__ == "__main__":
    main()
