#!/usr/bin/env python3
"""Analyze a weekly grocery ad against the Scrolling the Aisle food watchlist.

Usage:
  python3 scripts/analyze_weekly_ad.py --week=2026-06-17 --market=bay_area
  python3 scripts/analyze_weekly_ad.py --week=2026-06-17 --market=socal_oc \\
    --input-dir=data/weekly_ads/2026-06-17/socal_oc \\
    --output-dir=output/weekly_deals/2026-06-17/socal_oc
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from weekly_ad_analysis.config_loader import load_markets  # noqa: E402
from weekly_ad_analysis.pipeline import run_analysis  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weekly ad watchlist analysis")
    parser.add_argument("--week", required=True, help="Week start date YYYY-MM-DD")
    parser.add_argument("--market", required=True, choices=["bay_area", "socal_oc"])
    parser.add_argument("--input-dir", help="Override weekly input folder")
    parser.add_argument("--output-dir", help="Override weekly output folder")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markets = load_markets()
    market = markets[args.market]

    input_dir = Path(
        args.input_dir
        or market.default_input_folder_pattern.format(week=args.week)
    )
    if not input_dir.is_absolute():
        input_dir = (ROOT / input_dir).resolve()

    output_dir = Path(
        args.output_dir
        or market.default_output_folder_pattern.format(week=args.week)
    )
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir = output_dir.resolve()

    print(f"Market: {market.display_name} ({market.id})")
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")

    run_analysis(
        week=args.week,
        market_id=args.market,
        input_dir=input_dir,
        output_dir=output_dir,
    )
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
