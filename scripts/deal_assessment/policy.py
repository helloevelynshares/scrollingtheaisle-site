"""Explicit minimum-history and comparability policy for AisleCheck scoring.

First public feature prefers defensive coverage over maximum verdicts.
"""

from __future__ import annotations

# Chartable weeks required before any grounded signal.
INSUFFICIENT_MAX_OBS = 1  # 0–1 → insufficient_data
# Early signal band: show evidence, never a strong stock-up/good/fair verdict.
LIMITED_MAX_OBS = 3  # 2–3 → limited_data
# Full verdicts require at least this many comparable observations.
FULL_VERDICT_MIN_OBS = 4  # 4+ → normal benchmark bucket

POLICY_VERSION = "aislecheck_history_v1"


def history_tier(observation_count: int) -> str:
    """Return insufficient_data | limited_data | full."""
    if observation_count <= INSUFFICIENT_MAX_OBS:
        return "insufficient_data"
    if observation_count <= LIMITED_MAX_OBS:
        return "limited_data"
    return "full"
