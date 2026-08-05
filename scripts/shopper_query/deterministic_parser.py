"""Deterministic free-text extraction adapted from weekly-ad offer patterns.

There is no dedicated shopper free-text parser in production. Weekly ads are
vision-extracted into structured CSV columns. This module reuses the same
regex families already used when interpreting offer / promo text:

- ``price_tracker.normalization`` multi-buy / BOGO / price parsing cues
- ``generate_weekly_ad_prices._BOGO_PROMO_RE`` BOGO wording
- shared ``PROMOTION_TYPES`` / ``PRICE_BASIS_VALUES`` (``shopper_query.offer_vocab``)

It does NOT call an LLM and does NOT invent product identity.
"""

from __future__ import annotations

import re

from shopper_query.schema import (
    PRICE_BASIS_SET,
    PROMOTION_TYPE_SET,
    SUPPORTED_RETAILERS,
    ParsedShopperQuery,
)

# --- Patterns adapted from weekly-ad / normalization helpers -----------------

# Numeric dollar amounts: $3.99, 3.99, $5, 2/$5 style handled separately.
_DOLLAR_PRICE_RE = re.compile(
    r"(?<![\w.])\$?\s*(\d{1,3}(?:\.\d{1,2})?)\s*(?:ea\.?|each|/lb|per\s*lb)?(?!\s*(?:oz|ct|pack|pk|lb)\b)",
    re.I,
)
_EXPLICIT_DOLLAR_RE = re.compile(r"\$\s*(\d{1,3}(?:\.\d{1,2})?)")
_N_FOR_X_RE = re.compile(
    r"(\d+)\s*(?:for|/)\s*\$?\s*(\d+(?:\.\d+)?)",
    re.I,
)
# From price_tracker.normalization._buy_x_get_y_unit_price / generate_weekly_ad_prices
_BOGO_RE = re.compile(
    r"\bbogo\b|buy\s+(\d+)[,\s]+get\s+(\d+)(?:\s+free)?|buy\s+(\d+)\s+get\s+(\d+)",
    re.I,
)
_WHEN_YOU_BUY_RE = re.compile(
    r"(?:when\s+you\s+buy|need\s+to\s+buy|gotta\s+(?:get|buy)|have\s+to\s+buy|"
    r"must\s+buy)\s+(\d+)\b",
    re.I,
)
_PICK_N_RE = re.compile(r"\bpick\s+(\d+)\b", re.I)
_MEMBER_PRICE_RE = re.compile(r"\bmember\s+price\b", re.I)
_DIGITAL_COUPON_RE = re.compile(
    r"\b(?:digital\s+coupon|clip\s+(?:or\s+)?click|clip\s+coupon)\b",
    re.I,
)
_PER_LB_RE = re.compile(
    r"\b(?:per\s*lb|/lb|\blb\.?\b|a\s+pound|per\s+pound)\b",
    re.I,
)
_PACKAGE_SIZE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:-\s*)?(?:to\s+\d+(?:\.\d+)?\s*)?"
    r"(oz|ounces?|fl\.?\s*oz|lb|lbs|pounds?|ct|count|pk|pack)\b",
    re.I,
)
_SIZE_TIER_RE = re.compile(
    r"\b(family\s+size|party\s+size|giant\s+size|regular\s+size|"
    r"big\s+box|large\s+pack|multipack)\b",
    re.I,
)
_RETAILER_RE = re.compile(
    r"\b(safeway|vons|albertsons|pavilions|trader\s*joe'?s|costco|"
    r"target|walmart|ralphs?|kroger|whole\s*foods)\b",
    re.I,
)

# Noise words stripped when building product_text after removing price/promo spans.
# Keep short prepositions that appear in product names (e.g. "Honey Bunches of Oats").
_FILLER_RE = re.compile(
    r"\b(?:is|are|was|were|at|for|a|an|on|in|to|my|i|me|we|"
    r"saw|see|got|getting|looking|look|found|thinking|about|"
    r"deal|sale|price|priced|costs?|costing|bucks?|dollars?|"
    r"please|help|wondering|if|that|this|those|these|"
    r"good|worth|it|they|them|and|or|with|from|hey|really|"
    r"this\s+week|week)\b",
    re.I,
)


def _unit_alias(raw: str) -> str:
    u = raw.strip().lower().replace(".", "").replace(" ", "")
    aliases = {
        "ounce": "oz",
        "ounces": "oz",
        "oz": "oz",
        "floz": "fl_oz",
        "lb": "lb",
        "lbs": "lb",
        "pound": "lb",
        "pounds": "lb",
        "ct": "ct",
        "count": "ct",
        "pk": "pack",
        "pack": "pack",
    }
    return aliases.get(u, u)


def _find_prices(text: str) -> list[float]:
    """Collect plausible shelf prices; prefer explicit $ amounts."""
    explicit = [float(m.group(1)) for m in _EXPLICIT_DOLLAR_RE.finditer(text)]
    if explicit:
        return explicit
    # Without $, only take amounts near price cues to avoid grabbing sizes.
    prices: list[float] = []
    for m in re.finditer(
        r"(?:\$|for|at|is|are|price(?:d)?|costs?)\s*(\d{1,3}(?:\.\d{1,2})?)\b",
        text,
        re.I,
    ):
        prices.append(float(m.group(1)))
    return prices


def _extract_promotion(text: str) -> tuple[str, str, int | None, int | None, list[str]]:
    """Return (promotion_type, price_basis, required_qty, items_received, notes)."""
    notes: list[str] = []
    lowered = text.lower()

    bogo = _BOGO_RE.search(text)
    if bogo:
        g = bogo.groups()
        buy = next((int(x) for x in g[:4:2] if x), None)
        get = next((int(x) for x in g[1:4:2] if x), None)
        if "bogo" in lowered and buy is None:
            buy, get = 1, 1
        if buy == 1 and (get == 1 or get is None):
            return "bogo", "bogo", buy or 1, (buy or 1) + (get or 1), notes
        return (
            "buy_x_get_y",
            "buy_x_get_y",
            buy,
            (buy or 0) + (get or 0) if buy and get else None,
            notes,
        )

    n_for = _N_FOR_X_RE.search(text)
    when_buy = _WHEN_YOU_BUY_RE.search(text)
    pick_n = _PICK_N_RE.search(text)
    multi_buy_word = re.search(r"\bmulti[\s-]?buy\b", text, re.I)

    if n_for or when_buy or pick_n or multi_buy_word:
        qty = None
        if when_buy:
            qty = int(when_buy.group(1))
        elif pick_n:
            qty = int(pick_n.group(1))
        elif n_for:
            qty = int(n_for.group(1))
        return "multi_buy", "multi_buy", qty, None, notes

    if _DIGITAL_COUPON_RE.search(text):
        return "digital_coupon", "each", None, None, notes
    if _MEMBER_PRICE_RE.search(text):
        return "member_price", "each", None, None, notes
    if _PER_LB_RE.search(text) and re.search(r"\$?\d", text):
        # Per-lb cue with a price → price_per_pound when product is produce/meat-like.
        if re.search(r"\b(?:grape|chicken|beef|steak|lb|pound)\b", lowered):
            return "price_per_pound", "per_lb", None, None, notes

    if re.search(r"\b(?:sale|on\s+sale|marked\s+down)\b", lowered):
        return "simple_sale", "each", None, None, notes

    # Stated shelf/deal price without another promo mechanic → simple_sale.
    # Callers may still override basis for per-lb.
    if _EXPLICIT_DOLLAR_RE.search(text) or re.search(
        r"(?:\$|for|at|is|are|price(?:d)?|costs?)\s*\d",
        text,
        re.I,
    ):
        if _PER_LB_RE.search(text) or re.search(r"\ba\s+pound\b", lowered):
            return "price_per_pound", "per_lb", None, None, notes
        return "simple_sale", "each", None, None, notes

    return "unknown", "unknown", None, None, notes


def _extract_package(text: str) -> tuple[str | None, float | None, str | None, list[str]]:
    ambiguities: list[str] = []
    tier = _SIZE_TIER_RE.search(text)
    size = _PACKAGE_SIZE_RE.search(text)

    size_text = None
    value = None
    unit = None

    if size:
        value = float(size.group(1))
        unit = _unit_alias(size.group(2))
        size_text = size.group(0).strip()
    if tier:
        tier_text = tier.group(1).strip().lower()
        if size_text:
            size_text = f"{tier_text} {size_text}"
        else:
            size_text = tier_text
        if tier_text in {"big box", "large pack"}:
            ambiguities.append(
                f"package_synonym_ambiguous:{tier_text.replace(' ', '_')}"
            )

    return size_text, value, unit, ambiguities


def _extract_retailer(text: str) -> tuple[str | None, bool]:
    m = _RETAILER_RE.search(text)
    if not m:
        return None, False
    name = re.sub(r"\s+", " ", m.group(1).strip().lower())
    name = name.replace("trader joe's", "trader joes").replace("trader joes", "trader_joes")
    # Canonical short names
    if "trader" in name:
        return "trader_joes", True
    if name in {"ralphs", "ralph"}:
        return "ralphs", True
    if name.replace(" ", "") == "wholefoods":
        return "whole_foods", True
    slug = name.replace(" ", "_")
    unsupported = slug not in SUPPORTED_RETAILERS
    return slug, unsupported


def _build_product_text(text: str) -> str:
    """Strip price/promo/retailer spans; keep brand + product + size cues."""
    cleaned = text
    # Promo / quantity patterns first (before stripping `$N`, which would break
    # ``3 for $5`` into a dangling ``3 for``).
    cleaned = _N_FOR_X_RE.sub(" ", cleaned)
    cleaned = _BOGO_RE.sub(" ", cleaned)
    cleaned = _WHEN_YOU_BUY_RE.sub(" ", cleaned)
    cleaned = _PICK_N_RE.sub(" ", cleaned)
    cleaned = _EXPLICIT_DOLLAR_RE.sub(" ", cleaned)
    cleaned = _RETAILER_RE.sub(" ", cleaned)
    cleaned = re.sub(
        r"\b(?:member\s+price|digital\s+coupon|clip\s+(?:or\s+)?click|"
        r"on\s+sale|per\s*lb|/lb|ea\.?|each|bucks?|dollars?|"
        r"multi[\s-]?buy|deal)\b",
        " ",
        cleaned,
        flags=re.I,
    )
    cleaned = re.sub(r"[?!,:;\"]+", " ", cleaned)
    # Keep brand apostrophes/hyphens (Lay's, Cheez-It, Coca-Cola). Only drop
    # standalone hyphen separators and normalize curly quotes to ASCII.
    cleaned = cleaned.replace("’", "'").replace("‘", "'")
    cleaned = re.sub(r"(?<!\d)\.(?!\d)", " ", cleaned)
    cleaned = re.sub(r"\s+-\s+", " ", cleaned)
    # Drop common conversational filler but keep size tier / brand words.
    tokens = []
    for tok in cleaned.split():
        if _FILLER_RE.fullmatch(tok):
            continue
        tokens.append(tok)
    product = " ".join(tokens).strip()
    product = re.sub(r"\s{2,}", " ", product)
    return product


def parse_shopper_query(raw_query: str) -> ParsedShopperQuery:
    """Extract structured deal facts from free-text using weekly-ad regexes."""
    text = (raw_query or "").strip()
    notes: list[str] = []
    if not text:
        return ParsedShopperQuery(
            missing_fields=["product_text", "price"],
            parse_notes=["empty_query"],
        )

    retailer, unsupported_retailer = _extract_retailer(text)
    promo_type, basis, req_qty, items_recv, promo_notes = _extract_promotion(text)
    notes.extend(promo_notes)
    size_text, size_value, size_unit, size_amb = _extract_package(text)

    prices = _find_prices(text)
    n_for = _N_FOR_X_RE.search(text)
    conflicting = False
    malformed = False
    price: float | None = None

    # Conflicting prices: two different explicit $ amounts that aren't N-for-X.
    if len(set(round(p, 2) for p in prices)) > 1 and not n_for:
        conflicting = True
        notes.append(f"conflicting_prices:{sorted(set(round(p, 2) for p in prices))}")
        price = None
    elif n_for:
        # For "3 for $5", shelf/deal price is the unit or the total?
        # Weekly-ad convention for multi_buy often stores advertised as each or total;
        # we store the **bundle total** when pattern is N for $X, and required_quantity=N.
        price = float(n_for.group(2))
        if req_qty is None:
            req_qty = int(n_for.group(1))
        if promo_type == "unknown":
            promo_type = "multi_buy"
            basis = "multi_buy"
    elif prices:
        price = prices[0]
    else:
        # Malformed verbal leftovers like "$" alone or "bucks" without digits
        # (verbal forms are handled by the normalization layer before this parser).
        if re.search(r"\$\s*$|\$\s*[^\d]", text) or re.search(
            r"\b(?:bucks?|dollars?)\b", text, re.I
        ):
            # bucks without a number → not yet numeric; may be pre-normalization.
            if not re.search(r"\d", text):
                malformed = True
                notes.append("price_words_without_digits")

    if conflicting:
        promo_type = "mixed_or_unclear"
        basis = "unknown"
        price = None

    product_text = _build_product_text(text)

    # Per-lb basis when size unit is lb or cue present.
    if size_unit == "lb" or (
        _PER_LB_RE.search(text) and promo_type == "price_per_pound"
    ):
        basis = "per_lb"
        if promo_type == "unknown":
            promo_type = "price_per_pound"

    # Validate enums (should already be from controlled set).
    if promo_type not in PROMOTION_TYPE_SET:
        promo_type = "unknown"
    if basis not in PRICE_BASIS_SET:
        basis = "unknown"

    missing: list[str] = []
    ambiguities = list(size_amb)

    if not product_text:
        missing.append("product_text")
    if price is None and not conflicting:
        missing.append("price")
    if size_text is None:
        # Size is often optional for matching; note as missing but not always blocking.
        missing.append("package_size")
    if promo_type == "unknown":
        missing.append("promotion_type")
    if promo_type in {"multi_buy", "buy_x_get_y", "bogo"} and req_qty is None:
        missing.append("required_quantity")
    if retailer is None:
        missing.append("retailer")

    # Ambiguous identity heuristics (conservative — do not auto-pick trackers).
    # Protected multiword phrases (Chips Ahoy, Sun Chips, …) are derived from the
    # canonical catalog + overlays so category tokens inside brands do not fire.
    from shopper_query.entity_resolution.protected_phrases import (
        get_protected_phrase_registry,
    )

    registry = get_protected_phrase_registry()
    known_chip_brands = re.search(
        r"\b(doritos|lays|lay'?s|ruffles|kettle|cheetos|tostitos|sun\s*chips|"
        r"pringles|miss\s+vickie'?s|cape\s+cod|popcorners|pop\s*corners)\b",
        product_text,
        re.I,
    )
    if (
        re.search(r"\bchips?\b", product_text, re.I)
        and not known_chip_brands
        and not registry.suppresses_category(product_text, "chips")
    ):
        ambiguities.append("product_brand_unspecified:chips")

    known_cereal_brands = re.search(
        r"\b(cheerios|cinnamon\s+toast|lucky\s+charms|honey\s+nut|"
        r"general\s+mills|post|kellogg|apple\s+jacks|honey\s+bunches)\b",
        product_text,
        re.I,
    )
    if (
        re.search(r"\bcereal\b", product_text, re.I)
        and not known_cereal_brands
        and not registry.suppresses_category(product_text, "cereal")
    ):
        ambiguities.append("product_brand_unspecified:cereal")

    return ParsedShopperQuery(
        retailer=retailer,
        product_text=product_text,
        price=price,
        package_size_text=size_text,
        package_size_value=size_value,
        package_size_unit=size_unit,
        promotion_type=promo_type,
        required_quantity=req_qty,
        items_received=items_recv,
        price_basis=basis,
        missing_fields=missing,
        ambiguities=ambiguities,
        conflicting_prices=conflicting,
        malformed_price=malformed,
        unsupported_retailer=unsupported_retailer,
        parse_notes=notes,
    )


def parsed_to_offer_row(parsed: ParsedShopperQuery) -> dict[str, str]:
    """Build a synthetic weekly-ad-style offer row for ProductionMatcherFacade.

    Mirrors ``deal_assistant.match.build_offer_row`` so matching stays identical.
    """
    size_bits = []
    if parsed.package_size_text:
        size_bits.append(parsed.package_size_text)
    if parsed.package_size_value is not None and parsed.package_size_unit:
        bit = f"{parsed.package_size_value} {parsed.package_size_unit}"
        if bit.lower() not in " ".join(size_bits).lower():
            size_bits.append(bit)
    package_text = " ".join(size_bits)

    product = parsed.product_text.strip()
    if package_text and package_text.lower() not in product.lower():
        offer_text = f"{product} {package_text}".strip()
    else:
        offer_text = product

    promo_parts = []
    if parsed.promotion_type and parsed.promotion_type != "unknown":
        promo_parts.append(parsed.promotion_type.replace("_", " "))
    if parsed.required_quantity:
        promo_parts.append(f"when you buy {parsed.required_quantity}")
    if parsed.price is not None:
        promo_parts.append(f"${parsed.price:.2f}")

    row: dict[str, str] = {
        "split_product_text": offer_text,
        "raw_offer_text": offer_text,
        "promo_text": " ".join(promo_parts),
        "advertised_price": f"{parsed.price:.2f}" if parsed.price is not None else "",
        "price_basis": parsed.price_basis if parsed.price_basis != "unknown" else "each",
        "package_unit": (parsed.package_size_unit or "each").lower(),
        "package_text": package_text,
    }
    if parsed.package_size_value is not None:
        row["package_size_min"] = str(parsed.package_size_value)
        row["package_size_max"] = str(parsed.package_size_value)
    return row
