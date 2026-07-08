"""Durable script-ready shortlist wording derived from tracker family metadata.

Keeps the human-facing blurb in sync with the canonical family display name /
subtitle so one-off shortlist generators do not hand-write product copy that can
drift from the tracker. In particular, for the Nabisco family-size snack cracker
family it names the *actual eligible items* (Wheat Thins / Triscuit / Chicken in
a Biskit) instead of the generic "Nabisco snack crackers" app label.
"""

from __future__ import annotations

from price_tracker.canonical_families import TrackerFamily, family_by_id


def _oxford_join(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _price_text(price: float | None) -> str:
    if price is None:
        return "on sale"
    if float(price).is_integer():
        return f"${int(price)}"
    return f"${price:.2f}"


def _app_label(family: TrackerFamily) -> str:
    """Subtitle without the trailing size range, e.g. the app's promo title."""
    subtitle = family.subtitle or family.size_format_subtitle or ""
    return subtitle.split(",")[0].strip()


def is_family_size_family(family: TrackerFamily) -> bool:
    """True when the family represents family-size boxes with named product lines."""
    return bool(family.allowed_product_lines) and family.package_type == "family_size_box"


def family_shortlist_blurb(
    family: TrackerFamily,
    price: float | None,
    *,
    week_label: str = "this week",
    family_size_eligible: bool = False,
) -> str:
    """One-line shortlist blurb for a matched tracker family.

    Families that carry explicit `allowed_product_lines` + a family-size package
    type lead with the real eligible items and clarify the generic app label,
    e.g. "Wheat Thins, Triscuit, and Chicken in a Biskit family-size boxes are
    $3.49 this week — the app labels it as Nabisco family-size snack crackers,
    but those are the actual eligible items."

    The family-size sentence is only emitted when the caller confirms the offer
    is family-size eligible (``family_size_eligible=True``) — i.e. it passed the
    same canonical match eligibility gate the tracker uses. This prevents
    standard-size / Ritz-led mix-or-match offers from being mislabeled as a
    "family-size boxes are $X" deal. Without confirmation, a generic
    display-name blurb (no family-size claim) is returned.
    """
    price_text = _price_text(price)
    if family_size_eligible and is_family_size_family(family):
        joined = _oxford_join(list(family.allowed_product_lines))
        app_label = _app_label(family)
        return (
            f"{joined} family-size boxes are {price_text} {week_label} — the app "
            f"labels it as {app_label}, but those are the actual eligible items."
        )
    name = family.display_name or family.canonical_tracker_family
    return f"{name} are {price_text} {week_label}."


def family_shortlist_blurb_by_id(
    family_id: str,
    price: float | None,
    *,
    week_label: str = "this week",
    family_size_eligible: bool = False,
) -> str | None:
    family = family_by_id().get(family_id)
    if family is None:
        return None
    return family_shortlist_blurb(
        family, price, week_label=week_label, family_size_eligible=family_size_eligible
    )


if __name__ == "__main__":
    print(family_shortlist_blurb_by_id("nabisco_snack_crackers", 3.49, family_size_eligible=True))
