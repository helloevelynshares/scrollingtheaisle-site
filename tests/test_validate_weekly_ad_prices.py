"""Tests for scripts/validate_weekly_ad_prices.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.canonical_families import TrackerFamily  # noqa: E402
from validate_weekly_ad_prices import (  # noqa: E402
    _compute_median_baseline,
    _include_tokens,
    friday_multibuy_suspect_check,
    keyword_sanity_check,
    per_lb_check,
    price_outlier_check,
    parse_prices_ts,
    validate_feed,
)


def _make_family(
    family_id: str = "test_family",
    canonical_name: str = "Test Product",
    subtitle: str = "regular bags",
    include: tuple[str, ...] = ("Test Product",),
    keep_separate_from: tuple[str, ...] = (),
    category: str = "",
) -> TrackerFamily:
    """Build a minimal TrackerFamily for testing."""
    from price_tracker.canonical_families import build_patterns_from_family

    raw = {
        "id": family_id,
        "canonical_tracker_family": canonical_name,
        "size_format_subtitle": subtitle,
        "display_order": 1,
        "homepage_group": "snacks_and_crackers",
        "include": list(include),
        "keep_separate_from": list(keep_separate_from),
        "category": category,
    }
    patterns, excludes, prefers = build_patterns_from_family(raw)
    return TrackerFamily(
        id=family_id,
        canonical_tracker_family=canonical_name,
        size_format_subtitle=subtitle,
        display_order=1,
        homepage_section="stock_up_snacks_and_treats",
        include=include,
        keep_separate_from=keep_separate_from,
        patterns=patterns,
        exclude_patterns=excludes,
        prefer_patterns=prefers,
        category=category,
    )


class TestIncludeTokens(unittest.TestCase):
    def test_extracts_brand_name(self) -> None:
        family = _make_family(include=("Ruffles Original", "Ruffles Cheddar"))
        tokens = _include_tokens(family)
        self.assertIn("ruffles", tokens)
        self.assertIn("original", tokens)
        self.assertIn("cheddar", tokens)

    def test_filters_stopwords(self) -> None:
        family = _make_family(include=("Test Product oz ct.",))
        tokens = _include_tokens(family)
        self.assertNotIn("oz", tokens)
        self.assertNotIn("ct", tokens)

    def test_includes_canonical_name(self) -> None:
        family = _make_family(canonical_name="Doritos", include=("Doritos Nacho Cheese",))
        tokens = _include_tokens(family)
        self.assertIn("doritos", tokens)


class TestKeywordSanityCheck(unittest.TestCase):
    def setUp(self) -> None:
        self.ruffles = _make_family(
            family_id="ruffles_regular_bags",
            canonical_name="Ruffles",
            include=("Ruffles Original", "Ruffles potato chips"),
            keep_separate_from=(
                "Lindt",
                "Gourmet Truffles",
                "Lindt Truffles",
                "LINDOR",
                "chocolate truffles",
            ),
        )

    def test_good_offer_passes(self) -> None:
        ok, reason = keyword_sanity_check("Ruffles Original", self.ruffles)
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_multi_product_offer_passes(self) -> None:
        ok, _ = keyword_sanity_check("Doritos, Ruffles, SunChips", self.ruffles)
        self.assertTrue(ok)

    def test_null_offer_fails(self) -> None:
        ok, reason = keyword_sanity_check(None, self.ruffles)
        self.assertFalse(ok)
        self.assertIn("null", reason.lower())

    def test_lindt_truffle_blocked(self) -> None:
        ok, reason = keyword_sanity_check(
            "Lindt Gourmet Truffles Select varieties.", self.ruffles
        )
        self.assertFalse(ok)
        self.assertIn("keep_separate_from", reason)

    def test_lindor_truffles_blocked(self) -> None:
        ok, reason = keyword_sanity_check("LINDOR Truffles 5.1 oz", self.ruffles)
        self.assertFalse(ok)

    def test_chocolate_truffles_blocked(self) -> None:
        ok, reason = keyword_sanity_check("Ferrero Rocher chocolate truffles", self.ruffles)
        self.assertFalse(ok)

    def test_ruffles_word_boundary(self) -> None:
        """\\bRuffles\\b must NOT match Truffles (substring)."""
        ok, reason = keyword_sanity_check(
            "Lindt Truffles $11.99", self.ruffles
        )
        # Should fail because "Lindt Truffles" is in keep_separate_from, but
        # the include tokens check also matters, the key thing is it's not a pass.
        self.assertFalse(ok)

    def test_unrelated_product_fails_keyword(self) -> None:
        family = _make_family(
            canonical_name="Häagen-Dazs ice cream pints",
            include=("Häagen-Dazs pint", "Haagen Dazs ice cream"),
            keep_separate_from=("Cold Brew Coffee", "Nescafé"),
        )
        ok, reason = keyword_sanity_check("SToK Cold Brew Coffee 13.7 oz.", family)
        self.assertFalse(ok)

    def test_butter_peanut_butter_blocked(self) -> None:
        family = _make_family(
            canonical_name="Butter",
            include=("Lucerne butter 16 oz", "Challenge butter 16 oz"),
            keep_separate_from=("peanut butter", "Skippy", "Jif"),
        )
        ok, reason = keyword_sanity_check("Skippy Peanut Butter", family)
        self.assertFalse(ok)

    def test_mango_habanero_chicken_blocked(self) -> None:
        family = _make_family(
            canonical_name="Mangoes",
            include=("mango", "mangoes"),
            keep_separate_from=("habanero", "chicken"),
        )
        ok, reason = keyword_sanity_check("Mango Habanero Chicken 8-pc.", family)
        self.assertFalse(ok)

    def test_cereal_chex_mix_blocked(self) -> None:
        family = _make_family(
            canonical_name="General Mills cereal",
            include=("Chex cereal", "Cheerios", "General Mills cereal"),
            keep_separate_from=("Chex Mix", "Rold Gold"),
        )
        ok, reason = keyword_sanity_check(
            "Lay's Party Size Potato Chips or Kettle Cooked Chips or Rold Gold Selects or Chex Mix Family Size",
            family,
        )
        self.assertFalse(ok)


class TestPriceOutlierCheck(unittest.TestCase):
    def test_normal_price_passes(self) -> None:
        ok, _ = price_outlier_check(2.99, [2.49, 2.99, 3.29, 2.79], None)
        self.assertTrue(ok)

    def test_baseline_outlier_high(self) -> None:
        ok, reason = price_outlier_check(10.0, [2.0, 2.5, 2.0, 3.0], None)
        self.assertFalse(ok)
        self.assertIn("median baseline", reason)

    def test_prior_week_spike(self) -> None:
        # prior_price=2.0, new price=9.0 → 9.0 > 3.0× prior (6.0); all_prices median=3.0 → also > 2.0× (6.0)
        # Either baseline or prior-week check can fire; just ensure it fails.
        ok, reason = price_outlier_check(9.0, [3.0, 3.0, 3.0, 9.0], 2.0)
        self.assertFalse(ok)
        # Use prices where only prior-week fires (high median won't trigger baseline):
        ok2, reason2 = price_outlier_check(9.0, [8.5, 9.0, 8.0, 9.0], 2.0)
        self.assertFalse(ok2)
        self.assertIn("prior week", reason2)

    def test_prior_week_dive(self) -> None:
        ok, reason = price_outlier_check(0.5, [2.0, 2.5, 3.0, 0.5], 2.0)
        self.assertFalse(ok)
        self.assertIn("prior week", reason)

    def test_no_prior_week_no_outlier(self) -> None:
        ok, _ = price_outlier_check(5.0, [5.0], None)
        self.assertTrue(ok)

    def test_single_price_no_baseline(self) -> None:
        """Single observation → no baseline → only prior-week check applies."""
        ok, _ = price_outlier_check(99.0, [99.0], None)
        self.assertTrue(ok)

    def test_median_ignores_zero(self) -> None:
        baseline = _compute_median_baseline([0.0, 2.49, 2.99, 0.0])
        self.assertAlmostEqual(baseline, 2.74, places=1)


class TestPerLbCheck(unittest.TestCase):
    def test_non_per_lb_family_passes(self) -> None:
        family = _make_family(subtitle="regular bags, roughly 5–13 oz")
        ok, _ = per_lb_check(3.99, family)
        self.assertTrue(ok)

    def test_per_lb_normal_price_passes(self) -> None:
        family = _make_family(subtitle="per lb")
        ok, _ = per_lb_check(3.99, family)
        self.assertTrue(ok)

    def test_per_lb_too_low(self) -> None:
        family = _make_family(subtitle="per lb")
        ok, reason = per_lb_check(0.10, family)
        self.assertFalse(ok)
        self.assertIn("minimum", reason)

    def test_per_lb_too_high(self) -> None:
        family = _make_family(subtitle="per lb")
        ok, reason = per_lb_check(55.0, family)
        self.assertFalse(ok)
        self.assertIn("maximum", reason)


class TestFridayMultibuySuspect(unittest.TestCase):
    def setUp(self) -> None:
        self.kettle = _make_family(
            family_id="kettle_brand_chips",
            canonical_name="Kettle Brand potato chips",
            include=("Kettle Brand Chips",),
            category="chips_salty_snacks",
        )

    def test_april_style_five_dollar_trap(self) -> None:
        entry = {
            "price": 5.0,
            "availabilityType": "friday_only",
            "promoNote": "Member Price",
            "offerText": "Kettle Brand Potato Chips 6-8.5 oz",
        }
        ok, reason = friday_multibuy_suspect_check(entry, self.kettle)
        self.assertFalse(ok)
        self.assertIn("unnormalized", reason)

    def test_normalized_2_for_5_passes(self) -> None:
        entry = {
            "price": 2.5,
            "availabilityType": "friday_only",
            "promoNote": "2 for $5 Friday April 3rd",
            "offerText": "Kettle Brand Potato Chips",
        }
        ok, _ = friday_multibuy_suspect_check(entry, self.kettle)
        self.assertTrue(ok)

    def test_five_dollar_with_n_for_in_promo_passes(self) -> None:
        # Odd residual $5 with wording still present — not this trap.
        entry = {
            "price": 5.0,
            "availabilityType": "friday_only",
            "promoNote": "2 for $5 Member Price",
            "offerText": "Kettle Brand Potato Chips",
        }
        ok, _ = friday_multibuy_suspect_check(entry, self.kettle)
        self.assertTrue(ok)

    def test_non_snack_friday_five_passes(self) -> None:
        meat = _make_family(
            canonical_name="Ribs",
            include=("Pork Ribs",),
            category="meat_seafood",
        )
        entry = {
            "price": 5.0,
            "availabilityType": "friday_only",
            "promoNote": "Member Price",
            "offerText": "Pork Ribs",
        }
        ok, _ = friday_multibuy_suspect_check(entry, meat)
        self.assertTrue(ok)


class TestParsePricesTs(unittest.TestCase):
    def test_parses_valid_ts(self) -> None:
        ts_content = """\
export const WEEKLY_AD_PRICES: Record<
  string,
  Record<string, any>
> = {
  "ruffles_regular_bags": {
    "2026-05-06": {
      "price": 2.99,
      "offerText": "Ruffles",
      "confidence": "high",
      "availabilityType": "full_week",
      "promoNote": null
    }
  }
};
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ts", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(ts_content)
            tmp = Path(fh.name)

        try:
            result = parse_prices_ts(tmp)
            self.assertIn("ruffles_regular_bags", result)
            entry = result["ruffles_regular_bags"]["2026-05-06"]
            self.assertAlmostEqual(entry["price"], 2.99)
            self.assertEqual(entry["offerText"], "Ruffles")
            self.assertIsNone(entry["promoNote"])
        finally:
            tmp.unlink()


class TestValidateFeed(unittest.TestCase):
    def test_clean_data_no_flags(self) -> None:
        family = _make_family(
            family_id="test_chips",
            canonical_name="Test Chips",
            include=("Test Chips Original",),
        )
        prices = {
            "test_chips": {
                "2026-05-06": {
                    "price": 2.99,
                    "offerText": "Test Chips Original",
                    "confidence": "high",
                    "availabilityType": "full_week",
                    "promoNote": None,
                }
            }
        }
        rows = validate_feed(prices, {"test_chips": family}, "safeway")
        self.assertEqual(rows, [])

    def test_false_match_flagged(self) -> None:
        family = _make_family(
            family_id="ruffles_test",
            canonical_name="Ruffles",
            include=("Ruffles Original",),
            keep_separate_from=("Lindt", "Gourmet Truffles"),
        )
        prices = {
            "ruffles_test": {
                "2026-05-06": {
                    "price": 11.99,
                    "offerText": "Lindt Gourmet Truffles Select varieties.",
                    "confidence": "high",
                    "availabilityType": "full_week",
                    "promoNote": None,
                }
            }
        }
        rows = validate_feed(prices, {"ruffles_test": family}, "safeway")
        self.assertEqual(len(rows), 1)
        self.assertIn("keyword/FAIL", rows[0]["reason"])

    def test_null_price_skipped(self) -> None:
        family = _make_family(include=("Test Chips",))
        prices = {
            "test_family": {
                "2026-05-06": {
                    "price": None,
                    "offerText": None,
                    "confidence": None,
                    "availabilityType": None,
                    "promoNote": None,
                }
            }
        }
        rows = validate_feed(prices, {"test_family": family}, "safeway")
        self.assertEqual(rows, [])

    def test_outlier_flagged(self) -> None:
        family = _make_family(include=("Test Chips",))
        prices = {
            "test_family": {
                "2026-05-06": {
                    "price": 2.0,
                    "offerText": "Test Chips",
                    "confidence": "medium",
                    "availabilityType": None,
                    "promoNote": None,
                },
                "2026-05-13": {
                    "price": 2.0,
                    "offerText": "Test Chips",
                    "confidence": "medium",
                    "availabilityType": None,
                    "promoNote": None,
                },
                "2026-05-20": {
                    "price": 20.0,
                    "offerText": "Test Chips",
                    "confidence": "medium",
                    "availabilityType": None,
                    "promoNote": None,
                },
            }
        }
        rows = validate_feed(prices, {"test_family": family}, "safeway")
        flagged_weeks = [r["week"] for r in rows]
        self.assertIn("2026-05-20", flagged_weeks)


class TestRufflesLindtIntegration(unittest.TestCase):
    """Integration test using live YAML for the Ruffles/Lindt scenario."""

    def test_ruffles_lindt_truffle_excluded(self) -> None:
        from price_tracker.canonical_families import load_families

        families = {f.id: f for f in load_families()}
        ruffles = families.get("ruffles_regular_bags")
        self.assertIsNotNone(ruffles)

        lindt_offers = [
            "Lindt Gourmet Truffles Select varieties.",
            "LINDOR Truffles 5.1 oz",
            "Lindt Excellence Chocolate Bars 3.5 oz",
            "chocolate truffles assorted",
        ]
        for offer in lindt_offers:
            ok, reason = keyword_sanity_check(offer, ruffles)
            self.assertFalse(
                ok,
                msg=f"Expected {offer!r} to fail keyword check for ruffles, but passed",
            )

    def test_ruffles_chip_offers_pass(self) -> None:
        from price_tracker.canonical_families import load_families

        families = {f.id: f for f in load_families()}
        ruffles = families.get("ruffles_regular_bags")
        self.assertIsNotNone(ruffles)

        chip_offers = [
            "Ruffles Original",
            "Ruffles Cheddar & Sour Cream",
            "Doritos, Ruffles, SunChips",
            "Ruffles potato chips 8.5 oz",
        ]
        for offer in chip_offers:
            ok, _ = keyword_sanity_check(offer, ruffles)
            self.assertTrue(
                ok,
                msg=f"Expected {offer!r} to pass keyword check for ruffles",
            )


if __name__ == "__main__":
    unittest.main()
