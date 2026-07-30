"""Canonical match eligibility, gate weekly ad prices before tracker updates."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from price_tracker.canonical_families import TrackerFamily, family_by_id, load_families
from price_tracker.product_type_taxonomy import (
    ProductTypeClassification,
    classify_product_type,
    extract_unit_hint,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_PATH = ROOT / "config" / "canonical_match_rules.yaml"

CONFIDENCE_MAP = {"high": 0.9, "medium": 0.7, "low": 0.45}
DEFAULT_MIN_CONFIDENCE = 0.65
DEFAULT_ATL_CONFIDENCE = 0.85
DEFAULT_LARGE_CHANGE_PCT = 40.0


@dataclass(frozen=True)
class RequiredAttribute:
    """One AND-required auto-match attribute group (OR within the group)."""

    name: str
    any_of: tuple[str, ...] = ()
    any_of_patterns: tuple[str, ...] = ()


@dataclass(frozen=True)
class FamilyMatchRules:
    family_id: str
    canonical_intent: str | None = None
    positive_keywords: tuple[str, ...] = ()
    negative_keywords: tuple[str, ...] = ()
    allowed_product_types: tuple[str, ...] = ()
    disallowed_product_types: tuple[str, ...] = ()
    allowed_units: tuple[str, ...] = ()
    disallowed_units: tuple[str, ...] = ()
    allowed_package_patterns: tuple[str, ...] = ()
    disallowed_package_patterns: tuple[str, ...] = ()
    # When set, an accepted match must contain at least one of these
    # confirmation keywords (e.g. "family size" or an in-range size). Matches
    # that only hit a generic block type with no confirmation go to manual
    # review instead of updating the tracker graph. Empty = no requirement.
    # Prefer required_attributes for named missing-attribute reporting.
    require_confirmation_keywords: tuple[str, ...] = ()
    # Named attribute groups; EVERY group must hit at least one any_of /
    # any_of_patterns token before automatic accept. Missing groups → review.
    required_attributes: tuple[RequiredAttribute, ...] = ()
    min_confidence: float = DEFAULT_MIN_CONFIDENCE
    atl_requires_confidence: float = DEFAULT_ATL_CONFIDENCE
    large_price_change_pct: float = DEFAULT_LARGE_CHANGE_PCT


@dataclass
class MatchEligibilityResult:
    match_decision: str  # accepted | rejected | manual_review
    match_confidence: float
    match_reason: str
    reject_reason: str | None = None
    canonical_intent: str | None = None
    ad_product_type: str | None = None
    hard_negative_hits: list[str] = field(default_factory=list)
    product_type_match: bool = True
    package_type_match: bool = True
    unit_match: bool = True
  # For ranked/script output classification
    output_class: str = "canonical_tracker_match"  # ad_deal_only | manual_review_required
    # Canonical display / provenance metadata (surfaced in audit + reports).
    display_name: str | None = None
    subtitle: str | None = None
    manufacturer_family: str | None = None
    package_type: str | None = None
    size_range: str | None = None
    allowed_product_lines: list[str] = field(default_factory=list)
    eligible_item_examples: list[str] = field(default_factory=list)
    # Review-gate attribute accounting (empty when unused).
    present_attributes: list[str] = field(default_factory=list)
    missing_attributes: list[str] = field(default_factory=list)
    reason_code: str | None = None


def _normalize_keyword_list(values: Any) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(str(v).strip().lower() for v in values if str(v).strip())


def _parse_required_attributes(raw: Any) -> tuple[RequiredAttribute, ...]:
    """Parse required_attributes from YAML.

    Accepted shapes:
      required_attributes:
        package_count:
          any_of: [12-pack, 12 pack]
          any_of_patterns: ["\\\\b12\\\\s*ct\\\\b"]
      # or list form:
      - name: package_count
        any_of: [...]
    """
    if not raw:
        return ()
    out: list[RequiredAttribute] = []
    if isinstance(raw, dict):
        items = raw.items()
        for name, spec in items:
            if not isinstance(spec, dict):
                continue
            out.append(
                RequiredAttribute(
                    name=str(name).strip(),
                    any_of=_normalize_keyword_list(spec.get("any_of")),
                    any_of_patterns=tuple(
                        str(p) for p in (spec.get("any_of_patterns") or ()) if str(p).strip()
                    ),
                )
            )
    elif isinstance(raw, list):
        for spec in raw:
            if not isinstance(spec, dict):
                continue
            name = str(spec.get("name") or "").strip()
            if not name:
                continue
            out.append(
                RequiredAttribute(
                    name=name,
                    any_of=_normalize_keyword_list(spec.get("any_of")),
                    any_of_patterns=tuple(
                        str(p) for p in (spec.get("any_of_patterns") or ()) if str(p).strip()
                    ),
                )
            )
    return tuple(attr for attr in out if attr.any_of or attr.any_of_patterns)


def _parse_family_rules(family_id: str, raw: dict[str, Any]) -> FamilyMatchRules:
    return FamilyMatchRules(
        family_id=str(family_id),
        canonical_intent=raw.get("canonical_intent"),
        positive_keywords=_normalize_keyword_list(raw.get("positive_keywords")),
        negative_keywords=_normalize_keyword_list(raw.get("negative_keywords")),
        allowed_product_types=_normalize_keyword_list(raw.get("allowed_product_types")),
        disallowed_product_types=_normalize_keyword_list(raw.get("disallowed_product_types")),
        allowed_units=_normalize_keyword_list(raw.get("allowed_units")),
        disallowed_units=_normalize_keyword_list(raw.get("disallowed_units")),
        allowed_package_patterns=tuple(raw.get("allowed_package_patterns") or ()),
        disallowed_package_patterns=tuple(raw.get("disallowed_package_patterns") or ()),
        require_confirmation_keywords=_normalize_keyword_list(
            raw.get("require_confirmation_keywords")
        ),
        required_attributes=_parse_required_attributes(raw.get("required_attributes")),
        min_confidence=float(raw.get("min_confidence", DEFAULT_MIN_CONFIDENCE)),
        atl_requires_confidence=float(
            raw.get("atl_requires_confidence", DEFAULT_ATL_CONFIDENCE)
        ),
        large_price_change_pct=float(
            raw.get("large_price_change_pct", DEFAULT_LARGE_CHANGE_PCT)
        ),
    )


def _parse_rules_doc(doc: dict[str, Any]) -> dict[str, FamilyMatchRules]:
    out: dict[str, FamilyMatchRules] = {}
    for family_id, raw in (doc.get("families") or {}).items():
        if not isinstance(raw, dict):
            continue
        out[str(family_id)] = _parse_family_rules(str(family_id), raw)
    return out


def load_match_rules(path: Path | None = None) -> dict[str, FamilyMatchRules]:
    rules_path = path or DEFAULT_RULES_PATH
    if not rules_path.is_file():
        return {}
    with rules_path.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle) or {}
    return _parse_rules_doc(doc)


def merge_family_yaml_rules(
    family: TrackerFamily, rules: dict[str, FamilyMatchRules]
) -> FamilyMatchRules | None:
    """Merge config file rules with optional per-family YAML match_eligibility block."""
    base = rules.get(family.id)
    yaml_block = getattr(family, "match_eligibility", None) or {}

    if base is None and not yaml_block:
        return None

    def pick(field: str, default: Any = None) -> Any:
        if yaml_block.get(field) is not None:
            return yaml_block[field]
        if base is not None:
            return getattr(base, field)
        return default

    required_raw = pick("required_attributes", ())
    if isinstance(required_raw, (dict, list)):
        required_attrs = _parse_required_attributes(required_raw)
    elif isinstance(required_raw, tuple):
        required_attrs = required_raw
    else:
        required_attrs = ()

    return FamilyMatchRules(
        family_id=family.id,
        canonical_intent=pick("canonical_intent"),
        positive_keywords=_normalize_keyword_list(pick("positive_keywords", ())),
        negative_keywords=_normalize_keyword_list(pick("negative_keywords", ())),
        allowed_product_types=_normalize_keyword_list(pick("allowed_product_types", ())),
        disallowed_product_types=_normalize_keyword_list(pick("disallowed_product_types", ())),
        allowed_units=_normalize_keyword_list(pick("allowed_units", ())),
        disallowed_units=_normalize_keyword_list(pick("disallowed_units", ())),
        allowed_package_patterns=tuple(pick("allowed_package_patterns", ())),
        disallowed_package_patterns=tuple(pick("disallowed_package_patterns", ())),
        require_confirmation_keywords=_normalize_keyword_list(
            pick("require_confirmation_keywords", ())
        ),
        required_attributes=required_attrs,
        min_confidence=float(pick("min_confidence", DEFAULT_MIN_CONFIDENCE)),
        atl_requires_confidence=float(
            pick("atl_requires_confidence", DEFAULT_ATL_CONFIDENCE)
        ),
        large_price_change_pct=float(
            pick("large_price_change_pct", DEFAULT_LARGE_CHANGE_PCT)
        ),
    )


def _attribute_hits(text: str, attr: RequiredAttribute) -> list[str]:
    hits = _keyword_hits(text, attr.any_of)
    hits.extend(_pattern_hits(text, attr.any_of_patterns))
    return list(dict.fromkeys(hits))


def _evaluate_required_attributes(
    full_text: str, rules: FamilyMatchRules
) -> tuple[list[str], list[str]]:
    """Return (present_attribute_names, missing_attribute_names)."""
    present: list[str] = []
    missing: list[str] = []
    for attr in rules.required_attributes:
        if _attribute_hits(full_text, attr):
            present.append(attr.name)
        else:
            missing.append(attr.name)
    # Legacy OR confirmation list acts as a single unnamed confirmation group.
    if rules.require_confirmation_keywords:
        name = "confirmation"
        if _keyword_hits(full_text, rules.require_confirmation_keywords):
            present.append(name)
        else:
            missing.append(name)
    return present, missing


_REASON_CODE_BY_MISSING = {
    "package_size": "missing_package_size",
    "package_count": "missing_package_count",
    "brand": "missing_brand",
    "product_form": "ambiguous_product_variant",
    "product_line": "ambiguous_product_variant",
    "container_type": "ambiguous_product_variant",
    "confirmation": "insufficient_information",
}


def _reason_code_for_missing(missing: list[str]) -> str | None:
    if not missing:
        return None
    if len(missing) > 1:
        return "ambiguous_product_variant"
    return _REASON_CODE_BY_MISSING.get(missing[0], "insufficient_information")


def _keyword_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    """Return keywords that appear as whole tokens/phrases (not substrings).

    Short tokens like ``ct``, ``cup``, or ``stick`` must not match inside
    unrelated words (``selected``, ``occupied``, ``stickshift``).
    """
    lowered = text.lower()
    hits: list[str] = []
    for keyword in keywords:
        kw = keyword.strip().lower()
        if not kw:
            continue
        escaped = re.escape(kw).replace(r"\ ", r"\s+")
        # Non-word edges so digits/letters cannot absorb the token, while
        # apostrophes/punctuation still allow "Eggland" in "Eggland's".
        if re.search(rf"(?<![\w]){escaped}(?![\w])", lowered):
            hits.append(keyword)
    return hits


def _pattern_hits(text: str, patterns: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in patterns if re.search(pattern, lowered)]


_EXPLICIT_PACKAGE_SIGNAL = re.compile(
    r"""
    \b\d+(?:\.\d+)?\s*
    (?:oz\.?|fl\.?\s*oz\.?|ct\.?|count|pk|pack|lb\.?|liter|litre|l)\b
    |
    \b(?:dozen|party\s+size|family\s+size|tub|cups?|bottles?|cans?)\b
    |
    \b\d+\s*(?:to|-|–)\s*\d+(?:\.\d+)?\s*oz\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _has_explicit_package_signal(text: str) -> bool:
    """True when the offer states a concrete size/count/container cue."""
    return bool(_EXPLICIT_PACKAGE_SIGNAL.search(text))


def _mixed_item_package_ambiguity(text: str) -> bool:
    """True when an or/comma list mixes distinct containers or oz sizes.

    Same-family Mix & Match with one shared size (Goldfish crackers or crisps
    4–8 oz) returns False. Distinct containers (cans vs bottles) or distinct
    oz values return True so we abstain instead of auto-accepting.
    """
    lowered = text.lower()
    is_list = bool(re.search(r"\bor\b", lowered) or lowered.count(",") >= 2)
    if not is_list:
        return False
    containers = [
        name
        for name in ("cans", "can", "bottles", "bottle", "tub", "cups", "cup")
        if re.search(rf"(?<![\w]){name}(?![\w])", lowered)
    ]
    # Normalize singular/plural so cans+can counts once.
    normalized = {
        c[:-1] if c.endswith("s") and c not in {"cans"} else c for c in containers
    }
    # Treat can/cans and bottle/bottles as two families.
    families = set()
    for c in containers:
        if c.startswith("can"):
            families.add("can")
        elif c.startswith("bottle"):
            families.add("bottle")
        elif c.startswith("cup"):
            families.add("cup")
        elif c == "tub":
            families.add("tub")
    if len(families) >= 2:
        return True
    sizes = re.findall(r"\b(\d+(?:\.\d+)?)\s*oz\b", lowered)
    if len(set(sizes)) >= 2:
        return True
    return False


def _confidence_score(
    *,
    text: str,
    rules: FamilyMatchRules,
    classification: ProductTypeClassification,
    keyword_confidence: str | None,
    has_price: bool,
) -> float:
    score = CONFIDENCE_MAP.get(keyword_confidence or "medium", 0.7)
    if rules.positive_keywords:
        pos_hits = _keyword_hits(text, rules.positive_keywords)
        if pos_hits:
            score += min(0.1, 0.03 * len(pos_hits))
        else:
            score -= 0.15
    if rules.canonical_intent and classification.primary_type == rules.canonical_intent:
        score += 0.1
    elif (
        rules.allowed_product_types
        and classification.primary_type
        and classification.primary_type in rules.allowed_product_types
    ):
        score += 0.05
    # Confidence also dips for multi-item list copy (A or B / A, B, C), not for a
    # single size/grade comma like "Grade AA, 18-ct."
    if re.search(r"\bor\b", text.lower()) or text.lower().count(",") >= 2:
        score -= 0.15
    if not has_price:
        score -= 0.3
    return max(0.0, min(1.0, score))


def _offer_texts(row: dict[str, str]) -> tuple[str, str]:
    """Return (primary split text, full combined text).

    Full text includes package_text because size often lives only there
    (e.g. product "Blackberries" + package "6 oz.", or "Lucerne Large Eggs" +
    "12 ct").
    """
    primary = (row.get("split_product_text") or row.get("raw_offer_text") or "").strip()
    full = " ".join(
        filter(
            None,
            [
                row.get("split_product_text"),
                row.get("raw_offer_text"),
                row.get("promo_text"),
                row.get("package_text"),
            ],
        )
    ).strip()
    return primary, full or primary


def _family_metadata(family: TrackerFamily) -> dict[str, Any]:
    """Display / provenance metadata surfaced on every eligibility result."""
    return {
        "display_name": getattr(family, "display_name", "")
        or family.canonical_tracker_family,
        "subtitle": getattr(family, "subtitle", "") or family.size_format_subtitle,
        "manufacturer_family": getattr(family, "manufacturer_family", "") or None,
        "package_type": getattr(family, "package_type", "") or None,
        "size_range": getattr(family, "size_range", "") or None,
        "allowed_product_lines": list(getattr(family, "allowed_product_lines", ()) or ()),
        "eligible_item_examples": list(getattr(family, "eligible_item_examples", ()) or ()),
    }


def evaluate_canonical_match(
    row: dict[str, str],
    family: TrackerFamily,
    *,
    rules: FamilyMatchRules | None = None,
    keyword_confidence: str | None = None,
    prior_price: float | None = None,
    historical_low: float | None = None,
) -> MatchEligibilityResult:
    """Decide whether a pattern-matched ad row may update the canonical tracker."""
    primary_text, full_text = _offer_texts(row)
    # Classify on product + package so "Lucerne Large Eggs" + "12 ct" and
    # "Blackberries" + "6 oz." resolve to the intended product type.
    classification = classify_product_type(f"{primary_text} {row.get('package_text') or ''}")
    unit_hint = extract_unit_hint(full_text, row)
    meta = _family_metadata(family)

    if rules is None:
        # No eligibility rules, accept legacy pattern match (with basic price guard).
        conf = CONFIDENCE_MAP.get(keyword_confidence or "medium", 0.7)
        return MatchEligibilityResult(
            match_decision="accepted",
            match_confidence=conf,
            match_reason="No eligibility rules configured; pattern match accepted.",
            canonical_intent=None,
            ad_product_type=classification.primary_type,
            output_class="canonical_tracker_match",
            **meta,
        )

    # Product-identity negatives (chocolate, pint, strawberries) must come from
    # the product text — not package_text. A mixed-deal package like
    # "Pint, 6 oz" would otherwise reject a genuine "Blackberries 6 oz" row.
    hard_negatives = list(
        dict.fromkeys(
            _keyword_hits(primary_text, rules.negative_keywords)
            + _pattern_hits(full_text, rules.disallowed_package_patterns)
        )
    )

    product_type_match = True
    package_type_match = True
    unit_match = True
    reject_parts: list[str] = []

    if hard_negatives:
        reject_parts.append(
            f"hard negative keyword/pattern hit: {', '.join(hard_negatives)}"
        )

    # Prefer an allowed product type from all matched types (not only primary).
    # Egg cartons labeled "12 ct" used to classify primarily as 12_pack_cans.
    ad_type = classification.primary_type
    if rules.allowed_product_types and classification.all_types:
        allowed_hits = [
            t for t in classification.all_types if t in rules.allowed_product_types
        ]
        if allowed_hits:
            ad_type = allowed_hits[0]

    if rules.disallowed_product_types:
        disallowed_hits = [
            t for t in classification.all_types if t in rules.disallowed_product_types
        ]
        if disallowed_hits:
            product_type_match = False
            ad_type = disallowed_hits[0]
            reject_parts.append(
                f"ad product type {disallowed_hits[0]!r} is incompatible with "
                f"canonical intent {rules.canonical_intent!r}"
            )

    if rules.allowed_product_types and ad_type and product_type_match:
        if ad_type not in rules.allowed_product_types:
            # Allow generic nabisco if explicitly listed
            if not (
                "generic_nabisco_block" in rules.allowed_product_types
                and ad_type == "generic_nabisco_block"
            ):
                product_type_match = False
                reject_parts.append(
                    f"ad product type {ad_type!r} not in allowed types "
                    f"{list(rules.allowed_product_types)}"
                )

    if unit_hint and rules.disallowed_units and unit_hint in rules.disallowed_units:
        unit_match = False
        reject_parts.append(f"unit {unit_hint!r} is disallowed for this family")

    if unit_hint and rules.allowed_units and unit_hint not in rules.allowed_units:
        # Normalize per_lb price basis to lb for seafood counter items.
        normalized_unit = unit_hint
        if normalized_unit == "per_lb":
            normalized_unit = "lb"
        if normalized_unit not in rules.allowed_units:
            # Small oz packs for per-lb fresh items are a common mismatch.
            if not (unit_hint == "oz" and "lb" in rules.allowed_units):
                unit_match = False
                reject_parts.append(
                    f"unit {unit_hint!r} not in allowed units {list(rules.allowed_units)}"
                )

    # allowed_package_patterns: previously parsed but unused. Enforce when set.
    # - disallowed patterns already feed hard_negatives above
    # - explicit package outside allowed → reject
    # - no package signal yet → manual review (do not invent a size)
    package_missing_for_allowed = False
    if rules.allowed_package_patterns:
        allowed_pkg_hits = _pattern_hits(full_text, rules.allowed_package_patterns)
        if allowed_pkg_hits:
            package_type_match = package_type_match and True
        elif _has_explicit_package_signal(full_text):
            package_type_match = False
            reject_parts.append(
                "package size/form present but outside allowed_package_patterns"
            )
        else:
            package_missing_for_allowed = True

    price = None
    raw_price = row.get("advertised_price")
    if raw_price:
        try:
            price = float(str(raw_price).replace("$", ""))
        except ValueError:
            price = None

    # BOGO / buy-X-get-Y tiles frequently omit a printed shelf price; that is
    # expected, not a weak match. Count the promo mechanic as priced evidence.
    basis = (row.get("price_basis") or "").lower()
    priced_for_confidence = price is not None or basis in {"bogo", "buy_x_get_y"}

    confidence = _confidence_score(
        text=primary_text,
        rules=rules,
        classification=classification,
        keyword_confidence=keyword_confidence,
        has_price=priced_for_confidence,
    )

    manual_review = False
    # Multi-item Mix & Match copy ("Crackers or Crisps", "A, B, C") is common.
    # Gate it behind size confirmation below when required attributes /
    # require_confirmation_keywords are set; bare multi-item lists still need review.
    lowered_primary = primary_text.lower()
    variant_list = bool(
        re.search(r"\bor\b", lowered_primary) or lowered_primary.count(",") >= 2
    )
    mixed_package_ambiguity = _mixed_item_package_ambiguity(full_text)

    present_attrs, missing_attrs = _evaluate_required_attributes(full_text, rules)
    reason_code: str | None = None

    if package_missing_for_allowed:
        manual_review = True
        if "package_size" not in missing_attrs:
            missing_attrs = list(missing_attrs) + ["package_size"]
        reason_code = _reason_code_for_missing(missing_attrs)
        reject_parts.append(
            "allowed_package_patterns configured but no explicit package signal"
        )

    # Confirmation / required-attribute gate first so a real size/carton signal
    # can boost confidence before the ATL / large-change / medium-confidence floors.
    if missing_attrs:
        manual_review = True
        reason_code = reason_code or _reason_code_for_missing(missing_attrs)
        if "missing required auto-match attribute(s)" not in " ".join(reject_parts):
            reject_parts.append(
                "missing required auto-match attribute(s): " + ", ".join(missing_attrs)
            )
    elif present_attrs and not mixed_package_ambiguity:
        # Confirmed size/carton/brand signal is strong evidence — boost so a
        # legitimate new low is not stuck in manual_review by the ATL floor.
        confidence = min(1.0, confidence + 0.15)
        # Size-confirmed Mix & Match should update the graph; do not force review
        # solely for "or" when package attrs are unambiguous.
        variant_list = False

    if mixed_package_ambiguity:
        manual_review = True
        reject_parts.append(
            "mixed-item offer has conflicting package/container cues"
        )
        reason_code = reason_code or "ambiguous_product_variant"

    if variant_list:
        manual_review = True
        reject_parts.append("multi-item variant list (or/comma) needs review")

    if keyword_confidence == "medium" and confidence < rules.min_confidence + 0.1:
        manual_review = True
        if "medium-confidence" not in " ".join(reject_parts):
            reject_parts.append(
                f"medium pattern confidence {confidence:.2f} needs review"
            )

    # New all-time low needs higher confidence
    if (
        price is not None
        and historical_low is not None
        and price < historical_low
        and confidence < rules.atl_requires_confidence
    ):
        manual_review = True
        reject_parts.append(
            f"new all-time low ${price:.2f} requires confidence >= "
            f"{rules.atl_requires_confidence:.2f} (got {confidence:.2f})"
        )

    # Large preview price change
    if (
        price is not None
        and prior_price is not None
        and prior_price > 0
    ):
        change_pct = abs(price - prior_price) / prior_price * 100
        if change_pct >= rules.large_price_change_pct and confidence < rules.atl_requires_confidence:
            manual_review = True
            reject_parts.append(
                f"large price change {change_pct:.0f}% vs prior week requires audit"
            )

    if hard_negatives or not product_type_match or not package_type_match or not unit_match:
        reason = "; ".join(reject_parts) if reject_parts else "eligibility check failed"
        return MatchEligibilityResult(
            match_decision="rejected",
            match_confidence=confidence,
            match_reason="Pattern matched but failed eligibility checks.",
            reject_reason=reason,
            canonical_intent=rules.canonical_intent,
            ad_product_type=ad_type,
            hard_negative_hits=hard_negatives,
            product_type_match=product_type_match,
            package_type_match=package_type_match,
            unit_match=unit_match,
            output_class="ad_deal_only",
            present_attributes=present_attrs,
            missing_attributes=missing_attrs,
            reason_code="explicit_attribute_conflict",
            **meta,
        )

    if confidence < rules.min_confidence:
        return MatchEligibilityResult(
            match_decision="manual_review",
            match_confidence=confidence,
            match_reason="Pattern matched but confidence below threshold.",
            reject_reason=(
                f"confidence {confidence:.2f} < min {rules.min_confidence:.2f}"
            ),
            canonical_intent=rules.canonical_intent,
            ad_product_type=ad_type,
            hard_negative_hits=hard_negatives,
            product_type_match=product_type_match,
            package_type_match=package_type_match,
            unit_match=unit_match,
            output_class="manual_review_required",
            present_attributes=present_attrs,
            missing_attributes=missing_attrs,
            reason_code=reason_code or "insufficient_information",
            **meta,
        )

    if manual_review:
        return MatchEligibilityResult(
            match_decision="manual_review",
            match_confidence=confidence,
            match_reason="Pattern matched but needs manual review before graph update.",
            reject_reason="; ".join(reject_parts) if reject_parts else "ambiguous match",
            canonical_intent=rules.canonical_intent,
            ad_product_type=ad_type,
            hard_negative_hits=hard_negatives,
            product_type_match=product_type_match,
            package_type_match=package_type_match,
            unit_match=unit_match,
            output_class="manual_review_required",
            present_attributes=present_attrs,
            missing_attributes=missing_attrs,
            reason_code=reason_code or "insufficient_information",
            **meta,
        )

    return MatchEligibilityResult(
        match_decision="accepted",
        match_confidence=confidence,
        match_reason=(
            f"Eligible {rules.canonical_intent or family.id} match "
            f"(type={ad_type}, confidence={confidence:.2f})"
        ),
        canonical_intent=rules.canonical_intent,
        ad_product_type=ad_type,
        hard_negative_hits=hard_negatives,
        product_type_match=product_type_match,
        package_type_match=package_type_match,
        unit_match=unit_match,
        output_class="canonical_tracker_match",
        present_attributes=present_attrs,
        missing_attributes=missing_attrs,
        reason_code="none",
        **meta,
    )


class EligibilityIndex:
    """Cached rules + families for repeated matching in a pipeline run."""

    def __init__(self, rules_path: Path | None = None) -> None:
        self._families = family_by_id()
        self._rules = load_match_rules(rules_path)
        self._merged: dict[str, FamilyMatchRules | None] = {
            fid: merge_family_yaml_rules(fam, self._rules)
            for fid, fam in self._families.items()
        }

    def rules_for(self, family_id: str) -> FamilyMatchRules | None:
        return self._merged.get(family_id)

    def family(self, family_id: str) -> TrackerFamily | None:
        return self._families.get(family_id)

    def evaluate(
        self,
        row: dict[str, str],
        family_id: str,
        *,
        keyword_confidence: str | None = None,
        prior_price: float | None = None,
        historical_low: float | None = None,
    ) -> MatchEligibilityResult:
        family = self._families[family_id]
        return evaluate_canonical_match(
            row,
            family,
            rules=self._merged.get(family_id),
            keyword_confidence=keyword_confidence,
            prior_price=prior_price,
            historical_low=historical_low,
        )
