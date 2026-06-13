"""Load Safeway tracked-item ledger CSV rows."""

from __future__ import annotations

import csv
from pathlib import Path

LEDGER_COLUMNS = (
    "canonical_id",
    "content_theme",
    "display_name",
    "search_query",
    "accepted_product_name",
    "accepted_pid",
    "accepted_upc",
    "tracking_unit",
    "priority",
    "status",
    "notes",
)


def load_tracked_items(
    path: Path,
    *,
    statuses: tuple[str, ...] | None = None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "search_query" not in reader.fieldnames:
            raise ValueError(f"{path} must include a search_query column")
        for row in reader:
            query = (row.get("search_query") or "").strip()
            if not query:
                continue
            status = (row.get("status") or "").strip().lower()
            if statuses and status not in statuses:
                continue
            rows.append({k: (row.get(k) or "").strip() for k in row})
    return rows
