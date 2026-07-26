# Highlight → Tracker Coverage Report

Generated: 2026-07-26
Purpose: Durable inventory of historical Safeway video-transcript highlighted products and final coverage decisions from the Jul 2026 catalog expansion.

**Grain:** one row per unique normalized highlighted product (`unique_normalized_highlighted_products` = 89), matching `data/review/highlight_tracker_coverage_audit.yaml`. Weeks/transcript fidelity preserved via `weeks` + `source_transcript` on each row (not one row per week mention).

**Machine-readable inventory:** `data/product_matching/highlight_mentions.jsonl`

**Source of truth for decisions:** coverage audit + `implementation_status` + `data/product_matching/highlight_tracker_review.yaml`. No products were reclassified during this consolidation.

## Headline stats

| Metric | Count |
| --- | ---: |
| Unique highlighted products | 89 |
| Now covered (working tracker family) | 70 |
| Unresolved / review queue | 18 |
| Removed / deliberately not tracking | 1 |
| Canonical families before expansion | 68 |
| Canonical families after expansion (incl. shrimp) | 84 |
| Canonical families after shrimp removal (current YAML) | 83 |

Family-count provenance: PROJECT_NOTES highlight expansion (+16 families incl. `shrimp_16oz`: 68→84) then shrimp full removal (→83). Verified: current `data/canonical_tracker_families.yaml` has **83** families; `shrimp_16oz` absent.

### Action breakdown

- `alias_added`: 5
- `ambiguous_or_unresolved`: 17
- `eligibility_or_exclusion_added`: 1
- `existing_family`: 49
- `new_family_created`: 17

### Review status breakdown

- `covered`: 70
- `removed`: 1
- `review_queue`: 18

## Implementation evidence (already completed)

- Implemented on: 2026-07-25
- New families retained (15): `cape_cod_chips`, `smartfood_popcorn`, `pringles`, `snyders_pretzels`, `frito_lay_multipack_chips`, `pop_tarts`, `kellogg_breakfast_bars`, `betty_crocker_fruit_snacks`, `waterloo_sparkling_water`, `bell_peppers`, `chicken_wings_per_lb`, `beef_short_ribs_per_lb`, `pork_spare_ribs_per_lb`, `oscar_mayer_hot_dogs`, `cake_mix`
- Aliases extended: lays_potato_chips_regular (Poppables); cheez_it_crackers (Ultimate Snack Mix); general_mills_cereal_* (Honey Nut Cheerios); chobani_yogurt_per_cup (Layered/Flip); breyers_ice_cream (Sundae Swirls); oreo_family_size (Family Size phrasing)
- Families split/restructured: none
- Eval coverage: `data/product_matching/eval_cases.jsonl` highlight_* cases (accept/reject/alias/manual_review)
- Shrimp: added then removed; audit relationship `deliberately not tracked`

## Products still lacking a working tracker

These unique highlighted products do **not** have a confirmed, working canonical tracker mapping (or are intentionally untracked).

### Intentionally not tracking

| Product | Status | Notes |
| --- | --- | --- |
| Shrimp | `removed` | Highlight expansion briefly added shrimp_16oz; fully removed 2026-07-26 (low audience engagement). Deliberately not tracked — do not set SAFEWAY baseline. |

### Review queue / unresolved (no confirmed working tracker)

| Product | Tentative family | Review queue id | Why |
| --- | --- | --- | --- |
| Kerrygold butter | `butter_16oz` | `kerrygold_8oz_butter` | No family split performed (implementation families_split_or_restructured=[]). Comparable 16 oz stays on butter_16oz; 8 oz specialty policy in review. |
| Pork (cut unclear) | `—` | `pork_cut_unclear` | Review queue — identify cut from source week |
| Safeway All-American footlong | `—` | `safeway_all_american_footlong` | Review queue; 0 CSV hits; may be not appropriate for staples tracker |
| Hawaiian Brand chips | `—` | `hawaiian_brand_chips` | Review queue — 0 potato-chip ad hits; do not confuse with kings_hawaiian_rolls |
| Dot's Pretzels | `—` | `dots_pretzels` | Review queue — 0 pretzel hits (CSV Dots = candy) |
| Unidentified kimchi/dill pickle chips | `—` | `kimchi_dill_pickle_unidentified_chips` | Review queue; Lay's Dill Pickle already under lays if confirmed Lay's |
| Special K cereal | `—` | `special_k_cereal_vs_bars` | Review queue — sampled ads show Special K bars not cereal boxes |
| Baskin-Robbins ice cream | `—` | `baskin_robbins_novelties` | Review queue — possible baskin_robbins_novelties after confirmation |
| Unidentified frozen Greek yogurt brand | `—` | `frozen_greek_yogurt_brand_unknown` | Review queue — identify brand from source |
| Unidentified $1.67 snack | `—` | `unidentified_1_67_snack` | Review queue |
| Unidentified both-of-these $0.99 | `—` | `unidentified_both_099` | Review queue (possible Chobani cups) |
| Unidentified 10-pack kids snack | `—` | `unidentified_10pack_kids_snack` | Review queue; nabisco excludes 10-pack snack packs |
| Unidentified $5.99→$2 stacked promo | `—` | `unidentified_599_to_2_stack` | Review queue |
| Unidentified produce 8 vs Costco 6 | `hass_avocados_each` | `unidentified_produce_8_vs_costco_6` | Tentative family_id hass_avocados_each only if video confirms avocados |
| Unidentified 2 lb vs 5 lb produce | `—` | `unidentified_2lb_vs_5lb_produce` | Review queue |
| Unidentified crunch-dipped protein snack | `—` | `crunch_dipped_protein_snack` | Review queue |
| ASR oil family size | `oreo_family_size` | `asr_oil_family_size` | Tentative Oreo mapping; eval rejects bare ASR auto-match |
| ASR Cake pod | `—` | `asr_cake_pod` | Review queue |

**Count lacking working tracker (excl. intentional shrimp removal):** 18
**Count intentionally not tracking:** 1

### Review-queue hygiene on already-covered products

These review-queue entries confirm ASR phrases for products that already have families; they are **not** additional uncovered products:

- `siders_asr_snyders` → covered product **Snyder's pretzels**
- `asr_nutrigrain_country_bars` → covered product **Nutri-Grain bars**

## Disagreements flagged (not silently resolved)

1. Kerrygold butter: audit relationship "existing family may need splitting" but no split was implemented; queued as kerrygold_8oz_butter — flagged, not silently resolved
2. Fruit by the Foot: audit relationship is "covered by existing umbrella family" with family_id null, but betty_crocker_fruit_snacks did not exist pre-expansion — action recorded as new_family_created
3. Audit summary.requiring_new_families=17 but product relationships now show 16 'genuinely missing family' (+ shrimp reclassified to 'deliberately not tracked'). Summary field appears stale post-shrimp update.

## Schema notes (`highlight_mentions.jsonl`)

Each line is a JSON object with:

- `normalized_highlighted_product`, `raw_product_mentions`, `source_transcript`, `weeks`
- `canonical_family_id` (final / tentative)
- `action`: `existing_family` | `alias_added` | `eligibility_or_exclusion_added` | `new_family_created` | `family_split` | `ambiguous_or_unresolved`
- `evidence`, `audit_relationship`, `audit_recommendation`, `audit_confidence`, `package`
- `review_status`: `covered` | `review_queue` | `unresolved` | `removed`
- `review_queue_id` when present in `highlight_tracker_review.yaml`
- `notes`, `sources`

## Related files

- `data/review/highlight_tracker_coverage_audit.yaml`
- `data/product_matching/highlight_tracker_review.yaml`
- `data/canonical_tracker_families.yaml`
- `data/product_matching/eval_cases.jsonl`
- `docs/PROJECT_NOTES.md` (Safeway transcript highlight → tracker coverage expansion; Shrimp deliberately dropped)

