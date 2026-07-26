"""Isolated product-matching scaffold (eval + corrections).

This package wraps the production weekly-ad matcher for dry-run evaluation.
It does NOT write generated TypeScript, CSV outputs, or Supabase records, and
it is not wired into generate_weekly_ad_prices.py yet.
"""

from product_matching.engine import MatchDecision, match_offer_row
from product_matching.cases import EvalCase, load_eval_cases

__all__ = [
    "EvalCase",
    "MatchDecision",
    "load_eval_cases",
    "match_offer_row",
]
