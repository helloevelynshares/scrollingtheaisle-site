"""Typed models for deterministic deal assessment."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SubmittedOffer:
    """Confirmed structured offer fields — never reparsed from free text here."""

    price: float | None
    price_basis: str = "unknown"
    required_quantity: int | None = None
    promotion_type: str | None = None
    package_size: str | None = None
    product_text: str | None = None
    retailer: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "SubmittedOffer":
        raw = data or {}
        price_raw = raw.get("price")
        price: float | None
        try:
            price = float(price_raw) if price_raw is not None and price_raw != "" else None
        except (TypeError, ValueError):
            price = None
        qty_raw = raw.get("required_quantity")
        qty: int | None
        try:
            qty = int(qty_raw) if qty_raw is not None and qty_raw != "" else None
        except (TypeError, ValueError):
            qty = None
        return cls(
            price=price,
            price_basis=str(raw.get("price_basis") or "unknown").strip().lower() or "unknown",
            required_quantity=qty,
            promotion_type=(
                str(raw.get("promotion_type")).strip()
                if raw.get("promotion_type") not in (None, "")
                else None
            ),
            package_size=(
                str(raw.get("package_size")).strip()
                if raw.get("package_size") not in (None, "")
                else None
            ),
            product_text=(
                str(raw.get("product_text")).strip()
                if raw.get("product_text") not in (None, "")
                else None
            ),
            retailer=(
                str(raw.get("retailer")).strip()
                if raw.get("retailer") not in (None, "")
                else None
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedOffer:
    comparable_unit_price: float | None
    normalization_method: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparable_unit_price": self.comparable_unit_price,
            "normalization_method": self.normalization_method,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class PriceObservation:
    week_start: str
    unit_price: float
    promo_note: str | None = None
    offer_text: str | None = None
    confidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComparabilityResult:
    ok: bool
    reasons: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    feed_id: str | None = None
    tracker_id: str | None = None
    observation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "reasons": list(self.reasons),
            "notes": list(self.notes),
            "feed_id": self.feed_id,
            "tracker_id": self.tracker_id,
            "observation_count": self.observation_count,
        }


@dataclass(frozen=True)
class DealAssessment:
    """Grounded verdict from historical unit prices — deterministic only."""

    ok: bool
    verdict: str
    verdict_label: str
    headline: str
    summary: str
    tracker_id: str
    retailer: str
    feed_id: str | None
    submitted_offer: SubmittedOffer
    normalized_offer: NormalizedOffer
    comparability: ComparabilityResult
    evidence: dict[str, Any] = field(default_factory=dict)
    recent_observations: tuple[PriceObservation, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verdict": self.verdict,
            "verdict_label": self.verdict_label,
            "headline": self.headline,
            "summary": self.summary,
            "tracker_id": self.tracker_id,
            "retailer": self.retailer,
            "feed_id": self.feed_id,
            "submitted_offer": self.submitted_offer.to_dict(),
            "normalized_offer": self.normalized_offer.to_dict(),
            "comparability": self.comparability.to_dict(),
            "evidence": dict(self.evidence),
            "recent_observations": [o.to_dict() for o in self.recent_observations],
        }
