#!/usr/bin/env python3
"""
Extract food product mentions from TikTok bulk transcripts.

Reads bulk_transcripts.csv (repo root or data/raw/), excludes non-food categories,
weights by video views, and writes data/processed/tiktok_item_mentions.csv.

Usage:
  python scripts/extract_tiktok_food_mentions.py
  python scripts/extract_tiktok_food_mentions.py --input bulk_transcripts.csv
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from tiktok_food_config import (
    COMPILED_LEXICON,
    is_non_food_query,
    snippet_around,
    view_priority_score,
)

DEFAULT_INPUTS = (
    REPO_ROOT / "bulk_transcripts.csv",
    REPO_ROOT / "data/raw/bulk_transcripts.csv",
)
DEFAULT_OUTPUT = REPO_ROOT / "data/processed/tiktok_item_mentions.csv"

TITLE_COLUMNS = ("video_title", "title", "name")
URL_COLUMNS = ("video_url", "url", "link", "video_link")
VIEWS_COLUMNS = ("views", "view_count", "play_count", "plays")
TEXT_COLUMNS = ("transcript", "text", "caption", "description", "content")

OUTPUT_FIELDS = (
    "video_title",
    "video_url",
    "views",
    "item_mentioned",
    "brand_guess",
    "category",
    "content_theme",
    "evidence_snippet",
    "suggested_search_query",
    "priority_score",
)

logger = logging.getLogger("extract_tiktok_food_mentions")


def pick_column(fieldnames: list[str] | None, candidates: tuple[str, ...]) -> str | None:
    if not fieldnames:
        return None
    lower_map = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def parse_views(raw: str) -> int:
    text = (raw or "").strip().lower().replace(",", "")
    if not text:
        return 0
    mult = 1
    if text.endswith("k"):
        mult = 1_000
        text = text[:-1]
    elif text.endswith("m"):
        mult = 1_000_000
        text = text[:-1]
    try:
        return int(float(text) * mult)
    except ValueError:
        return 0


def resolve_input_path(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path if path.is_file() else None
    for candidate in DEFAULT_INPUTS:
        if candidate.is_file():
            return candidate
    return None


def extract_mentions_from_text(
    text: str,
    *,
    video_title: str,
    video_url: str,
    views: int,
) -> list[dict[str, str | float]]:
    if not text.strip():
        return []

    priority = view_priority_score(views)
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, str | float]] = []

    for pattern, entry in COMPILED_LEXICON:
        if is_non_food_query(entry.suggested_search_query):
            continue
        for match in pattern.finditer(text):
            key = (entry.item_mentioned, entry.suggested_search_query)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "video_title": video_title,
                    "video_url": video_url,
                    "views": str(views),
                    "item_mentioned": entry.item_mentioned,
                    "brand_guess": entry.brand_guess,
                    "category": entry.category,
                    "content_theme": entry.content_theme,
                    "evidence_snippet": snippet_around(text, match.start(), match.end()),
                    "suggested_search_query": entry.suggested_search_query,
                    "priority_score": f"{priority:.1f}",
                }
            )
    return rows


def process_transcripts(path: Path) -> list[dict[str, str | float]]:
    all_rows: list[dict[str, str | float]] = []

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        title_col = pick_column(reader.fieldnames, TITLE_COLUMNS)
        url_col = pick_column(reader.fieldnames, URL_COLUMNS)
        views_col = pick_column(reader.fieldnames, VIEWS_COLUMNS)
        text_cols = [
            pick_column(reader.fieldnames, (col,))
            for col in TEXT_COLUMNS
            if pick_column(reader.fieldnames, (col,))
        ]
        text_cols = [c for c in text_cols if c]

        if not text_cols:
            raise ValueError(
                f"{path} needs a transcript column ({', '.join(TEXT_COLUMNS)})"
            )

        for line_no, row in enumerate(reader, start=2):
            title = (row.get(title_col) if title_col else "") or ""
            url = (row.get(url_col) if url_col else "") or ""
            views = parse_views(row.get(views_col, "") if views_col else "")
            combined = "\n".join((row.get(col) or "") for col in text_cols)
            mentions = extract_mentions_from_text(
                combined,
                video_title=title.strip(),
                video_url=url.strip(),
                views=views,
            )
            if not mentions and line_no <= 3:
                logger.debug("No food mentions on line %d", line_no)
            all_rows.extend(mentions)

    all_rows.sort(
        key=lambda r: (
            -float(r["priority_score"]),
            -int(r["views"]),
            r["suggested_search_query"],
        ),
    )
    return all_rows


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Extract TikTok food mentions from transcripts.")
    parser.add_argument("--input", help="Path to bulk_transcripts.csv")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output CSV path",
    )
    args = parser.parse_args()

    input_path = resolve_input_path(args.input)
    if not input_path:
        logger.error(
            "bulk_transcripts.csv not found. Place it at bulk_transcripts.csv or "
            "data/raw/bulk_transcripts.csv (see data/raw/README.md)."
        )
        return 1

    logger.info("Reading %s", input_path)
    try:
        rows = process_transcripts(input_path)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    unique_queries = len({r["suggested_search_query"] for r in rows})
    logger.info(
        "Wrote %d mention row(s), %d unique search queries → %s",
        len(rows),
        unique_queries,
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
