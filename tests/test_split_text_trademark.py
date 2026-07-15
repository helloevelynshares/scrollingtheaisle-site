"""Trademark / brand punctuation must not block YAML phrase matching."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_weekly_ad_prices import matches, split_text  # noqa: E402
from price_tracker.yaml_matchers import build_yaml_matchers  # noqa: E402


class TestSplitTextTrademark(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matchers = {m.canonical_id: m for m in build_yaml_matchers()}

    def test_strips_chips_ahoy_bang(self) -> None:
        row = {
            "split_product_text": "Nabisco Chips Ahoy! Cookies 9.5 to 13-oz. Selected varieties."
        }
        self.assertEqual(
            split_text(row),
            "nabisco chips ahoy cookies 9.5 to 13-oz. selected varieties.",
        )

    def test_chips_ahoy_bang_matches_family(self) -> None:
        """Jul 15 miss: ad prints Chips Ahoy!; include phrases have no bang."""
        matcher = self.matchers["chips_ahoy"]
        row = {
            "split_product_text": "Nabisco Chips Ahoy! Cookies 9.5 to 13-oz. Selected varieties.",
            "raw_offer_text": (
                "Nabisco Chips Ahoy! Cookies 9.5 to 13-oz. Selected varieties. "
                "9.5 to 13-oz. 2.49 ea Member Price"
            ),
            "package_text": "9.5 to 13-oz.",
            "advertised_price": "2.49",
            "price_basis": "each",
        }
        self.assertTrue(matches(row, matcher))


if __name__ == "__main__":
    unittest.main()
