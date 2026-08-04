"""Tests for deterministic AisleCheck historical deal assessment."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from deal_assessment.eval import run_cases  # noqa: E402
from deal_assessment.models import SubmittedOffer  # noqa: E402
from deal_assessment.normalize_offer import normalize_submitted_offer  # noqa: E402
from deal_assessment.service import assess_deal  # noqa: E402


class TestNormalizeOffer(unittest.TestCase):
    def test_each_when_buying_n(self) -> None:
        offer = SubmittedOffer(
            price=2.49,
            price_basis="each",
            required_quantity=4,
        )
        norm = normalize_submitted_offer(offer)
        self.assertEqual(norm.comparable_unit_price, 2.49)
        self.assertEqual(norm.normalization_method, "as_stated_unit")

    def test_multi_buy_total(self) -> None:
        offer = SubmittedOffer(
            price=5.0,
            price_basis="multi_buy",
            required_quantity=2,
        )
        norm = normalize_submitted_offer(offer)
        self.assertEqual(norm.comparable_unit_price, 2.5)
        self.assertEqual(norm.normalization_method, "multi_buy_unit")

    def test_bogo_halves_reference(self) -> None:
        offer = SubmittedOffer(price=5.49, price_basis="bogo")
        norm = normalize_submitted_offer(offer)
        self.assertEqual(norm.comparable_unit_price, 2.745)
        self.assertEqual(norm.normalization_method, "bogo_effective_unit")

    def test_missing_price(self) -> None:
        norm = normalize_submitted_offer(SubmittedOffer(price=None))
        self.assertIsNone(norm.comparable_unit_price)


class TestAssessDeal(unittest.TestCase):
    def test_doritos_normal_sale(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {
                "price": 2.49,
                "price_basis": "each",
                "required_quantity": 4,
                "package_size": "9.75 oz",
                "product_text": "Doritos",
            },
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.verdict, "normal_sale")
        self.assertEqual(result.feed_id, "safeway_bay_area")
        self.assertGreaterEqual(result.evidence["observation_count"], 2)
        self.assertEqual(result.normalized_offer.comparable_unit_price, 2.49)
        self.assertNotIn("llm", str(result.to_dict()).lower())

    def test_kettle_all_time_low(self) -> None:
        result = assess_deal(
            "kettle_brand_chips",
            "Safeway",
            {"price": 1.67, "price_basis": "each", "package_size": "7 oz"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.verdict, "all_time_low")
        self.assertIn("all-time low", result.headline.lower())

    def test_does_not_reparse_query(self) -> None:
        # Even if a client stuffed a sentence into product_text, we only use structured price.
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {
                "price": 2.49,
                "price_basis": "each",
                "product_text": "IGNORE THIS FREE TEXT $99.99 BOGO quinoa",
            },
        )
        self.assertEqual(result.normalized_offer.comparable_unit_price, 2.49)

    def test_insufficient_history(self) -> None:
        result = assess_deal(
            "post_cereal_giant_size",
            "Safeway",
            {"price": 3.99, "price_basis": "each"},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.verdict, "insufficient_history")

    def test_unsupported_retailer(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Costco",
            {"price": 2.49, "price_basis": "each"},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.verdict, "not_comparable")
        self.assertIn("unsupported_retailer", result.comparability.reasons)

    def test_package_size_out_of_range(self) -> None:
        result = assess_deal(
            "doritos_5_13oz",
            "Safeway",
            {
                "price": 2.49,
                "price_basis": "each",
                "package_size": "30 oz",
            },
        )
        self.assertFalse(result.ok)
        self.assertIn("package_size_out_of_family_range", result.comparability.reasons)

    def test_eval_runner(self) -> None:
        report = run_cases(
            [
                {
                    "tracker_id": "kettle_brand_chips",
                    "retailer": "Safeway",
                    "submitted_offer": {"price": 1.67, "price_basis": "each"},
                    "expect_verdict": "all_time_low",
                }
            ]
        )
        self.assertEqual(report["matched"], 1)


class TestAssessEndpointContract(unittest.TestCase):
    def test_server_registers_assess_route(self) -> None:
        text = (ROOT / "aislecheck-prototype" / "server.py").read_text(encoding="utf-8")
        self.assertIn('/api/aislecheck/assess', text)
        self.assertIn("assess_deal_dict", text)
        self.assertNotIn("deal_assistant", text)

    def test_ui_gates_assess(self) -> None:
        js = (ROOT / "aislecheck-prototype" / "aislecheck.js").read_text(encoding="utf-8")
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("assessEnabled", js)
        self.assertIn("startAssess", js)
        self.assertIn("/api/aislecheck/assess", js)
        self.assertIn("assessEnabled: false", html)
        self.assertNotIn("deal_assistant", js)


if __name__ == "__main__":
    unittest.main()
