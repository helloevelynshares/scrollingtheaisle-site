#!/usr/bin/env python3
"""Generate the content-first weekly-ad deal shortlist (ANALYSIS ONLY).

This is the content-deal mode described in docs/PROJECT_NOTES.md. It is fully
separate from the canonical tracker-graph pipeline: it never writes to
``weeklyAdPrices.generated.ts`` or any generated graph TS, and it never touches
canonical eligibility. It produces four artifacts under
``output/weekly_deals/<week>/``:

  * content_gap_analysis.md / .json
  * content_script_shortlist.md / .json

Usage:
  PYTHONPATH=scripts python3 scripts/generate_content_shortlist.py \\
      --week 2026-07-08 --store safeway
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from weekly_ad_analysis.content_shortlist import write_outputs  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Content-first weekly-ad shortlist")
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    parser.add_argument("--store", required=True, choices=["safeway", "vons"])
    parser.add_argument("--output-dir", help="Override output folder")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else ROOT / "output" / "weekly_deals" / args.week
    )
    summary = write_outputs(args.week, args.store, output_dir)
    print(f"Content shortlist written to {summary['output_dir']}")
    print(f"  items: {summary['items']}")
    print(f"  coverage gaps: {summary['coverage_gaps']}")
    print("  section counts:")
    for name, count in summary["section_counts"].items():
        print(f"    {name}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
