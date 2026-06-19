#!/usr/bin/env python3
"""Generate Safeway baseline entries for priceTrackerFallback.ts from candidates CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "processed" / "safeway_baseline_candidates_v1.csv"
FALLBACK_TS = ROOT / "src" / "data" / "priceTrackerFallback.ts"
SOURCE_LABEL = "Safeway search result CSV"


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


def merge_into_fallback(new_entries: dict[str, dict[str, str]]) -> None:
    text = FALLBACK_TS.read_text(encoding="utf-8")
    marker = "const SAFEWAY_BASELINES"
    start = text.index(marker)
    brace_start = text.index("{", start)
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
        price = parse_price(row.get("price", ""))
        if price is None:
            continue
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
        price = parse_price(row.get("price", ""))
        print(f"{cid}: {price} — {row.get('product_name', '')[:60]}")

    if args.merge_fallback:
        merge_into_fallback(rank1)


if __name__ == "__main__":
    main()
