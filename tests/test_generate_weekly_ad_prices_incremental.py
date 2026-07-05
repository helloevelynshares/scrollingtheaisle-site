"""Tests for incremental price tracker artifact helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from price_tracker.artifacts import (  # noqa: E402
    merge_week_prices,
    merge_weeks_list,
    parse_ts_export,
    product_ids_missing_from_prices,
)


class TestWeeklyAdIncremental(unittest.TestCase):
    def test_merge_week_prices_inserts_and_updates(self) -> None:
        existing = {
            "grapes": {
                "2026-06-03": {"price": 1.99, "offerText": "old", "confidence": "high"},
            }
        }
        updates = {
            "grapes": {
                "2026-06-03": {"price": 2.49, "offerText": "new", "confidence": "medium"},
                "2026-06-10": {"price": 1.79, "offerText": "sale", "confidence": "high"},
            }
        }
        summary = merge_week_prices(existing, updates, {"grapes"})
        self.assertEqual(summary.updated, 1)
        self.assertEqual(summary.inserted, 1)
        self.assertEqual(existing["grapes"]["2026-06-10"]["price"], 1.79)

    def test_merge_weeks_list_unions_manifest(self) -> None:
        existing = [{"weekStart": "2026-06-03", "weekEnd": "2026-06-09", "sourceFile": "a.pdf", "sourceLabel": "A"}]
        manifest = [{"weekStart": "2026-06-10", "weekEnd": "2026-06-16", "sourceFile": "b.pdf", "sourceLabel": "B"}]
        merged = merge_weeks_list(existing, manifest)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["weekStart"], "2026-06-03")

    def test_product_ids_missing_from_prices(self) -> None:
        all_ids = {"grapes", "eggs_18_count", "strawberries"}
        prices = {"grapes": {}, "strawberries": {}}
        missing = product_ids_missing_from_prices(all_ids, prices)
        self.assertEqual(missing, {"eggs_18_count"})

    def test_parse_ts_export_from_repo(self) -> None:
        path = ROOT / "src" / "data" / "weeklyAdPrices.generated.ts"
        if not path.is_file():
            self.skipTest("generated TS not present")
        parsed = parse_ts_export(path, "WEEKLY_AD_WEEKS", "WEEKLY_AD_PRICES")
        self.assertIsNotNone(parsed)
        weeks, prices = parsed
        self.assertTrue(len(weeks) >= 1)
        self.assertIn("strawberries", prices)


if __name__ == "__main__":
    unittest.main()
