"""Conservative shopper-language normalization (preprocessing only).

Transforms common verbal / slang forms into weekly-ad-like wording so the
deterministic parser can reuse existing regexes. Does NOT resolve product
identity or map ambiguous package synonyms to trackers.

Every transformation records: source_text, replacement, normalization_type,
confidence.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

WORD_NUMBERS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "a": 1,
    "an": 1,
}


@dataclass(frozen=True)
class NormalizationStep:
    source_text: str
    replacement: str
    normalization_type: str
    confidence: float
    span_start: int | None = None
    span_end: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizationResult:
    original: str
    normalized: str
    steps: list[NormalizationStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "original": self.original,
            "normalized": self.normalized,
            "steps": [s.to_dict() for s in self.steps],
        }


def _word_to_int(token: str) -> int | None:
    return WORD_NUMBERS.get(token.lower().strip())


def _replace_span(
    text: str,
    start: int,
    end: int,
    replacement: str,
    *,
    steps: list[NormalizationStep],
    norm_type: str,
    confidence: float,
) -> str:
    source = text[start:end]
    steps.append(
        NormalizationStep(
            source_text=source,
            replacement=replacement,
            normalization_type=norm_type,
            confidence=confidence,
            span_start=start,
            span_end=end,
        )
    )
    return text[:start] + replacement + text[end:]


def _normalize_casing_punct(text: str, steps: list[NormalizationStep]) -> str:
    # Collapse curly quotes / weird dashes; keep content.
    mapping = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }
    out = text
    for src, dst in mapping.items():
        if src in out:
            out = out.replace(src, dst)
            steps.append(
                NormalizationStep(
                    source_text=src,
                    replacement=dst,
                    normalization_type="punctuation",
                    confidence=1.0,
                )
            )
    # Squeeze whitespace
    squeezed = re.sub(r"[ \t]+", " ", out).strip()
    if squeezed != out.strip():
        steps.append(
            NormalizationStep(
                source_text=out,
                replacement=squeezed,
                normalization_type="whitespace",
                confidence=1.0,
            )
        )
    return squeezed


def _normalize_verbal_prices(text: str, steps: list[NormalizationStep]) -> str:
    """five bucks → $5; two fifty → $2.50; 5 bucks → $5."""
    out = text

    # "two fifty" / "two-fifty" → $2.50 (dollars + cents shorthand)
    pattern_fifty = re.compile(
        r"\b("
        + "|".join(WORD_NUMBERS)
        + r"|\d{1,2})\s*-?\s*fifty\b",
        re.I,
    )

    def repl_fifty(m: re.Match[str]) -> str:
        raw = m.group(0)
        left = m.group(1)
        dollars = _word_to_int(left)
        if dollars is None:
            try:
                dollars = int(left)
            except ValueError:
                return raw
        replacement = f"${dollars}.50"
        steps.append(
            NormalizationStep(
                source_text=raw,
                replacement=replacement,
                normalization_type="verbal_price",
                confidence=0.9,
            )
        )
        return replacement

    out = pattern_fifty.sub(repl_fifty, out)

    # "five bucks" / "5 bucks" / "three dollars"
    pattern_bucks = re.compile(
        r"\b("
        + "|".join(WORD_NUMBERS)
        + r"|\d{1,3}(?:\.\d{1,2})?)\s+(?:bucks?|dollars?)\b",
        re.I,
    )

    def repl_bucks(m: re.Match[str]) -> str:
        raw = m.group(0)
        left = m.group(1)
        amount = _word_to_int(left)
        if amount is None:
            try:
                amount_f = float(left)
            except ValueError:
                return raw
        else:
            amount_f = float(amount)
        replacement = f"${amount_f:g}" if amount_f != int(amount_f) else f"${int(amount_f)}"
        # Prefer two-decimal when fractional
        if abs(amount_f - round(amount_f)) > 1e-9:
            replacement = f"${amount_f:.2f}"
        elif amount_f >= 1:
            replacement = f"${int(amount_f)}"
        steps.append(
            NormalizationStep(
                source_text=raw,
                replacement=replacement,
                normalization_type="bucks_to_dollar",
                confidence=0.95,
            )
        )
        return replacement

    out = pattern_bucks.sub(repl_bucks, out)

    # "a dollar" / "one dollar fifty" already partially covered; "99 cents"
    cents = re.compile(r"\b(\d{1,2})\s*cents?\b", re.I)

    def repl_cents(m: re.Match[str]) -> str:
        raw = m.group(0)
        n = int(m.group(1))
        replacement = f"${n / 100:.2f}"
        steps.append(
            NormalizationStep(
                source_text=raw,
                replacement=replacement,
                normalization_type="cents_to_dollar",
                confidence=0.9,
            )
        )
        return replacement

    out = cents.sub(repl_cents, out)
    return out


def _normalize_bogo(text: str, steps: list[NormalizationStep]) -> str:
    out = text
    patterns = [
        (
            re.compile(
                r"\b(?:buy\s+one\s+get\s+one(?:\s+free)?|b1g1(?:f)?|buy\s+1\s+get\s+1(?:\s+free)?)\b",
                re.I,
            ),
            "BOGO",
            0.95,
        ),
        (
            re.compile(r"\bbuy\s+one\s+get\s+one\s+free\b", re.I),
            "BOGO",
            0.95,
        ),
    ]
    for pattern, replacement, conf in patterns:
        m = pattern.search(out)
        while m:
            out = _replace_span(
                out,
                m.start(),
                m.end(),
                replacement,
                steps=steps,
                norm_type="bogo_synonym",
                confidence=conf,
            )
            m = pattern.search(out)
    return out


def _normalize_required_qty(text: str, steps: list[NormalizationStep]) -> str:
    """need to buy 3 / gotta get 4 / have to buy three → when you buy N."""
    out = text

    def qty_token(raw: str) -> str | None:
        n = _word_to_int(raw)
        if n is not None:
            return str(n)
        if re.fullmatch(r"\d+", raw):
            return raw
        return None

    pattern = re.compile(
        r"\b(?:need\s+to\s+buy|gotta\s+(?:get|buy)|have\s+to\s+buy|must\s+buy|"
        r"required\s+to\s+buy|you\s+(?:need|have)\s+to\s+buy)\s+"
        r"(" + "|".join(WORD_NUMBERS) + r"|\d+)\b",
        re.I,
    )

    def repl(m: re.Match[str]) -> str:
        raw = m.group(0)
        q = qty_token(m.group(1))
        if q is None:
            return raw
        replacement = f"when you buy {q}"
        steps.append(
            NormalizationStep(
                source_text=raw,
                replacement=replacement,
                normalization_type="required_quantity_wording",
                confidence=0.9,
            )
        )
        return replacement

    out = pattern.sub(repl, out)

    # "3 for five bucks" already handled if bucks normalized first; also
    # "two for $5" with word number on the left.
    n_for = re.compile(
        r"\b(" + "|".join(k for k in WORD_NUMBERS if k not in {"a", "an"}) + r")\s+for\s+",
        re.I,
    )

    def repl_n_for(m: re.Match[str]) -> str:
        raw = m.group(0)
        n = _word_to_int(m.group(1))
        if n is None:
            return raw
        replacement = f"{n} for "
        steps.append(
            NormalizationStep(
                source_text=raw,
                replacement=replacement,
                normalization_type="multi_buy_wording",
                confidence=0.9,
            )
        )
        return replacement

    out = n_for.sub(repl_n_for, out)
    return out


def _normalize_package_synonyms_note_only(text: str, steps: list[NormalizationStep]) -> str:
    """Record package synonyms without auto-mapping to a tracker size.

    Leaves 'big box' in place (parser marks ambiguity) but records the cue.
    """
    for m in re.finditer(r"\b(big\s+box|large\s+pack|family\s+sized?)\b", text, re.I):
        steps.append(
            NormalizationStep(
                source_text=m.group(0),
                replacement=m.group(0),  # no silent rewrite
                normalization_type="package_synonym_observed",
                confidence=0.5,
                span_start=m.start(),
                span_end=m.end(),
            )
        )
    # Mild: "family sized" → "family size" (harmless morphology)
    out = text
    m = re.search(r"\bfamily\s+sized\b", out, re.I)
    if m:
        out = _replace_span(
            out,
            m.start(),
            m.end(),
            "family size",
            steps=steps,
            norm_type="package_morphology",
            confidence=0.85,
        )
    return out


def normalize_shopper_query(raw_query: str) -> NormalizationResult:
    original = raw_query or ""
    steps: list[NormalizationStep] = []
    text = _normalize_casing_punct(original, steps)
    text = _normalize_verbal_prices(text, steps)
    text = _normalize_bogo(text, steps)
    text = _normalize_required_qty(text, steps)
    text = _normalize_package_synonyms_note_only(text, steps)
    return NormalizationResult(original=original, normalized=text, steps=steps)
