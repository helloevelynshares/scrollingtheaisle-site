"""Regression tests for canonical weekly ad match eligibility."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from price_tracker.canonical_families import load_families  # noqa: E402
from price_tracker.canonical_match_eligibility import (  # noqa: E402
    EligibilityIndex,
    evaluate_canonical_match,
    load_match_rules,
    merge_family_yaml_rules,
)


def _row(
    text: str,
    price: str = "4.99",
    *,
    package_text: str = "",
) -> dict[str, str]:
    return {
        "split_product_text": text,
        "raw_offer_text": text,
        "promo_text": "Member Price",
        "advertised_price": price,
        "price_basis": "each",
        "package_unit": "each",
        "package_text": package_text,
    }


class TestCanonicalMatchEligibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()
        cls.index = EligibilityIndex()

    def test_smoked_salmon_rejected_for_fresh_salmon_family(self) -> None:
        family = self.families["salmon"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Acme Togarashi or Nova Smoked Salmon 3 oz"),
            family,
            rules=rules,
            keyword_confidence="high",
            historical_low=6.99,
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "smoked_salmon")
        self.assertIn("smoked", result.hard_negative_hits)
        self.assertIn("smoked", (result.reject_reason or "").lower())

    def test_fresh_atlantic_fillets_accepted(self) -> None:
        family = self.families["salmon"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Fresh Atlantic Salmon Fillets Farm Raised", price="8.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.ad_product_type, "fresh_salmon_fillets")

    def test_2_liter_soda_rejected_for_coca_cola_12packs(self) -> None:
        family = self.families["coca_cola_12packs"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Coca-Cola 2 Liter Bottle", price="1.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "2_liter_bottle")

    def test_12_pack_soda_accepted_for_coca_cola_12packs(self) -> None:
        family = self.families["coca_cola_12packs"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Coca-Cola 12-Pack 12 fl oz cans", price="5.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.ad_product_type, "12_pack_cans")
        self.assertEqual(result.reason_code, "none")
        self.assertIn("package_count", result.present_attributes)
        self.assertIn("container_type", result.present_attributes)
        self.assertEqual(result.missing_attributes, [])

    def test_12_pack_bottles_rejected_for_coca_cola_cans_tracker(self) -> None:
        family = self.families["coca_cola_12packs"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Coca-Cola 12-Pack Bottles", price="5.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertTrue(
            any("bottle" in h for h in result.hard_negative_hits),
            result.hard_negative_hits,
        )
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_butter_spread_rejected_butter_sticks_accepted(self) -> None:
        family = self.families["butter_16oz"]
        rules = merge_family_yaml_rules(family, self.rules)

        spread = evaluate_canonical_match(
            _row(
                "Land O Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties.",
                price="3.49",
            ),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(spread.match_decision, "rejected")
        self.assertEqual(spread.ad_product_type, "butter_spread")

        sticks = evaluate_canonical_match(
            _row("Challenge Butter Quarters 16 oz", price="4.99"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(sticks.match_decision, "accepted")
        self.assertEqual(sticks.ad_product_type, "butter_sticks")


class TestEggsDozenNormalized(unittest.TestCase):
    """Lucerne large eggs 12-count — never candy / premium brands / 18-count."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()
        cls.family = cls.families["eggs_dozen_normalized"]
        cls.merged = merge_family_yaml_rules(cls.family, cls.rules)

    def _evaluate(self, text: str, price: str, package_text: str = "") -> object:
        return evaluate_canonical_match(
            _row(text, price=price, package_text=package_text),
            self.family,
            rules=self.merged,
            keyword_confidence="high",
        )

    def test_reject_chocolate_eggs(self) -> None:
        result = self._evaluate("Russell Stover Chocolate Eggs", "3.00", package_text="1 oz")
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "candy_eggs")

    def test_reject_reeses_eggs(self) -> None:
        result = self._evaluate("Reese’s Eggs", "4.49", package_text="7-10 oz.")
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "candy_eggs")

    def test_accept_lucerne_large_eggs_with_pack_in_package_text(self) -> None:
        result = self._evaluate("Lucerne Large Eggs", "2.49", package_text="12 ct")
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.ad_product_type, "eggs_dozen")

    def test_reject_eggland_best_not_lucerne(self) -> None:
        result = self._evaluate("Eggland's Best Large Eggs 12 ct", "7.00")
        self.assertEqual(result.match_decision, "rejected")
        self.assertIn("eggland", result.hard_negative_hits)
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_reject_happy_egg_not_lucerne(self) -> None:
        result = self._evaluate("Happy Egg Free Range Eggs", "7.49", package_text="12 ct")
        self.assertEqual(result.match_decision, "rejected")
        self.assertIn("happy egg", result.hard_negative_hits)
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_reject_vital_farms_pasture_raised(self) -> None:
        result = self._evaluate(
            "Vital Farms Pasture Raised Large Eggs", "12.99", package_text="12 ct."
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertTrue(
            {"vital farms", "pasture raised"} & set(result.hard_negative_hits),
            result.hard_negative_hits,
        )
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_lucerne_18ct_rejected_from_dozen_family(self) -> None:
        result = self._evaluate(
            "Lucerne Cage Free Eggs Grade AA, 18-ct.", "2.99", package_text="18-ct."
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertIn("18-ct", result.hard_negative_hits)
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_lucerne_18ct_accepted_on_18_family(self) -> None:
        family_18 = self.families["lucerne_eggs_18"]
        merged_18 = merge_family_yaml_rules(family_18, self.rules)
        result = evaluate_canonical_match(
            _row(
                "Lucerne Cage Free Eggs Grade AA, 18-ct.",
                price="2.99",
                package_text="18-ct.",
            ),
            family_18,
            rules=merged_18,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.ad_product_type, "eggs_dozen")


class TestBerries6oz(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()
        cls.family = cls.families["berries_6oz"]
        cls.merged = merge_family_yaml_rules(cls.family, cls.rules)

    def test_accept_blackberry_with_6oz_in_package_text(self) -> None:
        result = evaluate_canonical_match(
            _row("Blackberries", price="5.00", package_text="6 oz."),
            self.family,
            rules=self.merged,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.ad_product_type, "berries_6oz_clamshell")

    def test_manual_review_bare_blueberry_without_size(self) -> None:
        result = evaluate_canonical_match(
            _row("Blueberries", price="2.50"),
            self.family,
            rules=self.merged,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "manual_review")

    def test_accept_blackberry_6oz_even_if_package_mentions_pint(self) -> None:
        # Mixed-deal package labels sometimes say "Pint, 6 oz" for a group that
        # includes both pints and 6 oz clamshells. Product text wins.
        result = evaluate_canonical_match(
            _row("Blackberries 6 oz", price="2.99", package_text="Pint, 6 oz"),
            self.family,
            rules=self.merged,
            keyword_confidence="medium",
        )
        self.assertEqual(result.match_decision, "accepted")


class TestNabiscoFamilySizeSnackCrackers(unittest.TestCase):
    """Wheat Thins / Triscuit / Chicken in a Biskit family-size snack crackers."""

    DISPLAY_NAME = "Wheat Thins, Triscuit & Chicken in a Biskit"
    SUBTITLE = "family size, 11.5–14 oz"

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()

    def _evaluate(self, text: str, price: str, keyword_confidence: str = "medium"):
        family = self.families["nabisco_snack_crackers"]
        rules = merge_family_yaml_rules(family, self.rules)
        return evaluate_canonical_match(
            _row(text, price=price),
            family,
            rules=rules,
            keyword_confidence=keyword_confidence,
        )

    def test_1_accept_family_size_snack_crackers(self) -> None:
        result = self._evaluate(
            "Nabisco Snack Crackers Family Size 11.5–14 oz",
            price="3.49",
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.display_name, self.DISPLAY_NAME)
        self.assertEqual(result.subtitle, self.SUBTITLE)
        self.assertEqual(result.manufacturer_family, "Nabisco")
        self.assertEqual(result.package_type, "family_size_box")
        self.assertIn("Wheat Thins", result.allowed_product_lines)
        self.assertIn("Triscuit", result.allowed_product_lines)
        self.assertIn("Chicken in a Biskit", result.allowed_product_lines)
        self.assertTrue(result.eligible_item_examples)

    def test_1b_accept_real_safeway_offer(self) -> None:
        # The live 2026-07-08 Safeway offer text must still ACCEPT.
        result = self._evaluate(
            "Nabisco Family Size Snack Crackers 10-14 oz",
            price="3.49",
            keyword_confidence="medium",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.display_name, self.DISPLAY_NAME)

    def test_2_reject_chips_ahoy(self) -> None:
        result = self._evaluate(
            "Nabisco Chips Ahoy! Cookies 9.5–13 oz", price="3.49", keyword_confidence="high"
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "chips_ahoy")

    def test_3_reject_oreo(self) -> None:
        result = self._evaluate(
            "Oreo Family Size Cookies 10–18 oz", price="3.99", keyword_confidence="high"
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "oreo")

    def test_4_reject_ritz(self) -> None:
        result = self._evaluate(
            "Ritz Crackers 8.8–13.7 oz", price="2.49", keyword_confidence="high"
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "ritz_crackers")

    def test_5_reject_single_serve_multipack(self) -> None:
        result = self._evaluate(
            "Nabisco Single Serve Snacks 10 pack", price="3.99", keyword_confidence="high"
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "single_serve_snack_multipack")
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_6_manual_review_bare_nabisco_snack_crackers(self) -> None:
        # No size, no eligible items → manual review, no graph update.
        result = self._evaluate(
            "Nabisco Snack Crackers", price="2.49", keyword_confidence="high"
        )
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("confirmation", result.missing_attributes)
        self.assertEqual(result.reason_code, "insufficient_information")

    def test_7_reject_regular_size_band(self) -> None:
        result = self._evaluate(
            "Nabisco Snack Crackers 3.5 to 9.1 oz",
            price="1.99",
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")


class TestNabiscoRegularSizeSnackCrackers(unittest.TestCase):
    """Wheat Thins / Triscuit / Chicken in a Biskit regular-size (3.5–9.1 oz)."""

    DISPLAY_NAME = "Wheat Thins, Triscuit & Chicken in a Biskit — regular size"
    SUBTITLE = "regular size, 3.5–9.1 oz"

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()

    def _evaluate(self, text: str, price: str, keyword_confidence: str = "medium"):
        family = self.families["nabisco_snack_crackers_regular"]
        rules = merge_family_yaml_rules(family, self.rules)
        return evaluate_canonical_match(
            _row(text, price=price),
            family,
            rules=rules,
            keyword_confidence=keyword_confidence,
        )

    def test_1_accept_nabisco_snack_crackers_band(self) -> None:
        result = self._evaluate(
            "Nabisco Snack Crackers 3.5 to 9.1 oz",
            price="1.99",
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.display_name, self.DISPLAY_NAME)
        self.assertEqual(result.subtitle, self.SUBTITLE)
        self.assertEqual(result.package_type, "regular_size_box")
        self.assertIn("Wheat Thins", result.allowed_product_lines)

    def test_1b_accept_jul29_split(self) -> None:
        result = self._evaluate(
            "Nabisco Snack Crackers 3.5 to 9.1 oz.",
            price="1.99",
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")

    def test_2_accept_wheat_thins_regular(self) -> None:
        result = self._evaluate(
            "Wheat Thins 8 to 9.1 oz",
            price="2.49",
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.ad_product_type, "wheat_thins")

    def test_3_reject_family_size(self) -> None:
        result = self._evaluate(
            "Nabisco Family Size Snack Crackers 10-14 oz",
            price="3.49",
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")

    def test_4_reject_chips_ahoy(self) -> None:
        result = self._evaluate(
            "Nabisco Chips Ahoy! Cookies 7-13 oz",
            price="1.99",
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")

    def test_5_manual_review_bare_no_size(self) -> None:
        result = self._evaluate(
            "Nabisco Snack Crackers", price="2.49", keyword_confidence="high"
        )
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("confirmation", result.missing_attributes)


class TestGoldfishBagsVsTubs(unittest.TestCase):
    """Regular 4–8 oz Goldfish bags must never match 30 oz tubs."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()
        cls.family = cls.families["goldfish_bags"]
        cls.merged = merge_family_yaml_rules(cls.family, cls.rules)

    def test_reject_30oz_tub_safeway_2026_05_06(self) -> None:
        # Exact failure: split name dropped the size; package carried "30 oz".
        result = evaluate_canonical_match(
            _row(
                "Goldfish Crackers",
                price="7.99",
                package_text="30 oz",
            ),
            self.family,
            rules=self.merged,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertEqual(result.ad_product_type, "goldfish_tub")

    def test_reject_30oz_in_raw_offer_text(self) -> None:
        result = evaluate_canonical_match(
            {
                "split_product_text": "Goldfish Crackers",
                "raw_offer_text": "Goldfish Crackers 30 oz. 7.99 ea",
                "promo_text": "",
                "advertised_price": "7.99",
                "price_basis": "each",
                "package_unit": "each",
                "package_text": "30 oz",
            },
            self.family,
            rules=self.merged,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")

    def test_accept_6_1_to_8_oz_bag(self) -> None:
        result = evaluate_canonical_match(
            _row(
                "Pepperidge Farm Goldfish Crackers",
                price="3.49",
                package_text="6.1-8 oz",
            ),
            self.family,
            rules=self.merged,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.ad_product_type, "goldfish_crackers")

    def test_accept_5_9_to_8_oz_bag(self) -> None:
        result = evaluate_canonical_match(
            _row("Pepperidge Farm Goldfish 5.9-8 oz", price="1.88"),
            self.family,
            rules=self.merged,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")

    def test_accept_crackers_or_crisps_with_size(self) -> None:
        # Mix & Match "Crackers or Crisps" with bag size → accepted (not stuck
        # in manual_review solely because of "or").
        result = evaluate_canonical_match(
            {
                "split_product_text": "Goldfish Crackers or Crisps 4 to 8-oz.",
                "raw_offer_text": "Goldfish Crackers or Crisps 4 to 8-oz. "
                "BUY 1 GET 1 FREE MEMBER PRICE",
                "promo_text": "BUY 1 GET 1 FREE EQUAL OR LESSER VALUE MEMBER PRICE",
                "advertised_price": "",
                "price_basis": "bogo",
                "package_unit": "each",
                "package_text": "4 to 8-oz.",
            },
            self.family,
            rules=self.merged,
            keyword_confidence="medium",
        )
        self.assertEqual(result.match_decision, "accepted", result.reject_reason)

    def test_manual_review_bare_goldfish_without_size(self) -> None:
        result = evaluate_canonical_match(
            _row("Goldfish Crackers", price="5.00"),
            self.family,
            rules=self.merged,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "manual_review")


class TestSaferAutoMatchGate(unittest.TestCase):
    """Abstain when required attributes are missing; reject brand/size conflicts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()
        cls.index = EligibilityIndex()

    def _eval(self, family_id: str, text: str, package: str = "") -> object:
        family = self.families[family_id]
        rules = merge_family_yaml_rules(family, self.rules)
        return evaluate_canonical_match(
            _row(text, package_text=package),
            family,
            rules=rules,
            keyword_confidence="high",
        )

    def test_coke_cans_without_count_needs_review(self) -> None:
        result = self._eval("coca_cola_12packs", "Coca-Cola cans")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("package_count", result.missing_attributes)
        self.assertEqual(result.reason_code, "missing_package_count")

    def test_coke_12pack_cans_accepted_with_present_attributes(self) -> None:
        result = self._eval("coca_cola_12packs", "Coca-Cola 12-Pack 12 fl oz cans")
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(set(result.present_attributes), {"package_count", "container_type"})
        self.assertEqual(result.missing_attributes, [])
        self.assertEqual(result.reason_code, "none")

    def test_bare_chobani_needs_review(self) -> None:
        result = self._eval("chobani_yogurt_per_cup", "Chobani Greek Yogurt")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("package_size", result.missing_attributes)
        self.assertEqual(result.reason_code, "missing_package_size")

    def test_chobani_tub_rejected_for_per_cup(self) -> None:
        result = self._eval(
            "chobani_yogurt_per_cup",
            "Chobani Greek Yogurt Tub",
            package="32 oz",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertTrue(
            any("tub" in h or "32" in h for h in result.hard_negative_hits),
            result.hard_negative_hits,
        )
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_chobani_tub_accepted_for_tub(self) -> None:
        result = self._eval(
            "chobani_yogurt_tub",
            "Chobani Greek Yogurt Tub",
            package="32 oz",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertIn("package_size", result.present_attributes)
        self.assertEqual(result.reason_code, "none")

    def test_miss_vickies_rejected_for_lays_kettle(self) -> None:
        result = self._eval(
            "lays_kettle_cooked",
            "Miss Vickie's Kettle Cooked Potato Chips Jalapeno - 7.5 OZ",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertTrue(
            any("miss vickie" in h for h in result.hard_negative_hits),
            result.hard_negative_hits,
        )
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_kettle_chips_without_brand_needs_review(self) -> None:
        result = self._eval("kettle_brand_chips", "Kettle Chips")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("brand", result.missing_attributes)
        self.assertEqual(result.reason_code, "missing_brand")

    def test_kettle_potato_chips_alias_still_accepted(self) -> None:
        result = self._eval("kettle_brand_chips", "Kettle Potato Chips")
        self.assertEqual(result.match_decision, "accepted")
        self.assertIn("brand", result.present_attributes)
        self.assertEqual(result.reason_code, "none")

    def test_butter_size_without_form_needs_review(self) -> None:
        result = self._eval("butter_16oz", "Land O Lakes Butter 16 oz")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("product_form", result.missing_attributes)
        self.assertEqual(result.reason_code, "ambiguous_product_variant")

    def test_bare_cheerios_needs_review(self) -> None:
        result = self._eval("general_mills_cereal_regular", "Cheerios")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("package_size", result.missing_attributes)
        self.assertEqual(result.reason_code, "missing_package_size")

    def test_bare_lays_potato_needs_review(self) -> None:
        result = self._eval("lays_potato_chips_regular", "Lay's Potato Chips")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("package_size", result.missing_attributes)
        self.assertEqual(result.reason_code, "missing_package_size")

    def test_waterloo_without_pack_needs_review(self) -> None:
        result = self._eval("waterloo_sparkling_water", "Waterloo Sparkling Water")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("package_count", result.missing_attributes)
        self.assertEqual(result.reason_code, "missing_package_count")

    def test_nature_valley_without_count_needs_review(self) -> None:
        result = self._eval("nature_valley_bars", "Nature Valley Crunchy Bars")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("package_count", result.missing_attributes)
        self.assertEqual(result.reason_code, "missing_package_count")


class TestPackageRangeEnforcement(unittest.TestCase):
    """allowed/disallowed package patterns must gate automatic matches."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()

    def _eval(self, family_id: str, text: str, package: str = "") -> object:
        family = self.families[family_id]
        rules = merge_family_yaml_rules(family, self.rules)
        return evaluate_canonical_match(
            _row(text, package_text=package),
            family,
            rules=rules,
            keyword_confidence="high",
        )

    def test_lays_kettle_regular_6_to_8_oz_accepted(self) -> None:
        result = self._eval(
            "lays_kettle_cooked",
            "Lay's Kettle Cooked Potato Chips",
            package="6 to 8 oz",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertEqual(result.reason_code, "none")

    def test_lays_kettle_regular_8_oz_accepted(self) -> None:
        result = self._eval(
            "lays_kettle_cooked",
            "Lay's Kettle Cooked Potato Chips",
            package="8 oz",
        )
        self.assertEqual(result.match_decision, "accepted")

    def test_lays_kettle_party_size_12_5_oz_rejected(self) -> None:
        result = self._eval(
            "lays_kettle_cooked",
            "Lay's Kettle Cooked Potato Chips",
            package="12.5 oz",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertTrue(result.hard_negative_hits or not result.package_type_match)
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")

    def test_lays_kettle_missing_size_manual_review_not_reject(self) -> None:
        result = self._eval("lays_kettle_cooked", "Lay's Kettle")
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("package_size", result.missing_attributes)
        self.assertEqual(result.reason_code, "missing_package_size")

    def test_general_mills_regular_eligible_size_accepted(self) -> None:
        result = self._eval("general_mills_cereal_regular", "Cheerios", package="8.9-12 oz")
        self.assertEqual(result.match_decision, "accepted")
        self.assertIn("package_size", result.present_attributes)
        self.assertEqual(result.reason_code, "none")

    def test_general_mills_family_size_rejected_from_regular(self) -> None:
        result = self._eval(
            "general_mills_cereal_regular",
            "General Mills Family Size Cereal",
            package="18 oz",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertTrue(
            any("family size" in h or "18" in h for h in result.hard_negative_hits),
            result.hard_negative_hits,
        )
        self.assertEqual(result.reason_code, "explicit_attribute_conflict")


class TestKeywordBoundarySafety(unittest.TestCase):
    """Short tokens must not match inside unrelated words."""

    def test_ct_does_not_match_inside_selected(self) -> None:
        from price_tracker.canonical_match_eligibility import _keyword_hits

        self.assertEqual(_keyword_hits("Nature Valley Selected varieties", ("ct",)), [])
        hits = _keyword_hits("Nature Valley Crunchy Bars 6 ct", ("6 ct", "ct"))
        self.assertEqual(hits, ["6 ct", "ct"])

    def test_cup_does_not_match_inside_occupied(self) -> None:
        from price_tracker.canonical_match_eligibility import _keyword_hits

        self.assertEqual(_keyword_hits("occupied yogurt aisle", ("cup", "cups")), [])
        self.assertEqual(_keyword_hits("Chobani yogurt cup", ("cup",)), ["cup"])

    def test_stick_does_not_match_inside_stickshift(self) -> None:
        from price_tracker.canonical_match_eligibility import _keyword_hits

        self.assertEqual(_keyword_hits("stickshift butter display", ("stick", "sticks")), [])
        self.assertEqual(_keyword_hits("butter sticks 16 oz", ("sticks",)), ["sticks"])

    def test_nature_valley_selected_does_not_satisfy_count_via_ct_substring(self) -> None:
        families = {f.id: f for f in load_families()}
        rules = load_match_rules()
        family = families["nature_valley_bars"]
        merged = merge_family_yaml_rules(family, rules)
        result = evaluate_canonical_match(
            _row("Nature Valley Crunchy Bars Selected varieties"),
            family,
            rules=merged,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "manual_review")
        self.assertIn("package_count", result.missing_attributes)


class TestMixedItemOfferAbstention(unittest.TestCase):
    """Combined ads must not auto-accept when package cues may belong to peers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()

    def test_mixed_cans_and_bottles_does_not_auto_accept_waterloo(self) -> None:
        family = self.families["waterloo_sparkling_water"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Waterloo Sparkling Water 12 pack cans or 8 pack bottles"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "manual_review")
        self.assertEqual(result.reason_code, "ambiguous_product_variant")
        self.assertIn("mixed-item", (result.reject_reason or "").lower())

    def test_coke_cans_or_two_liter_bottles_rejected_not_accepted(self) -> None:
        family = self.families["coca_cola_12packs"]
        rules = merge_family_yaml_rules(family, self.rules)
        result = evaluate_canonical_match(
            _row("Coca-Cola 12-Pack cans or 2 Liter bottles"),
            family,
            rules=rules,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "rejected")
        self.assertNotEqual(result.match_decision, "accepted")
        self.assertTrue(result.hard_negative_hits)


class TestLegacyAcceptanceWithoutEligibilityRules(unittest.TestCase):
    """Document current behavior: no rules ⇒ automatic accept on pattern match."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.families = {f.id: f for f in load_families()}
        cls.rules = load_match_rules()
        cls.index = EligibilityIndex()

    def test_legacy_auto_accept_when_no_eligibility_rules_configured(self) -> None:
        family_id = "doritos_5_13oz"
        self.assertIsNone(
            self.index.rules_for(family_id),
            f"{family_id} should still bypass the gate (no configured rules)",
        )
        family = self.families[family_id]
        merged = merge_family_yaml_rules(family, self.rules)
        self.assertIsNone(merged)
        result = evaluate_canonical_match(
            _row("Doritos Nacho Cheese Tortilla Chips", package_text="9 oz"),
            family,
            rules=None,
            keyword_confidence="high",
        )
        self.assertEqual(result.match_decision, "accepted")
        self.assertIn("No eligibility rules configured", result.match_reason)


if __name__ == "__main__":
    unittest.main()
