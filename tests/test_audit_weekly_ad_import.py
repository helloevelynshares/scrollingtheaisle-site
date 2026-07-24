#!/usr/bin/env python3
"""Tests for scripts/audit_weekly_ad_import.py."""

from __future__ import annotations

import unittest

from audit_weekly_ad_import import (
    AuditReport,
    CropOverrideFinding,
    WowWorsenFinding,
    crop_overrides_from_raw,
    crop_overrides_from_split,
    prior_matched_week,
)


class TestCropOverridesFromRaw(unittest.TestCase):
    def test_flags_crop_raise_like_doritos_bleed(self) -> None:
        rows = [
            {
                "week_start": "2026-07-15",
                "page_number": "1",
                "offer_index_on_page": "17",
                "raw_product_text": "Lay's, Lay's Kettle, PopCorners or Doritos",
                "original_advertised_price": "2.49",
                "verified_advertised_price": "5.99",
                "advertised_price": "5.99",
                "package_text": "4.5-8 oz.",
                "layout_type": "coupon_grid_offer",
                "review_reasons": (
                    "first_pass_crop_disagreement|crop_verification_override|"
                    "crop_override_price"
                ),
            }
        ]
        findings = crop_overrides_from_raw("safeway", "2026-07-15", rows, "test.csv")
        self.assertEqual(len(findings), 1)
        finding: CropOverrideFinding = findings[0]
        self.assertEqual(finding.original_price, "2.49")
        self.assertEqual(finding.final_price, "5.99")
        self.assertIn("bleed", finding.note)

    def test_flags_bare_crop_tile_mismatch_like_vons_eggs(self) -> None:
        rows = [
            {
                "week_start": "2026-07-15",
                "page_number": "3",
                "offer_index_on_page": "7",
                "raw_product_text": "Lucerne Large Eggs",
                "original_advertised_price": "4.99",
                "verified_advertised_price": "5.99",
                "advertised_price": "4.99",
                "package_text": "12 ct",
                "layout_type": "standard_grid_offer",
                "review_reasons": "crop_tile_mismatch",
            }
        ]
        findings = crop_overrides_from_raw("vons", "2026-07-15", rows, "test.csv")
        self.assertEqual(len(findings), 1)
        self.assertIn("crop_tile_mismatch", findings[0].note)
        self.assertEqual(findings[0].original_price, "4.99")
        self.assertEqual(findings[0].final_price, "5.99")


class TestCropOverridesFromSplit(unittest.TestCase):
    def test_flags_crop_tile_mismatch_in_split(self) -> None:
        rows = [
            {
                "week_start": "2026-07-15",
                "page_number": "3",
                "offer_index_on_page": "7",
                "split_product_text": "Lucerne Large Eggs",
                "advertised_price": "4.99",
                "package_text": "12 ct",
                "layout_type": "standard_grid_offer",
                "review_reasons": "crop_tile_mismatch",
            }
        ]
        findings = crop_overrides_from_split("vons", "2026-07-15", rows)
        self.assertEqual(len(findings), 1)
        self.assertIn("crop_tile_mismatch", findings[0].note)


class TestPriorMatchedWeek(unittest.TestCase):
    def test_picks_latest_prior_with_price(self) -> None:
        weeks = {
            "2026-07-01": {"price": 2.2},
            "2026-07-08": {"price": 2.5},
            "2026-07-15": {"price": 5.99},
            "2026-06-24": {"price": None},
        }
        prior = prior_matched_week(weeks, "2026-07-15")
        self.assertEqual(prior, ("2026-07-08", 2.5))


class TestTrackedFindingCount(unittest.TestCase):
    def test_counts_wow_and_bleed_only(self) -> None:
        report = AuditReport(
            week_start="2026-07-15",
            crop_overrides=[
                CropOverrideFinding(
                    feed="Vons",
                    source="test",
                    page="3",
                    offer_index="7",
                    product="Lucerne Large Eggs",
                    original_price="4.99",
                    final_price="5.99",
                    package="12 ct",
                    layout="standard_grid_offer",
                    review_reasons="crop_tile_mismatch",
                    note="crop_tile_mismatch — first-pass tile identity disagreed with crop",
                ),
                CropOverrideFinding(
                    feed="Safeway",
                    source="test",
                    page="1",
                    offer_index="17",
                    product="Doritos",
                    original_price="2.49",
                    final_price="5.99",
                    package="4.5-8 oz",
                    layout="coupon_grid_offer",
                    review_reasons="crop_override_price",
                    note="crop raised price vs first-pass — check adjacent-tile bleed",
                ),
            ],
            wow_worsens=[
                WowWorsenFinding(
                    feed="Vons",
                    family_id="eggs_dozen_normalized",
                    week="2026-07-15",
                    prior_week="2026-07-08",
                    price=4.99,
                    prior_price=2.49,
                    ratio=2.0,
                    offer_text="Lucerne Large Eggs",
                    confidence="high",
                )
            ],
        )
        self.assertEqual(report.finding_count, 3)
        # 1 WoW + 1 bleed (bare crop_tile_mismatch does not hard-fail import).
        self.assertEqual(report.tracked_finding_count, 2)


if __name__ == "__main__":
    unittest.main()
