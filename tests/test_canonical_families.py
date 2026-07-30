"""Tests for data/canonical_tracker_families.yaml."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

import re

from price_tracker.canonical_families import (
    HOMEPAGE_SECTION_ORDER,
    family_by_id,
    load_families,
    phrase_to_pattern,
    validate_families,
)

ROOT = Path(__file__).resolve().parents[1]
YAML_PATH = ROOT / "data" / "canonical_tracker_families.yaml"
POPULAR_PATH = ROOT / "data" / "popular_this_week.yaml"


class TestCanonicalFamiliesYaml(unittest.TestCase):
    def test_yaml_file_exists(self) -> None:
        self.assertTrue(YAML_PATH.is_file())

    def test_families_load_without_errors(self) -> None:
        families = load_families()
        self.assertGreaterEqual(len(families), 50)

    def test_required_fields_and_sections(self) -> None:
        families = load_families()
        errors = validate_families(families)
        self.assertEqual(errors, [], msg="\n".join(errors))

    def test_no_duplicate_ids(self) -> None:
        families = load_families()
        ids = [family.id for family in families]
        self.assertEqual(len(ids), len(set(ids)))

    def test_homepage_sections_valid(self) -> None:
        families = load_families()
        valid = set(HOMEPAGE_SECTION_ORDER)
        for family in families:
            self.assertIn(family.homepage_section, valid)

    def test_drinks_section_is_fifth(self) -> None:
        self.assertEqual(HOMEPAGE_SECTION_ORDER[4], "drinks")

    def test_nabisco_family_size_snack_crackers_metadata(self) -> None:
        family = {f.id: f for f in load_families()}["nabisco_snack_crackers"]
        self.assertEqual(
            family.display_name, "Wheat Thins, Triscuit & Chicken in a Biskit"
        )
        self.assertEqual(
            family.canonical_tracker_family,
            "Wheat Thins, Triscuit & Chicken in a Biskit",
        )
        self.assertEqual(
            family.subtitle, "family size, 11.5–14 oz"
        )
        self.assertEqual(family.manufacturer_family, "Nabisco")
        self.assertEqual(family.package_type, "family_size_box")
        self.assertEqual(
            tuple(family.allowed_product_lines),
            ("Wheat Thins", "Triscuit", "Chicken in a Biskit"),
        )
        # Cookie / Ritz / single-serve lines must stay separate.
        joined = " ".join(family.keep_separate_from).lower()
        for term in ("oreo", "chips ahoy", "ritz", "single serve", "cookies"):
            self.assertIn(term, joined)
        self.assertIn("3.5-9.1", joined)

    def test_nabisco_regular_size_snack_crackers_metadata(self) -> None:
        family = {f.id: f for f in load_families()}["nabisco_snack_crackers_regular"]
        self.assertEqual(
            family.display_name,
            "Wheat Thins, Triscuit & Chicken in a Biskit — regular size",
        )
        self.assertEqual(family.subtitle, "regular size, 3.5–9.1 oz")
        self.assertEqual(family.package_type, "regular_size_box")
        self.assertEqual(
            tuple(family.allowed_product_lines),
            ("Wheat Thins", "Triscuit", "Chicken in a Biskit"),
        )
        joined_includes = " ".join(family.include).lower()
        self.assertIn("nabisco snack crackers", joined_includes)
        self.assertIn("chicken in a biskit", joined_includes)
        joined = " ".join(family.keep_separate_from).lower()
        for term in ("family size", "chips ahoy", "oreo", "ritz"):
            self.assertIn(term, joined)


class TestPopularThisWeek(unittest.TestCase):
    def test_popular_loads(self) -> None:
        self.assertTrue(POPULAR_PATH.is_file())
        with POPULAR_PATH.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        self.assertEqual(doc["week"], "2026-07-08")

    def test_popular_ids_resolve(self) -> None:
        families = load_families()
        known = {family.id for family in families}
        with POPULAR_PATH.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        unresolved: list[str] = []
        for store in ("safeway", "vons"):
            for entry in doc["stores"][store]:
                for family_id in entry["tracker_family_ids"]:
                    if family_id not in known:
                        unresolved.append(family_id)
        self.assertEqual(unresolved, [])

    def test_vons_has_no_shrimp(self) -> None:
        with POPULAR_PATH.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        vons_text = yaml.dump(doc["stores"]["vons"]).lower()
        self.assertNotIn("shrimp", vons_text)

    def test_multi_family_refs(self) -> None:
        with POPULAR_PATH.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        safeway_entries = doc["stores"]["safeway"]
        multi_family = [
            entry["tracker_family_ids"]
            for entry in safeway_entries
            if len(entry["tracker_family_ids"]) >= 2
        ]
        self.assertGreaterEqual(len(multi_family), 1)


class TestRobustPhraseMatching(unittest.TestCase):
    """Include phrases tolerate inserted marketing/size qualifiers ("Family
    Size", "Party Size", …) between words, WITHOUT bridging distinct products.
    """

    @staticmethod
    def _matches(phrase: str, text: str) -> bool:
        return bool(re.search(phrase_to_pattern(phrase), text.lower()))

    def test_inserted_qualifier_matches(self) -> None:
        # The exact regression that caused the Oreo/Nabisco 7/8 miss.
        self.assertTrue(
            self._matches("Nabisco snack crackers", "Nabisco Family Size Snack Crackers 10-14 oz")
        )
        self.assertTrue(
            self._matches("Oreo cookies", "Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz.")
        )
        self.assertTrue(self._matches("Wheat Thins", "Wheat Thins Family Size"))
        self.assertTrue(self._matches("Kettle Brand Chips", "Kettle Brand Chips Party Size"))

    def test_contiguous_still_matches(self) -> None:
        self.assertTrue(self._matches("Nabisco snack crackers", "Nabisco Snack Crackers"))
        self.assertTrue(self._matches("Oreo cookies", "Oreo Cookies"))

    def test_non_qualifier_word_does_not_bridge(self) -> None:
        # A non-qualifier word between brand and product must NOT match, this is
        # what stops the gap from bridging two different products.
        self.assertFalse(
            self._matches("Nabisco snack crackers", "Nabisco Oreo Cookies and Snack Crackers")
        )
        self.assertFalse(self._matches("Oreo cookies", "Oreo or Chips Ahoy! Cookies"))

    def test_substring_guard_preserved(self) -> None:
        self.assertFalse(self._matches("Ruffles", "Lindt Gourmet Truffles"))
        self.assertTrue(self._matches("Ruffles", "Ruffles Potato Chips"))

    def test_keep_separate_still_excludes(self) -> None:
        # Robust include matching must not defeat keep_separate_from protection.
        oreo = family_by_id()["oreo_family_size"]
        combined = "nabisco family size oreo cookies or chips ahoy! cookies"
        include_hit = any(re.search(p, combined) for p in oreo.patterns)
        exclude_hit = any(re.search(p, combined) for p in oreo.exclude_patterns)
        self.assertTrue(include_hit, "oreo include should still fire on combined tile")
        self.assertTrue(exclude_hit, "chips ahoy keep_separate_from should still exclude")

    def test_family_level_nabisco_family_size(self) -> None:
        crackers = family_by_id()["nabisco_snack_crackers"]
        text = "nabisco family size snack crackers 10-14 oz"
        self.assertTrue(any(re.search(p, text) for p in crackers.patterns))
        self.assertFalse(any(re.search(p, text) for p in crackers.exclude_patterns))


class TestKettleBrandChipsMatcher(unittest.TestCase):
    """Safeway/Vons flyers often omit 'Brand' from Kettle titles (Jul 22 miss)."""

    @classmethod
    def setUpClass(cls) -> None:
        import sys

        scripts = str(ROOT / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        from generate_weekly_ad_prices import matches  # noqa: WPS433
        from price_tracker.yaml_matchers import build_yaml_matchers  # noqa: WPS433

        cls.matches = staticmethod(matches)
        cls.matcher = next(m for m in build_yaml_matchers() if m.canonical_id == "kettle_brand_chips")
        cls.family = family_by_id()["kettle_brand_chips"]

    @staticmethod
    def _row(title: str, package: str = "") -> dict[str, str]:
        return {
            "split_product_text": title,
            "raw_offer_text": title,
            "package_text": package,
            "advertised_price": "1.99",
            "price_basis": "each",
        }

    def test_yaml_has_brand_optional_includes(self) -> None:
        # Regression: if includes again require the literal word Brand, Jul-style
        # "Kettle Potato Chips" / "Kettle chips" titles stop matching.
        includes_lower = [p.lower() for p in self.family.include]
        self.assertTrue(
            any("brand" not in p and "kettle" in p and "chip" in p for p in includes_lower),
            "kettle_brand_chips must include Brand-optional flyer phrases",
        )
        self.assertIn("kettle potato chips", includes_lower)
        self.assertIn("kettle chips", includes_lower)

    def test_flyer_titles_without_brand_match(self) -> None:
        for title in (
            "Kettle Potato Chips",
            "Kettle chips",
            "Kettle Chips",
            "Kettle Brand Potato Chips 6.5 to 8.5 oz",
            "Kettle Brand Chips",
        ):
            with self.subTest(title=title):
                self.assertTrue(self.matches(self._row(title), self.matcher))

    def test_excludes_cape_cod_lays_party_and_mix_tiles(self) -> None:
        for title in (
            "Cape Cod Kettle Chips",
            "Cape Cod Kettle Cooked Potato Chips",
            "Lay's Kettle Cooked Chips",
            "Kettle Brand Chips Party Size",
            "SunChips, Lay's Potato Chips, Kettle Brand Potato Chips",
            "Chips Ahoy, Nabisco, Triscuit, Kettle Brand Chips",
        ):
            with self.subTest(title=title):
                self.assertFalse(
                    self.matches(self._row(title), self.matcher),
                    f"should not match: {title}",
                )


class TestHighlightCoverageFamilies(unittest.TestCase):
    """High-confidence families added from Safeway transcript highlight inventory."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.by_id = {f.id: f for f in load_families()}

    def test_new_family_ids_present(self) -> None:
        expected = {
            "cape_cod_chips",
            "smartfood_popcorn",
            "pringles",
            "snyders_pretzels",
            "frito_lay_multipack_chips",
            "pop_tarts",
            "kellogg_breakfast_bars",
            "betty_crocker_fruit_snacks",
            "waterloo_sparkling_water",
            "bell_peppers",
            "chicken_wings_per_lb",
            "beef_short_ribs_per_lb",
            "pork_spare_ribs_per_lb",
            "oscar_mayer_hot_dogs",
            "cake_mix",
        }
        self.assertTrue(expected.issubset(self.by_id))
        self.assertNotIn("shrimp_16oz", self.by_id)

    def test_frito_multipack_legacy_maps_to_itself(self) -> None:
        from price_tracker.canonical_families import LEGACY_CANONICAL_TO_FAMILY

        self.assertEqual(
            LEGACY_CANONICAL_TO_FAMILY["frito_lay_multipack_chips"],
            "frito_lay_multipack_chips",
        )

    def test_cape_cod_not_confused_with_kettle_brand(self) -> None:
        cape = self.by_id["cape_cod_chips"]
        kettle = self.by_id["kettle_brand_chips"]
        joined_sep = " ".join(kettle.keep_separate_from).lower()
        self.assertIn("cape cod", joined_sep)
        self.assertTrue(any("cape cod" in p.lower() for p in cape.include))

    def test_pack_total_normalization_for_multipacks(self) -> None:
        for fid in (
            "waterloo_sparkling_water",
            "frito_lay_multipack_chips",
        ):
            self.assertEqual(self.by_id[fid].normalization, "pack_total")


if __name__ == "__main__":
    unittest.main()
