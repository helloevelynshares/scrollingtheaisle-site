# deterministic-baseline-v1 product policy

Frozen at public main `44ff557` / Render backend `0096b89`.  
No LLM in the public flow.

## Interpretation

- **Deterministic parsing** via `scripts/shopper_query/` (normalize → parse → match → route). No free-text LLM.
- **Supported offer forms:** simple sale price; multi-buy / N-for; BOGO / buy-X-get-Y when reference price present; `$X each when buying N`; optional retailer and package cues.
- **Unsupported:** products with no tracker match after clarification; absent catalog items (e.g. Apple Jacks) → `unsupported` (not a wrong continue).
- **Invalid-input:** empty/oversized query; conflicting prices; requests that cannot form a usable structured offer for assessment (`invalid_offer`).

## Entity resolution

- **Exact aliases / includes:** YAML `include` phrases plus shopper alias layer (`shopper_aliases.py`) for common shopper wording. Aliases do **not** change weekly-ad include matching.
- **Protected phrases:** 47 catalog-derived + overlay phrases (`protected-phrase-audit.json`); suppress generic category heuristics inside brand names (e.g. Chips Ahoy ≠ generic chips).
- **Multi-family brands:** brand-only queries across package/form siblings clarify (Cheetos, Chobani, General Mills cereal, Post, Lay’s).
- **Package/form boundaries:** sibling gate groups package sizes; keep_separate links prevent cross-category house-brand collapse (e.g. Lucerne).
- **Generic-category safeguard:** bare “chips” / unspecified chip brand → clarify (missing brand), never quiet match.
- **Wrong-confident-match policy:** offline catalog eval requires `wrong_confident_match_count == 0` (276/276 at freeze).

## Clarification

- **Triggered when:** ambiguous tracker match; missing required field (brand, price, package when required); underspecified generics.
- **Candidate options:** up to three `plausible_trackers` for `ambiguous_product` when structured clarification is enabled.
- **Field preservation:** price, promotion, retailer, and package extracted fields remain on clarify responses and through candidate rebuild when present.
- **Loop detection:** `clarify_fingerprint` + client `prior_clarify_digests`; identical non-progress → `clarify_loop_broken`.
- **None of these:** client marks `user_rejected_candidates` → unsupported safe exit.
- **Terminal unsupported:** with structured clarification off, loop break → plain unsupported (`clarify_loop_terminal`); with flag on, terminal may remain clarify with candidates when available.

## Assessment

Source and rules: `docs/AISLECHECK_ASSESSMENT_POLICY.md` / `scripts/deal_assessment/policy.py` (`aislecheck_history_v1`).

- **Historical source:** committed generated Safeway/Vons weekly unit-price series (same as price-tracker charts).
- **Comparability:** non-null price; confidence present and not `"low"`; retailer series never mixed; package out-of-range → `not_comparable`.
- **0–1 observations:** `insufficient_data`
- **2–3 observations:** `limited_data` (evidence only; no strong stock-up/good/fair label)
- **4+ observations:** full benchmark verdicts
- **Typical price:** median of chartable unit prices
- **Verdict categories:** all-time low / near all-time low / strong / normal / weak sale (plus insufficient/limited/not_comparable/invalid)
- **No-verdict cases:** insufficient, limited, not_comparable, invalid_offer, history load failure (HTTP 500; no fabricated series)

## Safety

- Abstain rather than invent trackers or history.
- No fabricated observation series.
- Deterministic verdict from structured fields only (assess never reparses free text).
- `llm_used` / `llm_invoked` = false for this baseline.
- Public API strips `debug`; errors sanitized; no raw query in Cloudflare analytics beacon.
- Privacy: do not log raw shopper query text in production debug logs.
