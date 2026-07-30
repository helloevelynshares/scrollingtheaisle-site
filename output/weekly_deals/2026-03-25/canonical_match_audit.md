# Canonical match audit: 2026-03-25 to 2026-03-31

Generated: 2026-07-30T03:20:13.769267+00:00

## Summary

- **Accepted:** 36
- **Rejected:** 8
- **Manual review:** 10
- **Families updated:** doritos_5_13oz, cheetos_regular_bags, ruffles_regular_bags, ritz_toasted_chips, breyers_ice_cream, strawberries_1_2lb, seedless_grapes_per_lb, hass_avocados_each, philadelphia_cream_cheese, chobani_yogurt_per_cup, general_mills_cereal_family_size, post_cereal_regular, clif_bars, chicken_breast_per_lb, salmon, bell_peppers, chicken_wings_per_lb, pork_spare_ribs_per_lb

## Graph update safety check

- No new all-time lows written this run.

### Graph preview changes

- `kettle_brand_chips` (Safeway): blocked $2.5: confidence 0.55 < min 0.60
- `ritz_crackers` (Safeway): blocked $2.49: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'ritz_crackers'; mixed-item offer has conflicting package/container cues
- `chips_ahoy` (Safeway): blocked $2.49: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'chips_ahoy'; mixed-item offer has conflicting package/container cues; medium pattern confidence 0.70 needs review
- `pepsi_12packs` (Safeway): blocked $1.19: hard negative keyword/pattern hit: 2 liter, 2\s*[- ]?liter, gatorade; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; mixed-item offer has conflicting package/container cues
- `berries_6oz` (Safeway): blocked $2.5: missing required auto-match attribute(s): confirmation
- `butter_16oz` (Safeway): blocked $3.49: missing required auto-match attribute(s): product_form
- `kettle_brand_chips` (Safeway): blocked $2.5: confidence 0.55 < min 0.60
- `ritz_crackers` (Safeway): blocked $2.49: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'ritz_crackers'; mixed-item offer has conflicting package/container cues
- `chips_ahoy` (Safeway): blocked $2.49: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'chips_ahoy'; mixed-item offer has conflicting package/container cues; medium pattern confidence 0.70 needs review
- `pepsi_12packs` (Safeway): blocked $1.19: hard negative keyword/pattern hit: 2 liter, 2\s*[- ]?liter, gatorade; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; mixed-item offer has conflicting package/container cues
- `berries_6oz` (Safeway): blocked $2.5: missing required auto-match attribute(s): confirmation
- `butter_16oz` (Safeway): blocked $3.49: missing required auto-match attribute(s): product_form

### Blocked from tracker graph

- `ritz_crackers` (Safeway): **rejected**: 'Ritz Crackers 7.1 to 13.7 oz, Chips Ahoy! Cookies 7 to 13 oz' @ $2.49
  - Reason: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'ritz_crackers'; mixed-item offer has conflicting package/container cues
  - Hard negatives: chips ahoy
- `chips_ahoy` (Safeway): **rejected**: 'Ritz Crackers 7.1 to 13.7 oz, Chips Ahoy! Cookies 7 to 13 oz' @ $2.49
  - Reason: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'chips_ahoy'; mixed-item offer has conflicting package/container cues; medium pattern confidence 0.70 needs review
  - Hard negatives: ritz
- `pepsi_12packs` (Safeway): **rejected**: 'Pepsi 2 liter' @ $1.19
  - Reason: hard negative keyword/pattern hit: 2 liter, 2\s*[- ]?liter, gatorade; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; mixed-item offer has conflicting package/container cues
  - Hard negatives: 2 liter, 2\s*[- ]?liter, gatorade
- `general_mills_cereal_regular` (Safeway): **rejected**: 'Cheerios Family Size, Honey Nut Cheerios Family Size, Cinnamon Cheerios Protein Family Size' @ $None
  - Reason: hard negative keyword/pattern hit: family size, \bfamily\s+size\b; package size/form present but outside allowed_package_patterns; missing required auto-match attribute(s): package_size; multi-item variant list (or/comma) needs review
  - Hard negatives: family size, \bfamily\s+size\b
- `ritz_crackers` (Safeway): **rejected**: 'Ritz Crackers 7.1 to 13.7 oz, Chips Ahoy! Cookies 7 to 13 oz' @ $2.49
  - Reason: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'ritz_crackers'; mixed-item offer has conflicting package/container cues
  - Hard negatives: chips ahoy
- `chips_ahoy` (Safeway): **rejected**: 'Ritz Crackers 7.1 to 13.7 oz, Chips Ahoy! Cookies 7 to 13 oz' @ $2.49
  - Reason: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'chips_ahoy'; mixed-item offer has conflicting package/container cues; medium pattern confidence 0.70 needs review
  - Hard negatives: ritz
- `pepsi_12packs` (Safeway): **rejected**: 'Pepsi 2 liter' @ $1.19
  - Reason: hard negative keyword/pattern hit: 2 liter, 2\s*[- ]?liter, gatorade; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; mixed-item offer has conflicting package/container cues
  - Hard negatives: 2 liter, 2\s*[- ]?liter, gatorade
- `general_mills_cereal_regular` (Safeway): **rejected**: 'Cheerios Family Size, Honey Nut Cheerios Family Size, Cinnamon Cheerios Protein Family Size' @ $None
  - Reason: hard negative keyword/pattern hit: family size, \bfamily\s+size\b; package size/form present but outside allowed_package_patterns; missing required auto-match attribute(s): package_size; multi-item variant list (or/comma) needs review
  - Hard negatives: family size, \bfamily\s+size\b
- `kettle_brand_chips` (Safeway): **manual_review**: 'Kettle Chips' @ $2.5
  - Reason: confidence 0.55 < min 0.60
- `coca_cola_12packs` (Safeway): **manual_review**: 'Coca-Cola' @ $None
  - Reason: confidence 0.50 < min 0.70
- `dr_pepper_12packs` (Safeway): **manual_review**: 'Dr Pepper Products 12-pack 12-oz cans' @ $None
  - Reason: confidence 0.53 < min 0.70
- `berries_6oz` (Safeway): **manual_review**: 'Blueberries' @ $2.5
  - Reason: missing required auto-match attribute(s): confirmation
- `butter_16oz` (Safeway): **manual_review**: 'Lucerne Butter' @ $3.49
  - Reason: missing required auto-match attribute(s): product_form
- `kettle_brand_chips` (Safeway): **manual_review**: 'Kettle Chips' @ $2.5
  - Reason: confidence 0.55 < min 0.60
- `coca_cola_12packs` (Safeway): **manual_review**: 'Coca-Cola' @ $None
  - Reason: confidence 0.50 < min 0.70
- `dr_pepper_12packs` (Safeway): **manual_review**: 'Dr Pepper Products 12-pack 12-oz cans' @ $None
  - Reason: confidence 0.53 < min 0.70
- `berries_6oz` (Safeway): **manual_review**: 'Blueberries' @ $2.5
  - Reason: missing required auto-match attribute(s): confirmation
- `butter_16oz` (Safeway): **manual_review**: 'Lucerne Butter' @ $3.49
  - Reason: missing required auto-match attribute(s): product_form

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `ritz_crackers`: 'Ritz Crackers 7.1 to 13.7 oz, Chips Ahoy! Cookies 7 to 13 oz' @ $2.49: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'ritz_crackers'; mixed-item offer has conflicting package/container cues
- `chips_ahoy`: 'Ritz Crackers 7.1 to 13.7 oz, Chips Ahoy! Cookies 7 to 13 oz' @ $2.49: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'chips_ahoy'; mixed-item offer has conflicting package/container cues; medium pattern confidence 0.70 needs review
- `pepsi_12packs`: 'Pepsi 2 liter' @ $1.19: hard negative keyword/pattern hit: 2 liter, 2\s*[- ]?liter, gatorade; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; mixed-item offer has conflicting package/container cues
- `ritz_crackers`: 'Ritz Crackers 7.1 to 13.7 oz, Chips Ahoy! Cookies 7 to 13 oz' @ $2.49: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'ritz_crackers'; mixed-item offer has conflicting package/container cues
- `chips_ahoy`: 'Ritz Crackers 7.1 to 13.7 oz, Chips Ahoy! Cookies 7 to 13 oz' @ $2.49: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'chips_ahoy'; mixed-item offer has conflicting package/container cues; medium pattern confidence 0.70 needs review
- `pepsi_12packs`: 'Pepsi 2 liter' @ $1.19: hard negative keyword/pattern hit: 2 liter, 2\s*[- ]?liter, gatorade; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; mixed-item offer has conflicting package/container cues

## Accepted matches

- `doritos_5_13oz` (Safeway): 'Doritos Tortilla Chips' @ $1.99 (confidence 0.90)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `cheetos_regular_bags` (Safeway): 'Doritos or Cheetos 6-10.25 oz. Selected varieties.' @ $None (confidence 0.70)
  - Display: Cheetos
  - Subtitle: regular size, 6.5–10 oz
- `ruffles_regular_bags` (Safeway): 'Ruffles' @ $None (confidence 0.70)
  - Display: Ruffles
  - Subtitle: regular size, 5–13 oz
- `ritz_toasted_chips` (Safeway): 'Ritz Toasted Chips' @ $2.49 (confidence 0.70)
  - Display: Nabisco Ritz Toasted Chips
  - Subtitle: regular size, 7–8.1 oz
- `breyers_ice_cream` (Safeway): 'Breyers Ice Cream 48 oz' @ $3.49 (confidence 0.90)
  - Display: Breyers ice cream
  - Subtitle: tubs, including Carb Smart and Sunday Swirls
- `strawberries_1_2lb` (Safeway): 'Strawberries' @ $2.5 (confidence 0.90)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `seedless_grapes_per_lb` (Safeway): 'Red Seedless Grapes' @ $2.49 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $1.67 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `philadelphia_cream_cheese` (Safeway): 'Philadelphia Cream Cheese' @ $2.49 (confidence 0.90)
  - Display: Philadelphia cream cheese
  - Subtitle: 7.5–8 oz tubs or bricks
- `chobani_yogurt_per_cup` (Safeway): 'Chobani Greek, Less Sugar' @ $0.99 (confidence 0.88)
  - Display: Chobani yogurt cups
  - Subtitle: single cups or 4×5.3 oz multipacks (incl. Layered); normalize per cup
- `general_mills_cereal_family_size` (Safeway): 'Cheerios Family Size, Honey Nut Cheerios Family Size, Cinnamon Cheerios Protein Family Size' @ $None (confidence 0.70)
  - Display: General Mills cereal (family size)
  - Subtitle: family size, 15–18 oz
- `post_cereal_regular` (Safeway): 'Post Cereal 10 to 14.75 oz' @ $1.99 (confidence 0.90)
  - Display: Post cereal
  - Subtitle: regular size, 10–16 oz
- `clif_bars` (Safeway): 'CLIF Bars' @ $0.19 (confidence 0.90)
  - Display: Clif Bars
  - Subtitle: per bar (multipack price ÷ bar count)
- `chicken_breast_per_lb` (Safeway): 'Signature SELECT® Chicken Breasts 24 oz' @ $1.99 (confidence 0.70)
  - Display: Chicken breast
  - Subtitle: per lb
- `salmon` (Safeway): 'Fresh Atlantic Salmon Whole Fillet' @ $5.0 (confidence 1.00)
  - Display: Salmon
  - Subtitle: fresh salmon fillet
- `bell_peppers` (Safeway): 'Green Bell Peppers' @ $1.0 (confidence 0.90)
  - Display: Bell peppers
  - Subtitle: each or multi-buy
- `chicken_wings_per_lb` (Safeway): 'Chicken Wings' @ $6.99 (confidence 0.93)
  - Display: Chicken wings
  - Subtitle: per lb (party wings)
- `pork_spare_ribs_per_lb` (Safeway): 'St. Louis Style Pork Back Ribs' @ $4.99 (confidence 0.70)
  - Display: Pork spare ribs
  - Subtitle: per lb
- `doritos_5_13oz` (Safeway): 'Doritos Tortilla Chips' @ $1.99 (confidence 0.90)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `cheetos_regular_bags` (Safeway): 'Doritos or Cheetos 6-10.25 oz. Selected varieties.' @ $None (confidence 0.70)
  - Display: Cheetos
  - Subtitle: regular size, 6.5–10 oz
- `ruffles_regular_bags` (Safeway): 'Ruffles' @ $None (confidence 0.70)
  - Display: Ruffles
  - Subtitle: regular size, 5–13 oz
- `ritz_toasted_chips` (Safeway): 'Ritz Toasted Chips' @ $2.49 (confidence 0.70)
  - Display: Nabisco Ritz Toasted Chips
  - Subtitle: regular size, 7–8.1 oz
- `breyers_ice_cream` (Safeway): 'Breyers Ice Cream 48 oz' @ $3.49 (confidence 0.90)
  - Display: Breyers ice cream
  - Subtitle: tubs, including Carb Smart and Sunday Swirls
- `strawberries_1_2lb` (Safeway): 'Strawberries' @ $2.5 (confidence 0.90)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `seedless_grapes_per_lb` (Safeway): 'Red Seedless Grapes' @ $2.49 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $1.67 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `philadelphia_cream_cheese` (Safeway): 'Philadelphia Cream Cheese' @ $2.49 (confidence 0.90)
  - Display: Philadelphia cream cheese
  - Subtitle: 7.5–8 oz tubs or bricks
- `chobani_yogurt_per_cup` (Safeway): 'Chobani Greek, Less Sugar' @ $0.99 (confidence 0.88)
  - Display: Chobani yogurt cups
  - Subtitle: single cups or 4×5.3 oz multipacks (incl. Layered); normalize per cup
- `general_mills_cereal_family_size` (Safeway): 'Cheerios Family Size, Honey Nut Cheerios Family Size, Cinnamon Cheerios Protein Family Size' @ $None (confidence 0.70)
  - Display: General Mills cereal (family size)
  - Subtitle: family size, 15–18 oz
- `post_cereal_regular` (Safeway): 'Post Cereal 10 to 14.75 oz' @ $1.99 (confidence 0.90)
  - Display: Post cereal
  - Subtitle: regular size, 10–16 oz
- `clif_bars` (Safeway): 'CLIF Bars' @ $0.19 (confidence 0.90)
  - Display: Clif Bars
  - Subtitle: per bar (multipack price ÷ bar count)
- `chicken_breast_per_lb` (Safeway): 'Signature SELECT® Chicken Breasts 24 oz' @ $1.99 (confidence 0.70)
  - Display: Chicken breast
  - Subtitle: per lb
- `salmon` (Safeway): 'Fresh Atlantic Salmon Whole Fillet' @ $5.0 (confidence 1.00)
  - Display: Salmon
  - Subtitle: fresh salmon fillet
- `bell_peppers` (Safeway): 'Green Bell Peppers' @ $1.0 (confidence 0.90)
  - Display: Bell peppers
  - Subtitle: each or multi-buy
- `chicken_wings_per_lb` (Safeway): 'Chicken Wings' @ $6.99 (confidence 0.93)
  - Display: Chicken wings
  - Subtitle: per lb (party wings)
- `pork_spare_ribs_per_lb` (Safeway): 'St. Louis Style Pork Back Ribs' @ $4.99 (confidence 0.70)
  - Display: Pork spare ribs
  - Subtitle: per lb
