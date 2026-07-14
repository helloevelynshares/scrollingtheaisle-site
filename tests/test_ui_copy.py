"""UI smoke tests: no internal IDs in user-facing copy."""

from __future__ import annotations

import re
import unittest

from price_tracker.canonical_families import load_families

INTERNAL_ID_PATTERN = re.compile(
    r"\b(regular_bags|5_13oz|party_size|per_lb|dozen_normalized|family_size)\b",
    re.I,
)


class TestNoInternalIdsExposed(unittest.TestCase):
    def test_display_names_hide_internal_ids(self) -> None:
        for family in load_families():
            self.assertFalse(
                INTERNAL_ID_PATTERN.search(family.canonical_tracker_family),
                msg=family.id,
            )
            if "_" in family.id:
                self.assertNotEqual(
                    family.id.lower(),
                    family.canonical_tracker_family.lower(),
                    msg=f"raw id exposed as title: {family.id}",
                )

    def test_subtitles_are_user_facing(self) -> None:
        for family in load_families():
            self.assertTrue(len(family.size_format_subtitle) > 0)
            lower = family.size_format_subtitle.lower()
            self.assertNotIn("regular_bags", lower)
            self.assertNotIn("regular bags", lower)
            self.assertNotIn("regular boxes", lower)

    def test_regular_family_size_subtitle_shape(self) -> None:
        """Snack/cereal size-tier families use regular/family size + range."""
        for family_id, expected_prefix in (
            ("ruffles_regular_bags", "regular size,"),
            ("oreo_family_size", "family size,"),
            ("nabisco_snack_crackers", "family size,"),
            ("doritos_5_13oz", "regular size,"),
            ("general_mills_cereal_regular", "regular size,"),
            ("general_mills_cereal_family_size", "family size,"),
            ("cheetos_party_size", "family size,"),
            ("post_cereal_giant_size", "family size,"),
        ):
            family = next(f for f in load_families() if f.id == family_id)
            self.assertTrue(
                family.size_format_subtitle.lower().startswith(expected_prefix),
                msg=f"{family_id}: {family.size_format_subtitle!r}",
            )


if __name__ == "__main__":
    unittest.main()
