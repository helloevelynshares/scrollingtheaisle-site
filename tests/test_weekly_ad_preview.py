"""Tests for weekly ad preview date logic and import safeguards."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from price_tracker.weekly_ad_preview import (  # noqa: E402
    build_feed_preview_summary,
    format_preview_summary,
    is_active_week,
    is_preview_week,
    latest_manifest_entry,
    validate_tracker_product_ids_unchanged,
)


class TestWeeklyAdPreviewDates(unittest.TestCase):
    def test_preview_when_today_before_week_start(self) -> None:
        as_of = date(2026, 7, 7)
        self.assertTrue(is_preview_week("2026-07-08", as_of))
        self.assertFalse(is_preview_week("2026-07-07", as_of))

    def test_active_on_start_date(self) -> None:
        as_of = date(2026, 7, 8)
        self.assertFalse(is_preview_week("2026-07-08", as_of))
        self.assertTrue(is_active_week("2026-07-08", "2026-07-14", as_of))

    def test_active_through_end_date(self) -> None:
        as_of = date(2026, 7, 14)
        self.assertTrue(is_active_week("2026-07-08", "2026-07-14", as_of))
        self.assertFalse(is_preview_week("2026-07-08", as_of))

    def test_preview_disappears_after_start(self) -> None:
        as_of = date(2026, 7, 9)
        self.assertFalse(is_preview_week("2026-07-08", as_of))

    def test_latest_manifest_entry(self) -> None:
        manifest = [
            {"week_start": "2026-07-01", "week_end": "2026-07-07"},
            {"week_start": "2026-07-08", "week_end": "2026-07-14"},
        ]
        latest = latest_manifest_entry(manifest)
        self.assertEqual(latest["week_start"], "2026-07-08")


class TestWeeklyAdPreviewSafeguards(unittest.TestCase):
    def test_validate_unchanged_ids_passes(self) -> None:
        before = {"a", "b", "c"}
        after = {"a", "b", "c"}
        added, removed = validate_tracker_product_ids_unchanged(before, after)
        self.assertEqual(added, set())
        self.assertEqual(removed, set())

    def test_validate_unchanged_ids_fails_on_add(self) -> None:
        with self.assertRaises(SystemExit):
            validate_tracker_product_ids_unchanged({"a"}, {"a", "b"})

    def test_validate_unchanged_ids_fails_on_remove(self) -> None:
        with self.assertRaises(SystemExit):
            validate_tracker_product_ids_unchanged({"a", "b"}, {"a"})

    def test_build_feed_preview_summary_preview_week(self) -> None:
        manifest = [{"week_start": "2026-07-08", "week_end": "2026-07-14"}]
        prices = {
            "doritos_5_13oz": {
                "2026-07-08": {"price": 2.5, "offerText": "2 for $5"},
            },
            "grapes": {
                "2026-07-08": {"price": None, "offerText": None},
            },
        }
        summary = build_feed_preview_summary(
            "Safeway",
            manifest,
            prices,
            ["doritos_5_13oz", "grapes"],
            as_of=date(2026, 7, 7),
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertTrue(summary.is_preview)
        self.assertEqual(summary.matched_products, 1)
        self.assertEqual(summary.unmatched_products, 1)
        self.assertEqual(summary.products_before, 2)
        self.assertEqual(summary.products_after, 2)
        text = format_preview_summary(summary)
        self.assertIn("PREVIEW", text)
        self.assertIn("no adds/removes", text)

    def test_build_feed_preview_summary_active_week(self) -> None:
        manifest = [{"week_start": "2026-07-08", "week_end": "2026-07-14"}]
        summary = build_feed_preview_summary(
            "Vons",
            manifest,
            {},
            ["doritos_5_13oz"],
            as_of=date(2026, 7, 10),
        )
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertFalse(summary.is_preview)
        self.assertIn("ACTIVE", format_preview_summary(summary))


class TestExistingTrackedItemsUpdated(unittest.TestCase):
    """Unmatched ad rows must not create new tracked products (structure check)."""

    def test_generated_prices_use_yaml_family_ids_only(self) -> None:
        from price_tracker.yaml_matchers import tracker_family_ids

        path = ROOT / "src" / "data" / "weeklyAdPrices.generated.ts"
        if not path.is_file():
            self.skipTest("generated TS not present")

        from price_tracker.artifacts import parse_ts_export

        parsed = parse_ts_export(path, "WEEKLY_AD_WEEKS", "WEEKLY_AD_PRICES")
        self.assertIsNotNone(parsed)
        _, prices = parsed
        allowed = set(tracker_family_ids())
        extra = set(prices.keys()) - allowed
        self.assertEqual(extra, set(), msg=f"unexpected product ids: {extra}")


if __name__ == "__main__":
    unittest.main()
