"""Generate canonical match audit artifacts per weekly ad run."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = ROOT / "output" / "weekly_deals"


@dataclass
class AuditRecord:
    week_start: str
    week_end: str
    feed: str
    family_id: str
    offer_text: str
    price: float | None
    match_decision: str
    match_confidence: float
    match_reason: str
    reject_reason: str | None = None
    canonical_intent: str | None = None
    ad_product_type: str | None = None
    hard_negative_hits: list[str] = field(default_factory=list)
    output_class: str = "canonical_tracker_match"
    updated_tracker: bool = False
    all_time_low_change: bool = False
    graph_preview_change: str | None = None
    # Canonical display / provenance metadata for this family.
    display_name: str | None = None
    subtitle: str | None = None
    manufacturer_family: str | None = None
    allowed_product_lines: list[str] = field(default_factory=list)
    package_type: str | None = None
    size_range: str | None = None
    eligible_item_examples: list[str] = field(default_factory=list)

    @property
    def raw_offer_text(self) -> str:
        return self.offer_text


@dataclass
class WeekAuditBundle:
    week_start: str
    week_end: str
    generated_at: str
    accepted: list[AuditRecord] = field(default_factory=list)
    rejected: list[AuditRecord] = field(default_factory=list)
    manual_review: list[AuditRecord] = field(default_factory=list)
    families_updated: list[str] = field(default_factory=list)
    all_time_low_changes: list[dict[str, Any]] = field(default_factory=list)
    graph_preview_changes: list[dict[str, Any]] = field(default_factory=list)
    rejected_tempting: list[AuditRecord] = field(default_factory=list)


class CanonicalMatchAuditCollector:
    def __init__(self) -> None:
        self._by_week: dict[str, WeekAuditBundle] = {}

    def add(self, record: AuditRecord) -> None:
        bundle = self._by_week.setdefault(
            record.week_start,
            WeekAuditBundle(
                week_start=record.week_start,
                week_end=record.week_end,
                generated_at=datetime.now(timezone.utc).isoformat(),
            ),
        )
        if record.updated_tracker:
            if record.family_id not in bundle.families_updated:
                bundle.families_updated.append(record.family_id)
        if record.all_time_low_change:
            bundle.all_time_low_changes.append(
                {
                    "family_id": record.family_id,
                    "feed": record.feed,
                    "price": record.price,
                    "offer_text": record.offer_text,
                }
            )
        if record.graph_preview_change:
            bundle.graph_preview_changes.append(
                {
                    "family_id": record.family_id,
                    "feed": record.feed,
                    "detail": record.graph_preview_change,
                }
            )

        buckets = {
            "accepted": bundle.accepted,
            "rejected": bundle.rejected,
            "manual_review": bundle.manual_review,
        }
        key = record.match_decision if record.match_decision in buckets else "rejected"
        buckets[key].append(record)

        if (
            record.match_decision == "rejected"
            and record.price is not None
            and record.hard_negative_hits
        ):
            bundle.rejected_tempting.append(record)

    def bundles(self) -> dict[str, WeekAuditBundle]:
        return self._by_week


def write_week_audit(bundle: WeekAuditBundle, output_root: Path | None = None) -> tuple[Path, Path]:
    root = output_root or DEFAULT_OUTPUT_ROOT
    week_dir = root / bundle.week_start
    week_dir.mkdir(parents=True, exist_ok=True)

    json_path = week_dir / "canonical_match_audit.json"
    md_path = week_dir / "canonical_match_audit.md"

    payload = {
        "week_start": bundle.week_start,
        "week_end": bundle.week_end,
        "generated_at": bundle.generated_at,
        "summary": {
            "accepted": len(bundle.accepted),
            "rejected": len(bundle.rejected),
            "manual_review": len(bundle.manual_review),
            "families_updated": bundle.families_updated,
            "all_time_low_changes": bundle.all_time_low_changes,
            "graph_preview_changes": bundle.graph_preview_changes,
        },
        "accepted": [asdict(r) for r in bundle.accepted],
        "rejected": [asdict(r) for r in bundle.rejected],
        "manual_review": [asdict(r) for r in bundle.manual_review],
        "rejected_tempting": [asdict(r) for r in bundle.rejected_tempting],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_audit_markdown(bundle), encoding="utf-8")
    return json_path, md_path


def write_all_audits(
    collector: CanonicalMatchAuditCollector, output_root: Path | None = None
) -> list[tuple[Path, Path]]:
    paths: list[tuple[Path, Path]] = []
    for bundle in collector.bundles().values():
        paths.append(write_week_audit(bundle, output_root))
    return paths


def render_audit_markdown(bundle: WeekAuditBundle) -> str:
    lines = [
        f"# Canonical match audit: {bundle.week_start} to {bundle.week_end}",
        "",
        f"Generated: {bundle.generated_at}",
        "",
        "## Summary",
        "",
        f"- **Accepted:** {len(bundle.accepted)}",
        f"- **Rejected:** {len(bundle.rejected)}",
        f"- **Manual review:** {len(bundle.manual_review)}",
        f"- **Families updated:** {', '.join(bundle.families_updated) or '(none)'}",
        "",
        "## Graph update safety check",
        "",
    ]

    if bundle.all_time_low_changes:
        lines.append("### All-time low changes")
        lines.append("")
        for change in bundle.all_time_low_changes:
            lines.append(
                f"- `{change['family_id']}` ({change['feed']}): "
                f"${change['price']}: {change['offer_text']}"
            )
        lines.append("")
    else:
        lines.append("- No new all-time lows written this run.")
        lines.append("")

    if bundle.graph_preview_changes:
        lines.append("### Graph preview changes")
        lines.append("")
        for change in bundle.graph_preview_changes:
            lines.append(
                f"- `{change['family_id']}` ({change['feed']}): {change['detail']}"
            )
        lines.append("")

    blocked = bundle.rejected + bundle.manual_review
    if blocked:
        lines.append("### Blocked from tracker graph")
        lines.append("")
        for record in blocked:
            lines.append(
                f"- `{record.family_id}` ({record.feed}): **{record.match_decision}**: "
                f"{record.offer_text!r} @ ${record.price}"
            )
            if record.reject_reason:
                lines.append(f"  - Reason: {record.reject_reason}")
            if record.hard_negative_hits:
                lines.append(
                    f"  - Hard negatives: {', '.join(record.hard_negative_hits)}"
                )
        lines.append("")

    if bundle.rejected_tempting:
        lines.append("## Rejected tempting items")
        lines.append("")
        lines.append(
            "These looked like deals but were blocked from updating canonical trackers:"
        )
        lines.append("")
        for record in bundle.rejected_tempting:
            lines.append(
                f"- `{record.family_id}`: {record.offer_text!r} @ ${record.price}: "
                f"{record.reject_reason}"
            )
        lines.append("")

    if bundle.accepted:
        lines.append("## Accepted matches")
        lines.append("")
        for record in bundle.accepted:
            lines.append(
                f"- `{record.family_id}` ({record.feed}): {record.offer_text!r} "
                f"@ ${record.price} (confidence {record.match_confidence:.2f})"
            )
            if record.display_name:
                lines.append(f"  - Display: {record.display_name}")
            if record.subtitle:
                lines.append(f"  - Subtitle: {record.subtitle}")
            if record.manufacturer_family:
                lines.append(f"  - Manufacturer family: {record.manufacturer_family}")
            if record.allowed_product_lines:
                lines.append(
                    f"  - Allowed product lines: {', '.join(record.allowed_product_lines)}"
                )
            if record.package_type or record.size_range:
                detail = ", ".join(
                    filter(None, [record.package_type, record.size_range])
                )
                lines.append(f"  - Package: {detail}")
            if record.eligible_item_examples:
                lines.append(
                    f"  - Eligible item examples: {', '.join(record.eligible_item_examples)}"
                )
        lines.append("")

    return "\n".join(lines)
