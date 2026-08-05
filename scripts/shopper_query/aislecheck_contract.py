"""Map shopper_query PipelineResult → AisleCheck homepage response contract.

Deterministic only. No LLM. No deal-quality verdict.
"""

from __future__ import annotations

from typing import Any

from product_matching.engine import ProductionMatcherFacade, get_facade
from shopper_query.pipeline import PipelineResult, process_query

# Bump when the homepage JSON contract shape/semantics change.
AISLECHECK_CONTRACT_VERSION = "aislecheck.v1"

# Clarification priority when multiple fields are missing (highest first).
_MISSING_FIELD_PRIORITY = (
    "product_text",
    "price",
    "price_basis",
    "required_quantity",
    "package_size",
    "retailer",
    "promotion_type",
)


def _tracker_option(
    family_id: str, facade: ProductionMatcherFacade
) -> dict[str, str | None]:
    fam = facade._families.get(family_id)  # noqa: SLF001 — read-only display lookup
    if fam is None:
        return {
            "id": family_id,
            "display_name": family_id,
            "name": family_id,
            "subtitle": None,
        }
    name = (fam.display_name or fam.canonical_tracker_family or family_id).strip()
    subtitle = (fam.subtitle or fam.size_format_subtitle or "").strip() or None
    display = f"{name} · {subtitle}" if subtitle else name
    return {
        "id": family_id,
        "display_name": display,
        "name": name,
        "subtitle": subtitle,
    }


def _format_price(price: float | None) -> str | None:
    if price is None:
        return None
    if float(price).is_integer():
        return f"${int(price)}"
    return f"${price:.2f}"


def _promotion_label(parsed: dict[str, Any]) -> str | None:
    promo = parsed.get("promotion_type") or "unknown"
    qty = parsed.get("required_quantity")
    if promo == "bogo":
        return "BOGO (buy one, get one)"
    if promo == "multi_buy" and qty:
        return f"Buy {qty}"
    if promo == "buy_x_get_y" and qty:
        return f"Buy {qty}"
    if promo == "multi_buy":
        return "Multi-buy"
    if promo == "simple_sale":
        return None
    if promo in {"unknown", "mixed_or_unclear"}:
        return None
    return str(promo).replace("_", " ")


def _price_basis_prompt(parsed: dict[str, Any]) -> str:
    price_txt = _format_price(parsed.get("price")) or "that price"
    qty = parsed.get("required_quantity") or "several"
    return f"Is {price_txt} the total for {qty} or {price_txt} each?"


def _prompt_for_field(field: str, parsed: dict[str, Any]) -> str:
    if field == "price":
        return "What was the advertised price?"
    if field == "price_basis":
        return _price_basis_prompt(parsed)
    if field == "required_quantity":
        return "How many do you need to buy for this deal?"
    if field == "package_size":
        return "What size was the package?"
    if field == "product_text":
        return "What product did you see?"
    if field == "retailer":
        return "Which store was this at?"
    if field == "promotion_type":
        return "Was this a sale price, multi-buy, or BOGO?"
    return "Can you add a bit more detail about the deal?"


def _pick_missing_field(parsed: dict[str, Any], reason_codes: list[str]) -> str | None:
    missing = list(parsed.get("missing_fields") or [])
    # Adapter-only escalations that the pipeline may not list as missing.
    if "price_basis" in reason_codes and "price_basis" not in missing:
        missing.append("price_basis")
    for field in _MISSING_FIELD_PRIORITY:
        if field in missing:
            # package_size alone is usually non-blocking for matched continues.
            if field == "package_size" and "package_size" not in reason_codes:
                continue
            if field == "retailer":
                continue
            if field == "promotion_type":
                continue
            return field
    return None


def _reason_codes(result: PipelineResult) -> list[str]:
    codes: list[str] = []
    parsed = result.parsed
    behavior = result.behavior
    if behavior.reason:
        codes.append(behavior.reason)
    if parsed.conflicting_prices:
        codes.append("conflicting_prices")
    if parsed.malformed_price:
        codes.append("malformed_price")
    if parsed.unsupported_retailer:
        codes.append("unsupported_retailer")
    for amb in parsed.ambiguities:
        if amb not in codes:
            codes.append(amb)
    if result.match.status and f"matcher_{result.match.status}" not in codes:
        codes.append(f"matcher_{result.match.status}")
    # Detect multi-buy / buy-N wording where unit vs total is unclear.
    if (
        parsed.price is not None
        and parsed.required_quantity
        and parsed.price_basis in {"unknown", "each"}
        and parsed.promotion_type in {"simple_sale", "unknown", "mixed_or_unclear"}
    ):
        codes.append("price_basis_unclear")
    return codes


def _next_action_and_clarify(
    result: PipelineResult, reason_codes: list[str]
) -> tuple[str, str | None, str | None, list[dict[str, str | None]]]:
    """Return (next_action, clarify_kind, clarify_prompt, plausible_trackers)."""
    facade = get_facade()
    behavior = result.behavior.behavior
    match = result.match
    parsed_dict = result.parsed.to_dict()

    plausible: list[dict[str, str | None]] = []
    for fid in list(match.candidate_family_ids)[:3]:
        plausible.append(_tracker_option(fid, facade))

    if behavior == "invalid":
        return "invalid", None, None, plausible

    if behavior == "unsupported":
        return "unsupported", None, None, plausible

    if behavior == "clarify":
        reason = result.behavior.reason or ""
        if reason == "ambiguous_tracker_match" or match.status in {
            "ambiguous",
            "needs_review",
        }:
            if not plausible and match.review_family_ids:
                for fid in list(match.review_family_ids)[:3]:
                    plausible.append(_tracker_option(fid, facade))
            return (
                "clarify",
                "ambiguous_product",
                "Which product did you mean?",
                plausible,
            )
        if reason.startswith("product_brand_unspecified"):
            if plausible:
                return (
                    "clarify",
                    "ambiguous_product",
                    "Which product did you mean?",
                    plausible,
                )
            brand = reason.split(":", 1)[-1] if ":" in reason else "product"
            return (
                "clarify",
                "missing_field",
                f"Which brand of {brand} was it?",
                plausible,
            )
        if reason.startswith("package_synonym_ambiguous"):
            return (
                "clarify",
                "missing_field",
                "What size was the package?",
                plausible,
            )
        if reason == "missing_price":
            return (
                "clarify",
                "missing_field",
                _prompt_for_field("price", parsed_dict),
                plausible,
            )
        if reason == "missing_required_quantity":
            return (
                "clarify",
                "missing_field",
                _prompt_for_field("required_quantity", parsed_dict),
                plausible,
            )
        if reason == "missing_product_text":
            return (
                "clarify",
                "missing_field",
                _prompt_for_field("product_text", parsed_dict),
                plausible,
            )
        field = _pick_missing_field(parsed_dict, reason_codes)
        if field:
            return (
                "clarify",
                "missing_field",
                _prompt_for_field(field, parsed_dict),
                plausible,
            )
        return ("clarify", "missing_field", "Can you add a bit more detail?", plausible)

    # continue — optionally escalate unclear price basis before confirming.
    if "price_basis_unclear" in reason_codes:
        return (
            "clarify",
            "missing_field",
            _prompt_for_field("price_basis", parsed_dict),
            plausible,
        )

    return "continue", None, None, plausible


def build_aislecheck_response(
    result: PipelineResult,
    *,
    session_id: str | None = None,
    prior_clarify_digests: list[str] | None = None,
    structured_clarification: bool = False,
) -> dict[str, Any]:
    """Build the homepage AisleCheck JSON contract from a pipeline result.

    ``structured_clarification`` opts into loop-terminal candidate pick lists and
    related prompts. When false (public default), loop breaks become plain
    ``unsupported`` so older frontends keep their existing contract.
    """
    facade = get_facade()
    parsed = result.parsed.to_dict()
    reason_codes = _reason_codes(result)
    next_action, clarify_kind, clarify_prompt, plausible = _next_action_and_clarify(
        result, reason_codes
    )

    selected = None
    if result.behavior.matched_family_id and next_action == "continue":
        selected = _tracker_option(result.behavior.matched_family_id, facade)
    elif result.behavior.matched_family_id and next_action == "clarify":
        # Keep selected when matched but waiting on a field (e.g. missing price).
        selected = _tracker_option(result.behavior.matched_family_id, facade)

    missing_field = None
    if clarify_kind == "missing_field":
        missing_field = _pick_missing_field(parsed, reason_codes)
        if missing_field is None and result.behavior.reason == "missing_price":
            missing_field = "price"
        if missing_field is None and result.behavior.reason == "missing_required_quantity":
            missing_field = "required_quantity"
        if missing_field is None and "price_basis_unclear" in reason_codes:
            missing_field = "price_basis"
        if missing_field is None and (
            result.behavior.reason or ""
        ).startswith("package_synonym"):
            missing_field = "package_size"

    clarify_fingerprint = None
    if next_action == "clarify":
        from shopper_query.entity_resolution.clarify_progress import (
            build_clarify_fingerprint,
            should_break_clarify_loop,
        )

        fp = build_clarify_fingerprint(
            clarify_kind=clarify_kind,
            clarify_prompt=clarify_prompt,
            reason=result.behavior.reason,
            matcher_status=result.match.status,
            missing_fields=parsed.get("missing_fields") or [],
            product_text=parsed.get("product_text") or "",
        )
        clarify_fingerprint = fp.digest
        if should_break_clarify_loop(fp, prior_clarify_digests):
            reason_codes = list(reason_codes) + ["clarify_loop_broken"]
            if structured_clarification and plausible:
                # Opt-in: show candidate picks as the terminal clarify step.
                next_action = "clarify"
                clarify_kind = "ambiguous_product"
                clarify_prompt = (
                    "I still can't tell which product you mean. "
                    "Pick one of these, or try a more specific name "
                    "(brand plus size or form)."
                )
                missing_field = "product_text"
            else:
                # Public / legacy-safe terminal: unsupported, no new pick-list UX.
                next_action = "unsupported"
                clarify_kind = None
                clarify_prompt = None
                missing_field = None
                plausible = []
                reason_codes = list(reason_codes) + ["clarify_loop_terminal"]
            clarify_fingerprint = build_clarify_fingerprint(
                clarify_kind=clarify_kind or "unsupported",
                clarify_prompt=clarify_prompt or "unsupported",
                reason="clarify_loop_broken",
                matcher_status=result.match.status,
                missing_fields=["product_text"] if next_action == "clarify" else [],
                product_text=parsed.get("product_text") or "",
            ).digest

    normalizations = []
    if result.normalized:
        normalizations = [s.to_dict() for s in result.normalized.steps]

    return {
        "contract_version": AISLECHECK_CONTRACT_VERSION,
        "original_query": result.original_query,
        "normalized_query": result.query_used,
        "normalizations_applied": normalizations,
        "extracted": {
            "product_text": parsed.get("product_text") or "",
            "price": parsed.get("price"),
            "price_display": _format_price(parsed.get("price")),
            "promotion_type": parsed.get("promotion_type"),
            "promotion_label": _promotion_label(parsed),
            "required_quantity": parsed.get("required_quantity"),
            "price_basis": parsed.get("price_basis"),
            "package_size": parsed.get("package_size_text"),
            "retailer": parsed.get("retailer"),
        },
        "missing_fields": list(parsed.get("missing_fields") or []),
        "matcher_status": result.match.status,
        "selected_tracker": selected,
        "plausible_trackers": plausible,
        "next_action": next_action,
        "clarify_kind": clarify_kind,
        "clarify_prompt": clarify_prompt,
        "clarify_field": missing_field,
        "clarify_fingerprint": clarify_fingerprint,
        "reason_codes": reason_codes,
        "session_id": session_id,
        "debug": {
            "path": result.path,
            "normalization": result.normalized.to_dict() if result.normalized else None,
            "parsed": parsed,
            "match": result.match.to_dict(),
            "behavior": result.behavior.to_dict(),
            "routing": {
                "next_action": next_action,
                "clarify_kind": clarify_kind,
                "clarify_field": missing_field,
                "clarify_fingerprint": clarify_fingerprint,
                "structured_clarification": bool(structured_clarification),
            },
        },
    }


def run_aislecheck_query(
    query: str,
    *,
    session_id: str | None = None,
    apply_normalization: bool = True,
    prior_clarify_digests: list[str] | None = None,
    structured_clarification: bool = False,
) -> dict[str, Any]:
    """Process a shopper query and return the AisleCheck contract."""
    result = process_query(query, apply_normalization=apply_normalization)
    return build_aislecheck_response(
        result,
        session_id=session_id,
        prior_clarify_digests=prior_clarify_digests,
        structured_clarification=structured_clarification,
    )
