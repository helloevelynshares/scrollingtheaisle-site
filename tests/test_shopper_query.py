"""Unit tests for shopper-query normalization, parsing, and behavior mapping."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from shopper_query.behavior import decide_behavior  # noqa: E402
from shopper_query.deterministic_parser import parse_shopper_query  # noqa: E402
from shopper_query.normalize import normalize_shopper_query  # noqa: E402
from shopper_query.schema import ParsedShopperQuery  # noqa: E402


class TestNormalize(unittest.TestCase):
    def test_bucks_to_dollar(self) -> None:
        result = normalize_shopper_query("Doritos are five bucks")
        self.assertIn("$5", result.normalized)
        types = {s.normalization_type for s in result.steps}
        self.assertIn("bucks_to_dollar", types)

    def test_two_fifty(self) -> None:
        result = normalize_shopper_query("priced at two fifty")
        self.assertIn("$2.50", result.normalized)

    def test_bogo_synonym(self) -> None:
        result = normalize_shopper_query("buy one get one free on yogurt")
        self.assertIn("BOGO", result.normalized)

    def test_gotta_buy(self) -> None:
        result = normalize_shopper_query("gotta buy 3 for the deal")
        self.assertIn("when you buy 3", result.normalized.lower())

    def test_need_to_buy_word_number(self) -> None:
        result = normalize_shopper_query("need to buy three")
        self.assertIn("when you buy 3", result.normalized.lower())

    def test_three_for_verbal(self) -> None:
        result = normalize_shopper_query("three for five bucks")
        self.assertTrue(
            "3 for" in result.normalized.lower() or "3 for $5" in result.normalized
        )
        self.assertIn("$5", result.normalized)

    def test_package_synonym_not_silently_mapped(self) -> None:
        result = normalize_shopper_query("Cheerios big box $3.99")
        self.assertIn("big box", result.normalized.lower())
        observed = [
            s for s in result.steps if s.normalization_type == "package_synonym_observed"
        ]
        self.assertTrue(observed)

    def test_steps_have_metadata(self) -> None:
        result = normalize_shopper_query("five bucks BOGO")
        for step in result.steps:
            self.assertTrue(step.source_text)
            self.assertIsNotNone(step.replacement)
            self.assertTrue(step.normalization_type)
            self.assertGreaterEqual(step.confidence, 0.0)
            self.assertLessEqual(step.confidence, 1.0)


class TestDeterministicParser(unittest.TestCase):
    def test_explicit_multibuy(self) -> None:
        parsed = parse_shopper_query(
            "Safeway Doritos Tortilla Chips 9.75 oz $2.49 when you buy 3"
        )
        self.assertEqual(parsed.retailer, "safeway")
        self.assertAlmostEqual(parsed.price or 0, 2.49)
        self.assertEqual(parsed.promotion_type, "multi_buy")
        self.assertEqual(parsed.required_quantity, 3)
        self.assertIn("doritos", parsed.product_text.lower())

    def test_n_for_x(self) -> None:
        parsed = parse_shopper_query("Safeway eggs 2 for $5")
        self.assertEqual(parsed.promotion_type, "multi_buy")
        self.assertEqual(parsed.required_quantity, 2)
        self.assertAlmostEqual(parsed.price or 0, 5.0)

    def test_bogo(self) -> None:
        parsed = parse_shopper_query("Oreo family size BOGO at Safeway $3.99")
        self.assertEqual(parsed.promotion_type, "bogo")
        self.assertEqual(parsed.required_quantity, 1)

    def test_conflicting_prices(self) -> None:
        parsed = parse_shopper_query("Doritos $1.99 or $2.49")
        self.assertTrue(parsed.conflicting_prices)
        self.assertIsNone(parsed.price)

    def test_unsupported_retailer(self) -> None:
        parsed = parse_shopper_query("Trader Joe's bananas $0.69")
        self.assertTrue(parsed.unsupported_retailer)

    def test_bucks_without_normalize_incomplete(self) -> None:
        # Without normalization, "five bucks" is not a numeric price.
        parsed = parse_shopper_query("Cheerios are five bucks")
        self.assertIsNone(parsed.price)

    def test_chips_ahoy_is_not_unspecified_chip_brand(self) -> None:
        parsed = parse_shopper_query("Safeway Chips Ahoy are $1.99")
        self.assertNotIn("product_brand_unspecified:chips", parsed.ambiguities)
        self.assertIn("chips ahoy", parsed.product_text.lower())

    def test_preserves_brand_apostrophe_and_hyphen(self) -> None:
        lays = parse_shopper_query("Safeway Lay's potato chips are $2.49")
        self.assertIn("lay's", lays.product_text.lower())
        self.assertNotIn("product_brand_unspecified:chips", lays.ambiguities)
        cheez = parse_shopper_query("Safeway Cheez-It crackers are $2.49")
        self.assertIn("cheez-it", cheez.product_text.lower())


class TestBehavior(unittest.TestCase):
    def test_invalid_on_conflict(self) -> None:
        parsed = ParsedShopperQuery(
            product_text="Doritos",
            conflicting_prices=True,
        )
        decision = decide_behavior(
            parsed,
            match_status="matched",
            matched_family_id="doritos_5_13oz",
        )
        self.assertEqual(decision.behavior, "invalid")
        self.assertFalse(decision.automatic_continuation_safe)

    def test_clarify_missing_price(self) -> None:
        parsed = ParsedShopperQuery(
            product_text="Oreo family size",
            price=None,
            missing_fields=["price"],
        )
        decision = decide_behavior(
            parsed,
            match_status="matched",
            matched_family_id="oreo_family_size",
        )
        self.assertEqual(decision.behavior, "clarify")

    def test_continue_on_unique_match(self) -> None:
        parsed = ParsedShopperQuery(
            product_text="Doritos 9.75 oz",
            price=1.99,
            promotion_type="multi_buy",
            required_quantity=3,
        )
        decision = decide_behavior(
            parsed,
            match_status="matched",
            matched_family_id="doritos_5_13oz",
        )
        self.assertEqual(decision.behavior, "continue")
        self.assertTrue(decision.automatic_continuation_safe)

    def test_clarify_package_synonym(self) -> None:
        parsed = ParsedShopperQuery(
            product_text="Cheerios big box",
            price=3.99,
            ambiguities=["package_synonym_ambiguous:big_box"],
        )
        decision = decide_behavior(
            parsed,
            match_status="matched",
            matched_family_id="general_mills_cereal_family_size",
        )
        self.assertEqual(decision.behavior, "clarify")

    def test_unsupported_retailer(self) -> None:
        parsed = ParsedShopperQuery(
            product_text="bananas",
            price=0.69,
            unsupported_retailer=True,
            retailer="trader_joes",
        )
        decision = decide_behavior(
            parsed,
            match_status="no_match",
            matched_family_id=None,
        )
        self.assertEqual(decision.behavior, "unsupported")


class TestNormalizeThenParse(unittest.TestCase):
    def test_five_bucks_pipeline(self) -> None:
        norm = normalize_shopper_query(
            "Safeway Cheerios family size is five bucks when you buy 3"
        )
        parsed = parse_shopper_query(norm.normalized)
        self.assertAlmostEqual(parsed.price or 0, 5.0)
        self.assertEqual(parsed.required_quantity, 3)
        self.assertEqual(parsed.promotion_type, "multi_buy")


if __name__ == "__main__":
    unittest.main()
