"""Catalog-wide entity resolution for AisleCheck shopper queries.

Derives protected phrases, language profiles, and reachability from the
authoritative canonical tracker catalog — not from handwritten ID lists.
"""

from __future__ import annotations

from .catalog import ActiveTracker, load_active_trackers
from .clarify_progress import (
    ClarifyFingerprint,
    build_clarify_fingerprint,
    should_break_clarify_loop,
)
from .collisions import Collision, find_collisions
from .language_model import (
    LanguageProfile,
    ResolutionClass,
    build_language_profile,
    build_language_profiles,
)
from .package_siblings import brand_siblings, multi_family_brands
from .protected_phrases import (
    ProtectedPhraseRegistry,
    get_protected_phrase_registry,
)
from .shopper_aliases import find_alias_hits, resolve_unique_alias

__all__ = [
    "ActiveTracker",
    "ClarifyFingerprint",
    "Collision",
    "LanguageProfile",
    "ProtectedPhraseRegistry",
    "ResolutionClass",
    "brand_siblings",
    "build_clarify_fingerprint",
    "build_language_profile",
    "build_language_profiles",
    "find_alias_hits",
    "find_collisions",
    "get_protected_phrase_registry",
    "load_active_trackers",
    "multi_family_brands",
    "resolve_unique_alias",
    "should_break_clarify_loop",
]
