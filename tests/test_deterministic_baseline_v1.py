"""Integrity checks for deterministic-baseline-v1."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from shopper_query.baseline_versions import (  # noqa: E402
    ASSESSMENT_POLICY_VERSION,
    BASELINE_ID,
    CATALOG_VERSION,
    CLARIFICATION_POLICY_VERSION,
    DETERMINISTIC_PIPELINE_VERSION,
    ENTITY_RESOLUTION_VERSION,
    EXPECTED_ACTIVE_TRACKER_COUNT,
    EXPECTED_PROTECTED_PHRASE_COUNT,
    FRONTEND_ASSET_VERSION,
    QUERY_CONTRACT_VERSION,
    versions_for_health,
)
from shopper_query.entity_resolution.catalog import load_active_trackers  # noqa: E402

MANIFEST = ROOT / "docs" / "baselines" / "deterministic-baseline-v1.json"
EVALS = ROOT / "docs" / "baselines" / "deterministic-baseline-v1-evals.json"
INDEX = ROOT / "index.html"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class TestDeterministicBaselineV1(unittest.TestCase):
    def test_manifest_exists_and_versions(self) -> None:
        self.assertTrue(MANIFEST.is_file())
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["baseline_id"], BASELINE_ID)
        self.assertEqual(data["main_sha_short"], "44ff557")
        self.assertEqual(data["frontend_asset_version"], FRONTEND_ASSET_VERSION)
        self.assertEqual(data["query_contract_version"], QUERY_CONTRACT_VERSION)
        self.assertEqual(data["assessment_contract_version"], ASSESSMENT_POLICY_VERSION)
        self.assertEqual(data["deterministic_pipeline_version"], DETERMINISTIC_PIPELINE_VERSION)
        self.assertEqual(data["catalog_version"], CATALOG_VERSION)
        self.assertEqual(data["entity_resolution_version"], ENTITY_RESOLUTION_VERSION)
        self.assertEqual(data["clarification_policy_version"], CLARIFICATION_POLICY_VERSION)
        self.assertFalse(data["llm_used"])
        self.assertFalse(data["llm_invoked"])
        self.assertEqual(data["llm_invocation_count"], 0)
        self.assertEqual(data["llm_token_cost_usd"], 0)
        self.assertFalse(data["public_behavior_changed_by_this_freeze"])
        flags = data["feature_flags"]
        self.assertTrue(flags["liveApiEnabled"])
        self.assertTrue(flags["assessEnabled"])
        self.assertTrue(flags["structuredClarificationEnabled"])

    def test_frozen_eval_hashes(self) -> None:
        artifacts = json.loads(EVALS.read_text(encoding="utf-8"))["artifacts"]
        for art in artifacts:
            path = ROOT / art["path"]
            self.assertTrue(path.is_file(), art["path"])
            self.assertEqual(_sha256(path), art["sha256"], art["path"])

    def test_active_tracker_and_phrase_counts(self) -> None:
        active = [t for t in load_active_trackers() if t.active]
        self.assertEqual(len(active), EXPECTED_ACTIVE_TRACKER_COUNT)
        audit = json.loads(
            (ROOT / "evals/entity-resolution/protected-phrase-audit.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(audit["phrase_count"], EXPECTED_PROTECTED_PHRASE_COUNT)
        self.assertEqual(audit["validation_failure_count"], 0)
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(man["active_tracker_count"], EXPECTED_ACTIVE_TRACKER_COUNT)
        self.assertEqual(man["protected_phrase_count"], EXPECTED_PROTECTED_PHRASE_COUNT)

    def test_index_feature_flags_match_baseline(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("structuredClarificationEnabled: true", html)
        self.assertIn("liveApiEnabled: true", html)
        self.assertIn("assessEnabled: true", html)
        self.assertIn(f"aislecheck.js?v={FRONTEND_ASSET_VERSION}", html)

    def test_health_versions_payload(self) -> None:
        payload = versions_for_health()
        self.assertEqual(payload["baseline_id"], BASELINE_ID)
        self.assertIs(payload["llm_used"], False)

    def test_no_llm_provider_in_runtime_path(self) -> None:
        """Production shopper_query + deal_assessment + API must not import LLM SDKs."""
        banned = re.compile(
            r"^\s*(from|import)\s+(openai|anthropic|google\.generativeai|litellm)\b"
        )
        roots = [
            ROOT / "scripts" / "shopper_query",
            ROOT / "scripts" / "deal_assessment",
            ROOT / "services" / "aislecheck_api",
            ROOT / "aislecheck-prototype",
        ]
        offenders: list[str] = []
        for root in roots:
            for path in root.rglob("*"):
                if path.suffix not in {".py", ".js"}:
                    continue
                if "__pycache__" in path.parts:
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    if banned.search(line):
                        offenders.append(f"{path.relative_to(ROOT)}:{i}:{line.strip()}")
        self.assertEqual(offenders, [])

    def test_schema_does_not_depend_on_untracked_holdout(self) -> None:
        schema = (ROOT / "scripts" / "shopper_query" / "schema.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("holdout_labeler", schema)


if __name__ == "__main__":
    unittest.main()
