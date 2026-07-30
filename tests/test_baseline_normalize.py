"""Tests for baseline package → unit price normalization."""

from __future__ import annotations

import unittest

from price_tracker.baseline_per_lb import (
    extract_bar_count,
    extract_package_weight_lbs,
    normalize_baseline_price,
)


class TestBaselineNormalize(unittest.TestCase):
    def test_per_lb_divides_package_weight(self) -> None:
        price, ok = normalize_baseline_price(
            "ribeye_steak",
            "USDA Choice Bone In Beef Rib Steak Mega Pack - 3.5 Lb",
            45.47,
        )
        self.assertTrue(ok)
        self.assertEqual(price, 12.99)

    def test_clif_per_bar_divides_five_count(self) -> None:
        price, ok = normalize_baseline_price(
            "clif_bars",
            "CLIF BAR White Chocolate Macadamia Nut Energy Protein Bars - 5 Count",
            7.99,
        )
        self.assertTrue(ok)
        self.assertEqual(price, 1.6)

    def test_clif_per_bar_divides_twelve(self) -> None:
        price, ok = normalize_baseline_price(
            "clif_bars",
            "CLIF BAR Chocolate Chip Energy Protein Bars - 12 Count",
            14.99,
        )
        self.assertTrue(ok)
        self.assertEqual(price, 1.25)

    def test_non_unit_family_unchanged(self) -> None:
        price, ok = normalize_baseline_price(
            "chips_ahoy",
            "Chips Ahoy! Original Chocolate Chip Cookies - 13 Oz",
            5.99,
        )
        self.assertFalse(ok)
        self.assertEqual(price, 5.99)

    def test_extract_helpers(self) -> None:
        self.assertEqual(extract_package_weight_lbs("Red Cherries - 1.75 Lb"), 1.75)
        self.assertEqual(
            extract_bar_count("CLIF BAR Energy Protein Bars - 5 Count"), 5.0
        )
        self.assertIsNone(extract_bar_count("CLIF BAR single 1 Count"))


if __name__ == "__main__":
    unittest.main()
