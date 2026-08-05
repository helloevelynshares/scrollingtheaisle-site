"""Entity-resolution unit tests (catalog-wide, not brand one-offs)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from shopper_query.aislecheck_contract import (  # noqa: E402
    run_aislecheck_query,
)
from shopper_query.deterministic_parser import parse_shopper_query  # noqa: E402
from shopper_query.entity_resolution.catalog import load_active_trackers  # noqa: E402
from shopper_query.entity_resolution.clarify_progress import (  # noqa: E402
    build_clarify_fingerprint,
    should_break_clarify_loop,
)
from shopper_query.entity_resolution.collisions import find_collisions  # noqa: E402
from shopper_query.entity_resolution.language_model import (  # noqa: E402
    ResolutionClass,
    build_language_profiles,
)
from shopper_query.entity_resolution.protected_phrases import (  # noqa: E402
    clear_protected_phrase_cache,
    get_protected_phrase_registry,
)


class TestCatalogInventory(unittest.TestCase):
    def test_loads_all_active_from_yaml(self) -> None:
        trackers = load_active_trackers()
        self.assertGreaterEqual(len(trackers), 80)
        ids = {t.id for t in trackers}
        self.assertIn("chips_ahoy", ids)
        self.assertIn("doritos_5_13oz", ids)
        # No handwritten drift list — count must match YAML actives.
        self.assertEqual(len(ids), len(trackers))

    def test_every_tracker_has_language_profile(self) -> None:
        trackers = load_active_trackers()
        profiles = build_language_profiles(trackers)
        self.assertEqual(len(profiles), len(trackers))
        classes = {p.resolution_class for p in profiles}
        self.assertIn(ResolutionClass.PROTECTED_PHRASE_REQUIRED, classes)

    def test_chips_ahoy_classified_protected(self) -> None:
        profiles = {p.tracker_id: p for p in build_language_profiles()}
        self.assertEqual(
            profiles["chips_ahoy"].resolution_class,
            ResolutionClass.PROTECTED_PHRASE_REQUIRED,
        )
        self.assertIn("chips ahoy", profiles["chips_ahoy"].protected_phrases)

    def test_yaml_optional_entity_resolution_fields(self) -> None:
        chips = next(t for t in load_active_trackers() if t.id == "chips_ahoy")
        self.assertTrue(any("chips ahoy" in a.lower() for a in chips.aliases))
        self.assertTrue(any("chips ahoy" in p.lower() for p in chips.protected_phrases))


class TestProtectedPhrases(unittest.TestCase):
    def setUp(self) -> None:
        clear_protected_phrase_cache()

    def test_chips_ahoy_suppresses_chips_heuristic(self) -> None:
        reg = get_protected_phrase_registry()
        self.assertTrue(reg.suppresses_category("Chips Ahoy are on sale", "chips"))
        parsed = parse_shopper_query("Safeway Chips Ahoy are $1.99")
        self.assertNotIn("product_brand_unspecified:chips", parsed.ambiguities)

    def test_generic_chips_still_flags(self) -> None:
        parsed = parse_shopper_query("Safeway chips are $2.49")
        self.assertIn("product_brand_unspecified:chips", parsed.ambiguities)

    def test_sun_chips_protected(self) -> None:
        reg = get_protected_phrase_registry()
        self.assertTrue(reg.suppresses_category("Sun Chips 7 oz", "chips"))
        parsed = parse_shopper_query("Safeway Sun Chips are $2.49")
        self.assertNotIn("product_brand_unspecified:chips", parsed.ambiguities)

    def test_global_apple_jacks_protects_apple_token(self) -> None:
        # No Apple Jacks tracker today — global phrase must still suppress apple.
        reg = get_protected_phrase_registry()
        self.assertTrue(reg.suppresses_category("Apple Jacks cereal", "apple"))

    def test_honey_bunches_protects_honey_and_oats(self) -> None:
        reg = get_protected_phrase_registry()
        self.assertTrue(
            reg.suppresses_category("Honey Bunches of Oats", "honey")
            or reg.suppresses_category("Honey Bunches of Oats", "oats")
        )

    def test_registry_built_from_catalog_not_empty(self) -> None:
        reg = get_protected_phrase_registry()
        self.assertGreater(len(reg.phrases_longest_first), 10)


class TestClarifyLoop(unittest.TestCase):
    def test_fingerprint_ignores_product_text_drift(self) -> None:
        a = build_clarify_fingerprint(
            clarify_kind="missing_field",
            clarify_prompt="Which brand of chips was it?",
            reason="product_brand_unspecified:chips",
            matcher_status="no_match",
            missing_fields=["price"],
            product_text="chips",
        )
        b = build_clarify_fingerprint(
            clarify_kind="missing_field",
            clarify_prompt="Which brand of chips was it?",
            reason="product_brand_unspecified:chips",
            matcher_status="no_match",
            missing_fields=["price"],
            product_text="chips chips ahoy",
        )
        self.assertEqual(a.digest, b.digest)
        self.assertTrue(should_break_clarify_loop(b, [a.digest]))

    def test_loop_break_escalates_prompt(self) -> None:
        first = run_aislecheck_query("Safeway chips are $2.49")
        self.assertEqual(first["next_action"], "clarify")
        fp = first.get("clarify_fingerprint")
        self.assertTrue(fp)
        second = run_aislecheck_query(
            "Safeway chips are $2.49 chips",
            prior_clarify_digests=[fp],
        )
        self.assertIn("clarify_loop_broken", second.get("reason_codes") or [])
        # Terminal: unsupported (no candidates) or product clarify (with candidates).
        self.assertIn(second.get("next_action"), {"unsupported", "clarify"})
        if second.get("next_action") == "clarify":
            self.assertEqual(second.get("clarify_kind"), "ambiguous_product")


class TestCatalogCollisions(unittest.TestCase):
    def test_finds_embedded_category_tokens(self) -> None:
        collisions = find_collisions()
        kinds = {c.kind for c in collisions}
        self.assertIn("embedded_category_token", kinds)
        chips_hits = [
            c
            for c in collisions
            if c.kind == "embedded_category_token" and "chips_ahoy" in c.tracker_ids
        ]
        self.assertTrue(chips_hits)


class TestEndToEndExamples(unittest.TestCase):
    def test_chips_ahoy_continues(self) -> None:
        result = run_aislecheck_query("Safeway Chips Ahoy are $1.99")
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["selected_tracker"]["id"], "chips_ahoy")

    def test_sun_chips_continues(self) -> None:
        result = run_aislecheck_query("Safeway Sun Chips are $2.49")
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["selected_tracker"]["id"], "sun_chips_7oz")

    def test_goldfish_continues(self) -> None:
        result = run_aislecheck_query("Safeway Goldfish are $2.49")
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["selected_tracker"]["id"], "goldfish_bags")

    def test_smartfood_continues(self) -> None:
        result = run_aislecheck_query("Safeway Smartfood are $2.49")
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["selected_tracker"]["id"], "smartfood_popcorn")

    def test_generic_chips_still_clarifies(self) -> None:
        result = run_aislecheck_query("Safeway chips are $2.49")
        self.assertEqual(result["next_action"], "clarify")
        self.assertIn("brand", (result.get("clarify_prompt") or "").lower())


class TestMultiFamilyBrands(unittest.TestCase):
    def test_cheetos_brand_only_clarifies(self) -> None:
        result = run_aislecheck_query("Safeway Cheetos are $2.49")
        self.assertEqual(result["next_action"], "clarify")
        ids = {t["id"] for t in result.get("plausible_trackers") or []}
        self.assertEqual(ids, {"cheetos_regular_bags", "cheetos_party_size"})

    def test_cheetos_party_continues(self) -> None:
        result = run_aislecheck_query("Safeway Cheetos party size are $4.99")
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["selected_tracker"]["id"], "cheetos_party_size")

    def test_general_mills_cereal_clarifies_size(self) -> None:
        result = run_aislecheck_query("Safeway General Mills cereal are $2.49")
        self.assertEqual(result["next_action"], "clarify")

    def test_chobani_tub_continues(self) -> None:
        result = run_aislecheck_query("Safeway Chobani yogurt tub are $4.99")
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["selected_tracker"]["id"], "chobani_yogurt_tub")


class TestPhraseAuditGate(unittest.TestCase):
    def test_no_hard_validation_failures(self) -> None:
        from shopper_query.entity_resolution.phrase_audit import validation_failures

        failures = validation_failures()
        hard = [
            f
            for f in failures
            if any(
                e in {
                    "broad_category_term",
                    "maps_to_multiple_trackers",
                    "bypasses_package_form_boundary",
                    "unnecessary_generated_without_live_heuristic",
                }
                or e.startswith("nonexistent_tracker")
                for e in f.validation_errors
            )
        ]
        self.assertEqual(hard, [], msg=[f.to_dict() for f in hard[:10]])


if __name__ == "__main__":
    unittest.main()
