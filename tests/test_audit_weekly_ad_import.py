#!/usr/bin/env python3
"""Tests for scripts/audit_weekly_ad_import.py."""

from __future__ import annotations

import unittest

from audit_weekly_ad_import import (
    CropOverrideFinding,
    crop_overrides_from_raw,
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


if __name__ == "__main__":
    unittest.main()
