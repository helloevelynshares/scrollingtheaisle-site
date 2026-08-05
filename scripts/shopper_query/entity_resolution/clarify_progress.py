"""Clarification progress fingerprints — prevent indefinite clarify loops."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ClarifyFingerprint:
    kind: str
    prompt: str
    reason: str
    matcher_status: str
    missing_fields: tuple[str, ...]
    product_text: str

    @property
    def digest(self) -> str:
        # Loop identity ignores product_text. Clarification answers are merged as
        # free text, so the product phrase often grows ("chips" → "chips chips ahoy")
        # while the same clarify prompt/reason repeats — that must still count as a loop.
        payload = {
            "kind": self.kind,
            "prompt": self.prompt,
            "reason": self.reason,
            "matcher_status": self.matcher_status,
            "missing_fields": list(self.missing_fields),
        }
        blob = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["digest"] = self.digest
        return d


def build_clarify_fingerprint(
    *,
    clarify_kind: str | None,
    clarify_prompt: str | None,
    reason: str | None,
    matcher_status: str | None,
    missing_fields: list[str] | tuple[str, ...] | None,
    product_text: str | None,
) -> ClarifyFingerprint:
    return ClarifyFingerprint(
        kind=str(clarify_kind or ""),
        prompt=str(clarify_prompt or "").strip(),
        reason=str(reason or ""),
        matcher_status=str(matcher_status or ""),
        missing_fields=tuple(missing_fields or ()),
        product_text=str(product_text or ""),
    )


def should_break_clarify_loop(
    current: ClarifyFingerprint,
    prior_digests: list[str] | tuple[str, ...] | None,
    *,
    max_repeats: int = 1,
) -> bool:
    """Return True when the same clarify fingerprint already occurred.

    ``max_repeats=1`` means the second identical clarify should break the loop
    (one retry is enough to prove non-progress).
    """
    if not prior_digests:
        return False
    digest = current.digest
    count = sum(1 for d in prior_digests if d == digest)
    return count >= max_repeats
