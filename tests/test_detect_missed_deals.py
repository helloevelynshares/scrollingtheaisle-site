"""Tests for scripts/detect_missed_deals.py (missed-deal coverage detector)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "detect_missed_deals", ROOT / "scripts" / "detect_missed_deals.py"
)
dmd = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
# Register before exec so dataclass type resolution can find the module.
sys.modules[_SPEC.name] = dmd
_SPEC.loader.exec_module(dmd)

from price_tracker.canonical_families import family_by_id  # noqa: E402


class TestParsePrice(unittest.TestCase):
    def test_dollar_and_plain(self) -> None:
        self.assertEqual(dmd.parse_price("$3.49"), 3.49)
        self.assertEqual(dmd.parse_price("3.49"), 3.49)

    def test_empty_and_bad(self) -> None:
        self.assertIsNone(dmd.parse_price(""))
        self.assertIsNone(dmd.parse_price(None))
        self.assertIsNone(dmd.parse_price("-"))
        self.assertIsNone(dmd.parse_price("BOGO"))


class TestMultiProductHeuristic(unittest.TestCase):
    def test_focused_single_product(self) -> None:
        self.assertFalse(dmd._looks_multi_product("nabisco family size snack crackers 10-14 oz"))
        self.assertFalse(dmd._looks_multi_product("cheez-it crackers"))

    def test_multi_product_block(self) -> None:
        self.assertTrue(
            dmd._looks_multi_product("doritos, ruffles, smartfood, sunchips 6-10.75 oz")
        )
        self.assertTrue(dmd._looks_multi_product("kellogg's cereal 8.8 oz\npepperidge 5.9 oz"))


class TestMatchText(unittest.TestCase):
    def test_field_precedence_prefers_product_field(self) -> None:
        row = {
            "split_product_text": "",
            "verified_raw_product_text": "Nabisco Snack Crackers",
            "raw_product_text": "ignored",
            "raw_offer_text": "long multi-product blob mentioning cheez-it and 20 other things",
        }
        self.assertEqual(dmd._match_text(row), "nabisco snack crackers")

    def test_does_not_fall_back_to_offer_blob(self) -> None:
        # No product-name field → returns "" so we never match on the noisy blob.
        row = {"raw_offer_text": "cheez-it buried inside an unrelated turkey tile"}
        self.assertEqual(dmd._match_text(row), "")


class TestFamilyMatches(unittest.TestCase):
    def test_family_size_snack_crackers_matches(self) -> None:
        fam = family_by_id()["nabisco_snack_crackers"]
        self.assertTrue(
            dmd.family_matches("nabisco family size snack crackers 10-14 oz", fam)
        )

    def test_exclude_blocks(self) -> None:
        oreo = family_by_id()["oreo_family_size"]
        # Combined Oreo/Chips-Ahoy text must be excluded (keep_separate_from).
        self.assertFalse(
            dmd.family_matches("nabisco family size oreo cookies or chips ahoy! cookies", oreo)
        )


class TestCandidateSeverity(unittest.TestCase):
    def test_raw_only_focused_is_high(self) -> None:
        c = dmd.Candidate(feed="safeway", week="2026-07-08", family_id="x")
        c.in_raw = True
        c.multi_product = False
        self.assertEqual(c.severity, "high")

    def test_raw_only_multiproduct_is_medium(self) -> None:
        c = dmd.Candidate(feed="safeway", week="2026-07-08", family_id="x")
        c.in_raw = True
        c.multi_product = True
        self.assertEqual(c.severity, "medium")

    def test_audit_rejected_is_info(self) -> None:
        c = dmd.Candidate(feed="safeway", week="2026-07-08", family_id="x")
        c.in_raw = True
        c.multi_product = False
        c.audit = {"rejected"}
        self.assertEqual(c.severity, "info")


if __name__ == "__main__":
    unittest.main()
