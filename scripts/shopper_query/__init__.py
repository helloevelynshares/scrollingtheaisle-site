"""Deterministic shopper-query experiment (no LLM, no deal verdict).

Adapts weekly-ad offer-text regexes + production canonical matching to
natural-language shopper questions. See docs/PROJECT_NOTES.md.
"""

from shopper_query.pipeline import process_query
from shopper_query.schema import ParsedShopperQuery

__all__ = ["ParsedShopperQuery", "process_query"]
