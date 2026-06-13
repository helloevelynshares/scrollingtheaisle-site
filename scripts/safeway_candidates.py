"""Parse Safeway pgmsearch JSON into flat candidate rows for manual SKU selection."""

from __future__ import annotations

from typing import Any


def extract_product_docs(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not payload or not isinstance(payload, dict):
        return []
    primary = payload.get("primaryProducts")
    if not isinstance(primary, dict):
        return []
    inner = primary.get("response")
    if not isinstance(inner, dict):
        return []
    docs = inner.get("docs")
    if not isinstance(docs, list):
        return []
    return [doc for doc in docs if isinstance(doc, dict)]


def _price_from_doc(doc: dict[str, Any]) -> str:
    price = doc.get("price") or doc.get("basePrice") or doc.get("currentPrice")
    if isinstance(price, dict):
        for key in ("amount", "price", "value", "display"):
            if price.get(key) is not None:
                return str(price[key])
        return ""
    if price is not None:
        return str(price)
    return ""


def doc_to_candidate_row(
    doc: dict[str, Any],
    *,
    rank: int,
    canonical_id: str,
    display_name: str,
    search_query: str,
    content_theme: str,
) -> dict[str, str]:
    return {
        "canonical_id": canonical_id,
        "display_name": display_name,
        "search_query": search_query,
        "content_theme": content_theme,
        "candidate_rank": str(rank),
        "product_name": str(doc.get("name") or doc.get("productName") or doc.get("title") or ""),
        "price": _price_from_doc(doc),
        "pid": str(doc.get("productId") or doc.get("id") or doc.get("sku") or ""),
        "upc": str(doc.get("upc") or doc.get("UPC") or doc.get("upcCode") or ""),
        "size": str(doc.get("size") or doc.get("unitQuantity") or doc.get("unitOfMeasure") or ""),
    }


CANDIDATE_CSV_FIELDS = (
    "canonical_id",
    "display_name",
    "search_query",
    "content_theme",
    "candidate_rank",
    "product_name",
    "price",
    "pid",
    "upc",
    "size",
)
