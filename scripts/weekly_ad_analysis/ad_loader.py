"""Load weekly ad rows from structured CSV or PDF text extraction."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AdOfferRow:
    ad_item_name: str
    raw_ad_text: str
    page_number: int | None
    advertised_price: float | None
    package_text: str | None
    package_size_min: float | None
    package_size_max: float | None
    package_unit: str | None
    price_basis: str | None
    promo_text: str | None
    promo_type_guess: str | None
    availability_type_guess: str | None
    split_product_text: str | None
    source: str


PRICE_RE = re.compile(
    r"(?:\$|¢)\s*(\d+(?:\.\d+)?)|(\d+)\s*/\s*\$?\s*(\d+(?:\.\d+)?)|"
    r"(\d+(?:\.\d+)?)\s*(?:¢|cents?)\s*(?:ea|each)?",
    re.I,
)
FRIDAY_RE = re.compile(r"\$5|5\s*friday|friday[,\s].*\$5", re.I)


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_split_offer_csv(path: Path, banner_filter: str | None = None) -> list[AdOfferRow]:
    rows: list[AdOfferRow] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            if banner_filter:
                banner = (raw.get("banner") or "").strip().lower()
                if banner and banner != banner_filter.strip().lower():
                    continue
            if raw.get("split_status") == "excluded":
                continue
            rows.append(
                AdOfferRow(
                    ad_item_name=raw.get("split_product_text")
                    or raw.get("raw_product_text")
                    or raw.get("raw_offer_text")
                    or "",
                    raw_ad_text=raw.get("raw_offer_text") or "",
                    page_number=int(raw["page_number"]) if raw.get("page_number") else None,
                    advertised_price=_parse_float(raw.get("advertised_price")),
                    package_text=raw.get("package_text") or None,
                    package_size_min=_parse_float(raw.get("package_size_min")),
                    package_size_max=_parse_float(raw.get("package_size_max")),
                    package_unit=raw.get("package_unit") or None,
                    price_basis=raw.get("price_basis") or None,
                    promo_text=raw.get("promo_text") or None,
                    promo_type_guess=raw.get("promo_type_guess") or None,
                    availability_type_guess=raw.get("availability_type_guess") or None,
                    split_product_text=raw.get("split_product_text") or None,
                    source="split_offer_items.csv",
                )
            )
    return rows


def _guess_price_from_text(text: str) -> tuple[float | None, str | None]:
    if re.search(r"buy\s+\d+\s+get\s+\d+", text, re.I) and not PRICE_RE.search(text):
        return None, "bogo"
    for match in PRICE_RE.finditer(text):
        if match.group(1):
            return float(match.group(1)), None
        if match.group(2) and match.group(3):
            count = float(match.group(2))
            total = float(match.group(3))
            if count > 0:
                return round(total / count, 4), "multi_buy"
        if match.group(4):
            return round(float(match.group(4)) / 100, 4), None
    return None, None


def _guess_promo_type(text: str) -> str | None:
    lower = text.lower()
    if "buy 1 get 1" in lower or "bogo" in lower:
        return "bogo"
    if re.search(r"buy\s+\d+\s+get\s+\d+", lower):
        return "buy_x_get_y"
    if re.search(r"\d+\s*/\s*\$", lower) or re.search(r"\d+\s+for\s+\$", lower):
        return "multi_buy"
    if "digital coupon" in lower or "clip" in lower:
        return "digital_coupon"
    if "member price" in lower or "member pack" in lower:
        return "member_price"
    if FRIDAY_RE.search(lower):
        return "five_dollar_friday"
    return "week_long"


def _guess_availability(text: str) -> str | None:
    lower = text.lower()
    if "friday" in lower and ("$5" in lower or "5 lb" in lower or "5 ea" in lower):
        return "friday_only"
    return "full_week"


def load_pdf_text_rows(pdf_path: Path) -> list[AdOfferRow]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF extraction requires pypdf. Install with: pip install pypdf"
        ) from exc

    reader = PdfReader(str(pdf_path))
    rows: list[AdOfferRow] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for line in text.splitlines():
            cleaned = " ".join(line.split())
            if len(cleaned) < 8:
                continue
            price, price_basis = _guess_price_from_text(cleaned)
            rows.append(
                AdOfferRow(
                    ad_item_name=cleaned[:120],
                    raw_ad_text=cleaned,
                    page_number=page_index,
                    advertised_price=price,
                    package_text=None,
                    package_size_min=None,
                    package_size_max=None,
                    package_unit=None,
                    price_basis=price_basis,
                    promo_text=cleaned,
                    promo_type_guess=_guess_promo_type(cleaned),
                    availability_type_guess=_guess_availability(cleaned),
                    split_product_text=cleaned,
                    source=f"pdf:{pdf_path.name}",
                )
            )
    return rows


def load_ad_rows(
    input_dir: Path,
    *,
    pdf_filename: str,
    banner_filter: str | None,
) -> list[AdOfferRow]:
    split_csv = input_dir / "split_offer_items.csv"
    if split_csv.is_file():
        return load_split_offer_csv(split_csv, banner_filter)

    pdf_path = input_dir / pdf_filename
    if pdf_path.is_file():
        return load_pdf_text_rows(pdf_path)

    raise FileNotFoundError(
        f"No ad input found in {input_dir}. Expected split_offer_items.csv or {pdf_filename}"
    )
