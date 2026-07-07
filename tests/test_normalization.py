"""Normalization rule tests for YAML tracker families."""

from __future__ import annotations

import unittest

from price_tracker.normalization import (
    _buy_x_get_y_unit_price,
    normalize_per_bar,
    normalize_per_cup,
    normalize_per_dozen,
    normalize_per_lb,
    normalize_strawberries_per_lb,
    base_normalize_unit_price,
)


def row(
    price: str,
    text: str = "",
    *,
    basis: str = "",
    size_min: str = "",
    unit: str = "",
) -> dict[str, str]:
    return {
        "advertised_price": price,
        "split_product_text": text,
        "raw_offer_text": text,
        "promo_text": text,
        "price_basis": basis,
        "package_size_min": size_min,
        "package_unit": unit,
    }


class TestNormalization(unittest.TestCase):
    def test_strawberries_1lb(self) -> None:
        result = normalize_strawberries_per_lb(row("$3.99", "strawberries 1 lb"))
        self.assertEqual(result, 3.99)

    def test_strawberries_2lb(self) -> None:
        result = normalize_strawberries_per_lb(row("$5.98", "strawberries 2 lb"))
        self.assertEqual(result, 2.99)

    def test_grapes_per_lb(self) -> None:
        result = normalize_per_lb(row("$1.99", "seedless grapes per lb"))
        self.assertEqual(result, 1.99)

    def test_eggs_18_to_dozen(self) -> None:
        result = normalize_per_dozen(row("$8.97", "large eggs 18 ct"))
        self.assertAlmostEqual(result or 0, 5.98, places=2)

    def test_chobani_4pack_per_cup(self) -> None:
        result = normalize_per_cup(row("$4.99", "chobani greek yogurt 4-5.3 oz cups 4 pk"))
        self.assertIsNotNone(result)
        self.assertLess(result or 99, 5.0)

    def test_quest_bar_multipack(self) -> None:
        result = normalize_per_bar(row("$8.99", "quest bars 4 ct"))
        self.assertAlmostEqual(result or 0, 2.25, places=2)

    def test_chicken_breast_per_lb(self) -> None:
        result = normalize_per_lb(row("$4.99", "boneless skinless chicken breast per lb"))
        self.assertEqual(result, 4.99)

    def test_b2g3f_coca_cola_12pack(self) -> None:
        promo = "BUY 2, GET 3 FREE WHEN YOU BUY 5 MEMBER PRICE"
        deal_row = row(
            "12.99",
            promo,
            basis="bogo",
        )
        self.assertEqual(base_normalize_unit_price(deal_row), 5.2)
        self.assertAlmostEqual(
            _buy_x_get_y_unit_price(deal_row, 12.99) or 0,
            5.196,
            places=2,
        )


class TestMatcherSeparation(unittest.TestCase):
    """Smoke tests that YAML exclude patterns keep known families separate."""

    def test_soda_families_distinct(self) -> None:
        from price_tracker.canonical_families import family_by_id

        coke = family_by_id()["coca_cola_12packs"]
        pepsi = family_by_id()["pepsi_12packs"]
        self.assertIn("pepsi", " ".join(coke.keep_separate_from).lower())
        self.assertIn("coca-cola", " ".join(pepsi.keep_separate_from).lower())

    def test_lays_vs_kettle(self) -> None:
        from price_tracker.canonical_families import family_by_id

        lays = family_by_id()["lays_potato_chips_regular"]
        kettle = family_by_id()["kettle_brand_chips"]
        self.assertTrue(
            any("kettle" in item.lower() for item in lays.keep_separate_from)
        )
        self.assertTrue(
            any("lay" in item.lower() for item in kettle.keep_separate_from)
        )

    def test_cheetos_vs_party(self) -> None:
        from price_tracker.canonical_families import family_by_id

        regular = family_by_id()["cheetos_regular_bags"]
        party = family_by_id()["cheetos_party_size"]
        self.assertIn("party size", " ".join(regular.keep_separate_from).lower())
        self.assertIn("6.5", " ".join(party.keep_separate_from).lower())

    def test_quest_vs_clif(self) -> None:
        from price_tracker.canonical_families import family_by_id

        quest = family_by_id()["quest_bars"]
        clif = family_by_id()["clif_bars"]
        self.assertIn("clif", " ".join(quest.keep_separate_from).lower())
        self.assertIn("quest", " ".join(clif.keep_separate_from).lower())

    def test_chicken_breast_vs_thigh(self) -> None:
        from price_tracker.canonical_families import family_by_id

        breast = family_by_id()["chicken_breast_per_lb"]
        thigh = family_by_id()["chicken_thigh_per_lb"]
        self.assertIn("thigh", " ".join(breast.keep_separate_from).lower())
        self.assertIn("breast", " ".join(thigh.keep_separate_from).lower())


if __name__ == "__main__":
    unittest.main()
