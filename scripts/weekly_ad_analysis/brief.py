"""Render video_brief.md from scored deals."""

from __future__ import annotations

from weekly_ad_analysis.scoring import ScoredDeal


def _section(title: str, deals: list[dict]) -> str:
    if not deals:
        return ""
    lines = [f"## {title}", ""]
    for deal in deals:
        lines.append(f"### {deal['canonical_name']}")
        lines.append(f"- **Deal:** {deal.get('deal_price_display', '—')}")
        if deal.get("normalized_unit_price") is not None:
            lines.append(
                f"- **Unit math:** ${deal['normalized_unit_price']:.2f} / {deal.get('normalized_unit', 'unit')}"
            )
        if deal.get("costco_match_name"):
            lines.append(
                f"- **Costco:** {deal['costco_match_name']} — "
                f"${deal.get('costco_unit_price', '—')} / {deal.get('costco_unit_type', 'unit')}"
            )
        if deal.get("historical_benchmark_bucket") not in {None, "insufficient history"}:
            lines.append(f"- **History:** {deal['historical_benchmark_bucket']}")
        lines.append(f"- **Confidence:** {deal.get('confidence', 'medium')}")
        lines.append(f"- **Speaking point:** {deal.get('script_angle', '')}")
        lines.append("")
    return "\n".join(lines)


def render_video_brief(
    *,
    market_display_name: str,
    retailer_label: str,
    week_start: str,
    week_end: str,
    ranked: list[dict],
    skipped: list[dict],
) -> str:
    themes: list[str] = []
    if any(d.get("is_five_dollar_friday") for d in ranked):
        themes.append("$5 Friday food deals")
    if any(d.get("deal_bucket") == "Clear win vs Costco" for d in ranked):
        themes.append("grocer beats Costco on tracked staples")
    if any(
        d.get("deal_bucket") == "No Costco comp, but historically strong market price"
        for d in ranked
    ):
        themes.append("historically strong prices without a clean Costco comp")

    summary = (
        ", ".join(themes)
        if themes
        else "A lighter week on tracked food staples — lean on the strongest matches only."
    )

    friday = [d for d in ranked if d.get("is_five_dollar_friday")]
    clear_wins = [d for d in ranked if d.get("deal_bucket") == "Clear win vs Costco" and d not in friday]
    on_par = [
        d
        for d in ranked
        if d.get("deal_bucket") == "On par with Costco / grocer wins on variety"
        and d not in friday
    ]
    historic = [
        d
        for d in ranked
        if d.get("deal_bucket") == "No Costco comp, but historically strong market price"
        and d not in friday
    ]
    honorable = [
        d
        for d in ranked
        if d.get("deal_bucket") not in {
            "Clear win vs Costco",
            "On par with Costco / grocer wins on variety",
            "No Costco comp, but historically strong market price",
            "Skip / not worth highlighting",
            "Not a Costco win",
        }
        and d not in friday
        and d.get("content_score", 0) >= 8
    ]
    do_not = skipped + [
        d
        for d in ranked
        if d.get("deal_bucket") in {"Not a Costco win", "Skip / not worth highlighting"}
    ]

    parts = [
        f"# {market_display_name} weekly ad brief — week of {week_start}",
        "",
        f"**Retailer:** {retailer_label}  ",
        f"**Ad week:** {week_start} → {week_end}",
        "",
        "## Summary",
        "",
        summary,
        "",
        _section("$5 Friday food deals", friday),
        _section("Clear wins vs Costco", clear_wins),
        _section("On par with Costco / variety wins", on_par),
        _section("Historically strong, no clean Costco comp", historic),
        _section("Honorable mentions", honorable),
        _section("Do not mention / Costco wins / weak deals", do_not),
    ]
    return "\n".join(part for part in parts if part.strip()) + "\n"
