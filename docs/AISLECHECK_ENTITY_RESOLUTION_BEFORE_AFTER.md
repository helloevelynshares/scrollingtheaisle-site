# Entity-resolution before/after comparison

Date: 2026-08-04  
Branch: `feature/aislecheck-catalog-entity-resolution`  
Baseline: `main` @ Chips Ahoy one-off (`369b0ef`)

## Probe set (14 shopper queries)

| Metric | Before (`main`) | After (this branch) |
|---|---|---|
| continue | 8 | 9 |
| clarify | 3 | 5 |
| unsupported | 3 | 0 |
| Wrong-confident multi-family continues | **2** | **0** |
| Protected phrases | 144 (pre-trim) | **47** (post-audit) |
| Catalog eval | — | **276/276**, wrong-confident **0** |
| Reachability | — | **86/86** |

## Safety deltas (selected)

| Query | Before | After |
|---|---|---|
| Cheetos (brand-only) | continue → regular bags | **clarify** (regular vs party) |
| Post cereal (no size) | continue → regular | **clarify** (regular vs giant) |
| General Mills cereal (no size) | continue → regular | **clarify** (regular vs family) |
| Family-size General Mills cereal | unsupported | **continue** family size |
| Goldfish | clarify | **continue** |
| Lay's Classic | unsupported | **continue** |
| Chobani (brand-only) | unsupported | **clarify** (cups vs tub) |
| Chips Ahoy | continue | continue |
| Generic chips | clarify | clarify |

## Holdout precision/recall

Frozen holdout runner depends on local `scripts/holdout_labeler/` (untracked). Production modules do **not** import it (`forbidden_import_violations=0`). Holdout precision/recall is unchanged by this branch because deal matching / assessment policy was not modified — only AisleCheck shopper entity resolution.

## Gate summary

- Protected-phrase audit failures: **0**
- Catalog-resolution eval failures: **0**
- Wrong-confident matches on eval: **0**
- Clarify loop termination: **ok**
- No merge / deploy / structured-clarify public enablement
