"""Load durable human corrections (read-only for production matcher)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CORRECTIONS_PATH = ROOT / "data" / "product_matching" / "corrections.yaml"


@dataclass(frozen=True)
class Correction:
    id: str
    family_id: str
    offer_text: str
    decision: str
    kind: str = "note"
    source: str = ""
    status: str = "open"
    notes: str = ""
    package_text: str = ""


def load_corrections(path: Path | None = None) -> list[Correction]:
    """Load corrections.yaml. Production matching must not call this yet."""
    path = path or DEFAULT_CORRECTIONS_PATH
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle) or {}
    rows = doc.get("corrections") or []
    out: list[Correction] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        out.append(
            Correction(
                id=str(raw.get("id") or "").strip(),
                family_id=str(raw.get("family_id") or "").strip(),
                offer_text=str(raw.get("offer_text") or "").strip(),
                decision=str(raw.get("decision") or "").strip().lower(),
                kind=str(raw.get("kind") or "note"),
                source=str(raw.get("source") or ""),
                status=str(raw.get("status") or "open"),
                notes=str(raw.get("notes") or "").strip(),
                package_text=str(raw.get("package_text") or ""),
            )
        )
    return [c for c in out if c.id and c.family_id and c.offer_text]


def open_baseline_bugs(path: Path | None = None) -> list[Correction]:
    return [
        c
        for c in load_corrections(path)
        if c.kind == "baseline_bug" and c.status == "open"
    ]


def corrections_as_dicts(path: Path | None = None) -> list[dict[str, Any]]:
    return [
        {
            "id": c.id,
            "family_id": c.family_id,
            "offer_text": c.offer_text,
            "decision": c.decision,
            "kind": c.kind,
            "source": c.source,
            "status": c.status,
            "notes": c.notes,
        }
        for c in load_corrections(path)
    ]
