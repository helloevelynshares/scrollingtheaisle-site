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
            family.subtitle, "Nabisco family-size snack crackers, 11.5–14 oz"
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
        # A non-qualifier word between brand and product must NOT match — this is
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


if __name__ == "__main__":
    unittest.main()
