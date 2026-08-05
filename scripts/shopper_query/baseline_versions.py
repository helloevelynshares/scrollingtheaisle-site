"""Version identifiers for the public deterministic AisleCheck baseline.

These constants document reproducibility. Changing them requires an explicit
baseline-version update — they do not alter matching, scoring, or UI policy.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Public pre-LLM freeze: deterministic-baseline-v1 (main @ 44ff557).
BASELINE_ID = "deterministic-baseline-v1"
DETERMINISTIC_PIPELINE_VERSION = "deterministic_pipeline_v1"
CATALOG_VERSION = "catalog_v1"
ENTITY_RESOLUTION_VERSION = "entity_resolution_v1"
# Matches deal_assessment.policy.POLICY_VERSION / health contracts.assessment.
ASSESSMENT_POLICY_VERSION = "aislecheck_history_v1"
CLARIFICATION_POLICY_VERSION = "structured_clarification_v1"
# Matches shopper_query.aislecheck_contract.AISLECHECK_CONTRACT_VERSION.
QUERY_CONTRACT_VERSION = "aislecheck.v1"

CANONICAL_YAML = ROOT / "data" / "canonical_tracker_families.yaml"
PHRASE_OVERLAYS_YAML = ROOT / "data" / "entity_resolution" / "phrase_overlays.yaml"
CATALOG_EVAL_PATH = ROOT / "evals" / "entity-resolution" / "catalog-resolution-v1.jsonl"
PHRASE_AUDIT_PATH = ROOT / "evals" / "entity-resolution" / "protected-phrase-audit.json"

# Frozen at baseline creation: active trackers / protected phrases.
EXPECTED_ACTIVE_TRACKER_COUNT = 86
EXPECTED_PROTECTED_PHRASE_COUNT = 47

# Public frontend asset cache at activation.
FRONTEND_ASSET_VERSION = "ac18"


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def catalog_yaml_sha256() -> str | None:
    return _sha256_file(CANONICAL_YAML)


def phrase_overlays_sha256() -> str | None:
    return _sha256_file(PHRASE_OVERLAYS_YAML)


def versions_for_health() -> dict[str, object]:
    """Safe version payload for /health (no secrets, no debug internals)."""
    return {
        "baseline_id": BASELINE_ID,
        "deterministic_pipeline_version": DETERMINISTIC_PIPELINE_VERSION,
        "catalog_version": CATALOG_VERSION,
        "entity_resolution_version": ENTITY_RESOLUTION_VERSION,
        "assessment_policy_version": ASSESSMENT_POLICY_VERSION,
        "clarification_policy_version": CLARIFICATION_POLICY_VERSION,
        "query_contract_version": QUERY_CONTRACT_VERSION,
        "llm_used": False,
    }
