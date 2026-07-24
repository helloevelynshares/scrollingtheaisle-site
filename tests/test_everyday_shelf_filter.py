"""Everyday / shelf flyer rows must not become weekly chart points."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from generate_weekly_ad_prices import (  # noqa: E402
    _remap_baselines_to_family_ids,
    exceeds_store_baseline,
    is_crop_tile_mismatch_row,
    is_everyday_shelf_price_row,
    is_untrustworthy_crop_mismatch_row,
    load_feed_baselines,
    week_price_from_row,
)
from price_tracker.yaml_matchers import build_yaml_matchers  # noqa: E402


def _matcher(family_id: str):
    return next(m for m in build_yaml_matchers() if m.canonical_id == family_id)


class EverydayShelfFilterTest(unittest.TestCase):
    def test_bare_every_day_promo_is_shelf(self) -> None:
        row = {
            "promo_text": "Every Day",
            "raw_offer_text": "Yellow Peaches or Nectarines Every Day 4.49 lb",
            "price_role_guess": "baseline_candidate",
            "advertised_price": "4.49",
            "price_basis": "per_lb",
            "split_product_text": "Yellow Peaches",
        }
        self.assertTrue(is_everyday_shelf_price_row(row))

    def test_member_price_every_day_deal_kept(self) -> None:
        row = {
            "promo_text": "2/$4 Member Price Every Day",
            "raw_offer_text": "Hass Avocado 2/$4 Member Price Every Day",
            "advertised_price": "4.0",
            "price_basis": "multi_buy",
            "split_product_text": "Hass Avocado",
        }
        self.assertFalse(is_everyday_shelf_price_row(row))

    def test_week_entry_nulls_everyday_and_above_baseline(self) -> None:
        matcher = _matcher("peaches_per_lb")
        everyday = {
            "promo_text": "Every Day",
            "raw_offer_text": "Yellow Peaches Every Day 4.49 lb",
            "price_role_guess": "baseline_candidate",
            "advertised_price": "4.49",
            "price_basis": "per_lb",
            "split_product_text": "Yellow Peaches",
        }
        entry = week_price_from_row(everyday, matcher, baseline=2.99)
        self.assertIsNone(entry["price"])

        sale_above = {
            "promo_text": "MEMBER PRICE",
            "raw_offer_text": "Yellow Peaches 3.49 LB MEMBER PRICE",
            "advertised_price": "3.49",
            "price_basis": "per_lb",
            "split_product_text": "Yellow Peaches",
            "availability_type_guess": "full_week",
        }
        entry2 = week_price_from_row(sale_above, matcher, baseline=2.99)
        self.assertIsNone(entry2["price"])
        self.assertTrue(exceeds_store_baseline(3.49, 2.99))

        real_sale = {
            "promo_text": "MEMBER PRICE",
            "raw_offer_text": "Yellow Peaches 1.99 LB MEMBER PRICE",
            "advertised_price": "1.99",
            "price_basis": "per_lb",
            "split_product_text": "Yellow Peaches",
            "availability_type_guess": "full_week",
        }
        entry3 = week_price_from_row(real_sale, matcher, baseline=2.99)
        self.assertEqual(entry3["price"], 1.99)


class CropTileMismatchFilterTest(unittest.TestCase):
    def test_detects_crop_tile_mismatch_flag(self) -> None:
        self.assertTrue(
            is_crop_tile_mismatch_row(
                {"review_reasons": "crop_tile_mismatch"}
            )
        )
        self.assertFalse(
            is_crop_tile_mismatch_row(
                {"review_reasons": "crop_override_price"}
            )
        )

    def test_bare_mismatch_keeps_plausible_sale(self) -> None:
        """Many real Lucerne weeks are tagged crop_tile_mismatch but look fine."""
        matcher = _matcher("eggs_dozen_normalized")
        row = {
            "advertised_price": "2.49",
            "price_basis": "each",
            "promo_text": "",
            "split_product_text": "Lucerne Large Eggs",
            "raw_offer_text": "Lucerne Large Eggs 12 ct",
            "package_text": "12 ct",
            "review_reasons": "crop_tile_mismatch",
            "availability_type_guess": "full_week",
        }
        self.assertTrue(is_crop_tile_mismatch_row(row))
        self.assertFalse(
            is_untrustworthy_crop_mismatch_row(row, unit_price=2.49, baseline=3.99)
        )
        entry = week_price_from_row(row, matcher, baseline=3.99)
        self.assertEqual(entry["price"], 2.49)

    def test_vons_eggs_bogo_mismatch_nulled(self) -> None:
        """Jul 15 Vons: eggs + BOGO promo while crop was ground beef."""
        matcher = _matcher("eggs_dozen_normalized")
        row = {
            "advertised_price": "4.99",
            "price_basis": "each",
            "promo_text": "Buy 1 Get 1 Free",
            "split_product_text": "Lucerne Large Eggs",
            "raw_offer_text": "Lucerne Large Eggs 12 ct",
            "package_text": "12 ct",
            "review_reasons": "crop_tile_mismatch",
            "availability_type_guess": "full_week",
        }
        self.assertTrue(
            is_untrustworthy_crop_mismatch_row(row, unit_price=4.99, baseline=3.99)
        )
        entry = week_price_from_row(row, matcher, baseline=3.99)
        self.assertIsNone(entry["price"])
        self.assertIsNone(entry["promoNote"])


class BaselineRemapTest(unittest.TestCase):
    def test_remap_exposes_yaml_family_ids(self) -> None:
        remapped = _remap_baselines_to_family_ids({"eggs_18_count": 3.99})
        self.assertEqual(remapped["eggs_18_count"], 3.99)
        self.assertEqual(remapped["eggs_dozen_normalized"], 3.99)

    def test_vons_baselines_resolve_eggs_family(self) -> None:
        baselines = load_feed_baselines("Vons")
        self.assertIn("eggs_dozen_normalized", baselines)
        self.assertGreater(baselines["eggs_dozen_normalized"], 0)

    def test_eggs_above_baseline_nulled_when_family_keyed(self) -> None:
        matcher = _matcher("eggs_dozen_normalized")
        # No crop mismatch — only above-baseline should kill the point.
        row = {
            "advertised_price": "4.99",
            "price_basis": "each",
            "promo_text": "",
            "split_product_text": "Lucerne Large Eggs",
            "raw_offer_text": "Lucerne Large Eggs 12 ct",
            "package_text": "12 ct",
            "review_reasons": "",
            "availability_type_guess": "full_week",
        }
        entry = week_price_from_row(row, matcher, baseline=3.99)
        self.assertIsNone(entry["price"])


if __name__ == "__main__":
    unittest.main()
