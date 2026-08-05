# AisleCheck entity resolution — root-cause map

Date: 2026-08-04  
Branch: `feature/aislecheck-catalog-entity-resolution`  
Scope: catalog-wide hardening (Chips Ahoy is the motivating bug, not the finish line).

## Production flow (current)

```
POST /api/aislecheck
  → run_aislecheck_query (aislecheck_contract.py)
      → process_query (pipeline.py)
          1. normalize_shopper_query     # verbal prices, BOGO, qty phrasing
          2. parse_shopper_query         # retailer, product_text, price, promo, size,
                                         # brand-unspecified / package-synonym ambiguities
          3. match_parsed_query          # ProductionMatcherFacade ← YAML includes/excludes
                                         # + canonical_match_rules eligibility
          4. decide_behavior             # continue | clarify | unsupported | invalid
      → build_aislecheck_response        # clarify_kind / clarify_prompt / plausible_trackers
```

Frontend clarification (`aislecheck.js`):
- Missing-field answer → `original_query + " " + answer` → full reparse
- Product pick → synthesize new free-text from label + prior extracted fields → full reparse
- No structured session state on the API (`session_id` is correlation only)

## Failure modes → root causes

| Failure mode | What happens | Root cause class |
|---|---|---|
| Generic-token misclassification | “Chips Ahoy” → `product_brand_unspecified:chips` | Heuristic matches a category token inside a multiword brand; no protected-phrase layer |
| Missing alias | Shopper uses a short name not in YAML `include` | Catalog language gap; includes written for ad copy, not shopper speech |
| Overly strict include | Bare brand fails match until “cookies” / flavor appended | Family name auto-include may require extra tokens; short forms never listed |
| Duplicate candidate ambiguity | Multiple families accept / review | Genuine overlap OR missing keep_separate / eligibility |
| Clarification answer not merged | Answer reparsed as free text only | By design today; no structured patch API |
| Repeated clarification, no progress | Same prompt after answer | Reparse hits same heuristic; no progress/fingerprint guard |
| Unreachable canonical tracker | No reasonable NL query selects family | Include phrases too ad-specific; brand-only unsafe or blocked |
| Package/form ambiguity | Regular vs party size / tub vs cup | Correct clarify path when multiple trackers share a brand |
| Unsafe brand-only matching | Short brand maps to wrong family | Must remain `multiple_tracker_candidates` or clarify |

## Chips Ahoy (already patched on main)

**Fixed (partial, one-off on main):**
- Parser excludes `\bchips\s*ahoy\b` from chips brand-unspecified (one-off regex)
- YAML includes bare `Chips Ahoy`
- Unique matcher hit no longer blocked by brand-unspecified (systemic behavior change)

**Catalog-wide on this branch (replaces one-offs):**
- Protected-phrase registry derived from catalog + overlays
- Optional family YAML keys: `aliases`, `protected_phrases`, `clarification`
- Shopper alias layer (does not alter weekly-ad include matching)
- Clarify fingerprints ignore free-text product drift; frontend sends `prior_clarify_digests`
- Full-catalog reachability + collision audits under `evals/entity-resolution/`

## Design principles for this branch

1. **Authoritative catalog** = `data/canonical_tracker_families.yaml` (+ match rules + generated history for reachability context). No handwritten tracker ID list.
2. **Protected phrases** derived from the catalog (and optional committed overlays), never per-product `if` branches in the parser.
3. **Safe clarification > wrong continue.**
4. **Brand-only resolve only when classification is `exact_alias_safe`.**
5. **Loop prevention:** detect non-progressing clarify cycles server-side; return a terminal clarify/unsupported instead of repeating the same prompt.
6. **Do not** merge to main or enable a new public structured-clarification UI in this branch’s activation step.

## Authoritative sources

| Source | Role |
|---|---|
| `data/canonical_tracker_families.yaml` | Active tracker catalog, includes, keep_separate |
| `config/canonical_match_rules.yaml` | Package/type eligibility gates |
| `src/data/weeklyAdPrices.generated.ts` / Vons twin | Historical observation presence |
| `src/data/canonicalTrackerFamilies.generated.ts` | UI mirror (not match source of truth) |
| `data/product_matching/corrections.yaml` | Eval/human notes only (not live match) |
| Untracked `scripts/holdout_labeler/` | Must not be a production dependency |

## Implementation map (this branch)

1. `scripts/shopper_query/entity_resolution/` — catalog load, language profiles, collisions, reachability, clarify progress
2. `data/entity_resolution/phrase_overlays.yaml` — optional safe protected phrases / aliases that cannot live cleanly in family YAML yet
3. Optional YAML fields on families: `aliases`, `protected_phrases`, `entity_resolution` (backward compatible)
4. Parser uses protected-phrase registry instead of one-off brand exceptions
5. Contract/pipeline fingerprint for clarify loops
6. Committed audits under `evals/entity-resolution/` + `docs/AISLECHECK_TRACKER_LANGUAGE_COVERAGE.md`
