#!/usr/bin/env python3
"""Import a new weekly ad week into the price tracker (preview-safe).

Orchestrates vision extraction (sibling repo), manifest updates, offer merge,
and price regeneration. Does not add or remove canonical tracker products.

Typical weekly workflow:

  python3 scripts/import_weekly_ad.py \\
    --week-start 2026-07-08 --week-end 2026-07-14 \\
    --safeway-pdf "safeway 7-8 - 7-14.pdf" \\
    --vons-pdf "vons 7-8 - 7-14.pdf"

Skip extraction when split_offer_items already exist:

  python3 scripts/import_weekly_ad.py ... --skip-extraction

Verify only (no writes):

  python3 scripts/import_weekly_ad.py ... --verify-only
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.weekly_ad_preview import (  # noqa: E402
    build_feed_preview_summary,
    format_preview_summary,
    validate_tracker_product_ids_unchanged,
)
from price_tracker.yaml_matchers import tracker_family_ids  # noqa: E402

DEFAULT_DATA_ROOT = Path.home() / "Documents" / "scrolling-the-aisle"
DATA_ROOT = Path(os.environ.get("SCROLLING_THE_AISLE_ROOT", DEFAULT_DATA_ROOT))

MANIFEST_FIELDS = [
    "source_file",
    "parent_company",
    "banner",
    "region",
    "representative_store_id",
    "week_start",
    "week_end",
    "notes",
]

FEED_CONFIG = {
    "safeway": {
        "label": "Safeway",
        "banner": "Safeway",
        "region": "bay_area",
        "parent": "Albertsons",
        "manifest_site": ROOT / "data" / "weekly_ads" / "flyer_manifest_safeway.csv",
        "manifest_sibling": DATA_ROOT / "inputs" / "weekly_ads" / "flyer_manifest_safeway.csv",
        "split_items": DATA_ROOT / "outputs" / "product_discovery_safeway" / "split_offer_items.csv",
        "discovery_dir": DATA_ROOT / "outputs" / "product_discovery_safeway",
    },
    "vons": {
        "label": "Vons",
        "banner": "Vons",
        "region": "southern_california",
        "parent": "Albertsons",
        "manifest_site": ROOT / "data" / "weekly_ads" / "flyer_manifest_vons.csv",
        "manifest_sibling": DATA_ROOT / "inputs" / "weekly_ads" / "flyer_manifest_vons.csv",
        "split_items": DATA_ROOT / "outputs" / "product_discovery_vons" / "split_offer_items.csv",
        "discovery_dir": DATA_ROOT / "outputs" / "product_discovery_vons",
    },
}


@dataclass(frozen=True)
class FeedImportSpec:
    key: str
    pdf_name: str


def load_manifest(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def upsert_manifest_row(
    rows: list[dict[str, str]],
    *,
    source_file: str,
    banner: str,
    region: str,
    parent: str,
    week_start: str,
    week_end: str,
) -> list[dict[str, str]]:
    updated = [row for row in rows if row.get("week_start") != week_start]
    updated.append(
        {
            "source_file": source_file,
            "parent_company": parent,
            "banner": banner,
            "region": region,
            "representative_store_id": "",
            "week_start": week_start,
            "week_end": week_end,
            "notes": "",
        }
    )
    return sorted(updated, key=lambda row: row["week_start"])


def run_extraction(feed_key: str, pdf_name: str) -> None:
    cfg = FEED_CONFIG[feed_key]
    discover = DATA_ROOT / "src" / "discover_product_candidates.py"
    if not discover.is_file():
        raise SystemExit(f"Missing vision pipeline: {discover}")

    # Use date-range token (e.g. "7-8") to avoid matching every historical flyer.
    stem = pdf_name.replace(".pdf", "")
    date_token = stem.split()[-1] if " " in stem else stem
    output_slug = stem.replace(" ", "_").replace("/", "-")
    output_dir = cfg["discovery_dir"].parent / f"product_discovery_{feed_key}_{output_slug}"
    cmd = [
        sys.executable,
        str(discover),
        "--input-dir",
        str(DATA_ROOT / "inputs" / "weekly_ads"),
        "--manifest",
        str(cfg["manifest_sibling"]),
        "--output-dir",
        str(output_dir),
        "--only-file",
        date_token,
    ]
    print(f"Running vision extraction: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=DATA_ROOT)
    split_csv = output_dir / "split_offer_items.csv"
    if result.returncode != 0:
        if split_csv.is_file():
            print(
                f"Warning: extraction exited {result.returncode} "
                f"(often summary_report.py) but {split_csv.name} exists, continuing"
            )
        else:
            raise subprocess.CalledProcessError(result.returncode, cmd)


def merge_split_offer_items(
    feed_key: str,
    week_start: str,
    extracted_csv: Path | None = None,
    pdf_name: str | None = None,
) -> int:
    cfg = FEED_CONFIG[feed_key]
    target = cfg["split_items"]
    if extracted_csv is None and pdf_name:
        stem = pdf_name.replace(".pdf", "").replace(" ", "_").replace("/", "-")
        candidates = [
            cfg["discovery_dir"].parent
            / f"product_discovery_{feed_key}_{stem}"
            / "split_offer_items.csv",
            cfg["discovery_dir"].parent
            / f"product_discovery_safeway_{stem}"
            / "split_offer_items.csv",
        ]
        for candidate in candidates:
            if candidate.is_file():
                extracted_csv = candidate
                break

    if extracted_csv is None:
        for path in sorted(
            cfg["discovery_dir"].parent.glob(f"product_discovery_{feed_key}_*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            candidate = path / "split_offer_items.csv"
            if not candidate.is_file():
                continue
            rows = load_manifest_rows_from_split(candidate)
            if any(row.get("week_start") == week_start for row in rows):
                extracted_csv = candidate
                break

    if extracted_csv is None or not extracted_csv.is_file():
        raise SystemExit(
            f"No extracted split_offer_items.csv found for {feed_key} week {week_start}. "
            "Run without --skip-extraction or pass --extracted-csv."
        )

    new_rows = [
        row
        for row in load_manifest_rows_from_split(extracted_csv)
        if row.get("week_start") == week_start
        and (row.get("banner") or "").strip().lower() == cfg["banner"].lower()
    ]
    if not new_rows:
        raise SystemExit(
            f"No rows for week {week_start} in {extracted_csv}. "
            "Check vision extraction output."
        )

    existing_rows: list[dict[str, str]] = []
    if target.is_file():
        existing_rows = load_manifest_rows_from_split(target)

    existing_ids = {
        row.get("split_item_id")
        for row in existing_rows
        if row.get("split_item_id")
    }
    merged = [row for row in existing_rows if row.get("week_start") != week_start]
    added = 0
    for row in new_rows:
        split_id = row.get("split_item_id")
        if split_id and split_id in existing_ids and row.get("week_start") != week_start:
            continue
        merged.append(row)
        added += 1

    target.parent.mkdir(parents=True, exist_ok=True)
    if merged:
        fieldnames = list(merged[0].keys())
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged)

    print(
        f"Merged {added} offer row(s) for {cfg['label']} week {week_start} "
        f"into {target}"
    )
    return added


def load_manifest_rows_from_split(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_generate_prices(as_of: date | None) -> None:
    cmd = [sys.executable, str(SCRIPT_DIR / "generate_weekly_ad_prices.py")]
    if as_of is not None:
        cmd.extend(["--as-of", as_of.isoformat()])
    print(f"Regenerating weekly ad prices: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def verify_tracker_counts() -> None:
    from price_tracker.artifacts import parse_ts_export

    tracked = set(tracker_family_ids())
    for feed_key, cfg in (
        ("safeway", FEED_CONFIG["safeway"]),
        ("vons", FEED_CONFIG["vons"]),
    ):
        output = (
            ROOT / "src" / "data" / ("weeklyAdPrices.generated.ts" if feed_key == "safeway" else "vonsWeeklyAdPrices.generated.ts")
        )
        weeks_key = "WEEKLY_AD_WEEKS" if feed_key == "safeway" else "VONS_WEEKLY_AD_WEEKS"
        prices_key = "WEEKLY_AD_PRICES" if feed_key == "safeway" else "VONS_WEEKLY_AD_PRICES"
        parsed = parse_ts_export(output, weeks_key, prices_key)
        if parsed is None:
            raise SystemExit(f"Missing generated prices: {output}")
        _, prices = parsed
        validate_tracker_product_ids_unchanged(tracked, prices.keys())
        print(f"{cfg['label']}: canonical product count unchanged ({len(tracked)})")


def print_preview_report(as_of: date | None) -> None:
    from generate_weekly_ad_prices import FEEDS, load_manifest, load_split_items

    tracked = set(tracker_family_ids())
    for config in FEEDS:
        manifest = load_manifest(config.manifest_path)
        split_items = load_split_items(config.split_items_path, config.banner_filter)
        from generate_weekly_ad_prices import build_prices

        _, prices = build_prices(config.feed_label, manifest, split_items)
        validate_tracker_product_ids_unchanged(tracked, prices.keys())
        summary = build_feed_preview_summary(
            config.feed_label,
            manifest,
            prices,
            tracked,
            as_of=as_of,
            products_before=len(tracked),
            products_after=len(prices),
        )
        if summary:
            print(format_preview_summary(summary))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import weekly ad into price tracker.")
    parser.add_argument("--week-start", help="Ad week start (YYYY-MM-DD)")
    parser.add_argument("--week-end", help="Ad week end (YYYY-MM-DD)")
    parser.add_argument("--safeway-pdf", help="Safeway PDF filename in inputs/weekly_ads/")
    parser.add_argument("--vons-pdf", help="Vons PDF filename in inputs/weekly_ads/")
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Skip vision pipeline; use existing extracted CSV",
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Update manifests/merge only; do not regenerate TS",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Validate canonical counts and print preview report only",
    )
    parser.add_argument(
        "--as-of",
        help="Override today's date for preview detection (YYYY-MM-DD)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    as_of = date.fromisoformat(args.as_of) if args.as_of else None

    if args.verify_only:
        verify_tracker_counts()
        print_preview_report(as_of)
        return

    if not args.week_start or not args.week_end:
        raise SystemExit("--week-start and --week-end are required unless --verify-only")

    feeds: list[FeedImportSpec] = []
    if args.safeway_pdf:
        feeds.append(FeedImportSpec("safeway", args.safeway_pdf))
    if args.vons_pdf:
        feeds.append(FeedImportSpec("vons", args.vons_pdf))
    if not feeds:
        raise SystemExit("Provide at least one of --safeway-pdf or --vons-pdf")

    for spec in feeds:
        cfg = FEED_CONFIG[spec.key]
        for manifest_path in (cfg["manifest_site"], cfg["manifest_sibling"]):
            rows = upsert_manifest_row(
                load_manifest(manifest_path),
                source_file=spec.pdf_name,
                banner=cfg["banner"],
                region=cfg["region"],
                parent=cfg["parent"],
                week_start=args.week_start,
                week_end=args.week_end,
            )
            write_manifest(manifest_path, rows)
            print(f"Updated manifest: {manifest_path}")

        if not args.skip_extraction:
            run_extraction(spec.key, spec.pdf_name)

        merge_split_offer_items(spec.key, args.week_start, pdf_name=spec.pdf_name)

    if not args.skip_generate:
        run_generate_prices(as_of)

    verify_tracker_counts()
    print_preview_report(as_of)
    print(
        "\nInspect canonical match audit after import:"
    )
    print(f"  output/weekly_deals/{args.week_start}/canonical_match_audit.md")
    print("\nImport complete. Run: npm run build:price-tracker")


if __name__ == "__main__":
    main()
