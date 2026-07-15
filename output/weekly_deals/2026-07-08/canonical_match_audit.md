# Canonical match audit: 2026-07-08 to 2026-07-14

Generated: 2026-07-15T15:56:43.183192+00:00

## Summary

- **Accepted:** 14
- **Rejected:** 5
- **Manual review:** 0
- **Families updated:** doritos_5_13oz, ruffles_regular_bags, nabisco_snack_crackers, chips_ahoy, oreo_family_size, seedless_grapes_per_lb, cherries_per_lb, hass_avocados_each, mangoes_each, plums_per_lb, sweet_corn, pillsbury_refrigerated_dough, chicken_breast_per_lb

## Graph update safety check

- No new all-time lows written this run.

### Graph preview changes

- `coca_cola_12packs` (Safeway): blocked $3.99: ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review; new all-time low $3.99 requires confidence >= 0.90 (got 0.55)
- `pepsi_12packs` (Safeway): blocked $3.99: hard negative keyword/pattern hit: 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review
- `berries_6oz` (Safeway): blocked $2.99: hard negative keyword/pattern hit: pint
- `butter_16oz` (Safeway): blocked $3.49: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'
- `salmon` (Safeway): blocked $4.99: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'

### Blocked from tracker graph

- `coca_cola_12packs` (Safeway): **rejected**: 'Coca-Cola, Pepsi' @ $3.99
  - Reason: ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review; new all-time low $3.99 requires confidence >= 0.90 (got 0.55)
- `pepsi_12packs` (Safeway): **rejected**: 'Coca-Cola, Pepsi' @ $3.99
  - Reason: hard negative keyword/pattern hit: 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review
  - Hard negatives: 8\s*[- ]?pack.{0,20}bottle
- `berries_6oz` (Safeway): **rejected**: 'Blueberries Pint, Raspberries' @ $2.99
  - Reason: hard negative keyword/pattern hit: pint
  - Hard negatives: pint
- `butter_16oz` (Safeway): **rejected**: "Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties." @ $3.49
  - Reason: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'
  - Hard negatives: spread, 13\s*to\s*15
- `salmon` (Safeway): **rejected**: 'Acme Smoked Nova Salmon 4 oz' @ $4.99
  - Reason: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'
  - Hard negatives: smoked, nova, 4 oz, acme, \b[234]\s*oz\b

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `pepsi_12packs`: 'Coca-Cola, Pepsi' @ $3.99: hard negative keyword/pattern hit: 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review
- `berries_6oz`: 'Blueberries Pint, Raspberries' @ $2.99: hard negative keyword/pattern hit: pint
- `butter_16oz`: "Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties." @ $3.49: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'
- `salmon`: 'Acme Smoked Nova Salmon 4 oz' @ $4.99: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'

## Accepted matches

- `doritos_5_13oz` (Safeway): 'Doritos Tortilla Chips' @ $2.5 (confidence 0.90)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `doritos_5_13oz` (Safeway): 'Doritos Tortilla Chips' @ $2.5 (confidence 0.90)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `ruffles_regular_bags` (Safeway): 'Ruffles Potato Chips' @ $2.5 (confidence 0.90)
  - Display: Ruffles
  - Subtitle: regular size, 5–13 oz
- `nabisco_snack_crackers` (Safeway): 'Nabisco Family Size Snack Crackers 10-14 oz' @ $3.49 (confidence 1.00)
  - Display: Wheat Thins, Triscuit & Chicken in a Biskit
  - Subtitle: family size, 11.5–14 oz
  - Manufacturer family: Nabisco
  - Allowed product lines: Wheat Thins, Triscuit, Chicken in a Biskit
  - Package: family_size_box, 11.5–14 oz
  - Eligible item examples: Wheat Thins Family Size Original 14 oz, Wheat Thins Family Size Reduced Fat 12.5 oz, Triscuit Family Size Original 12.5 oz, Triscuit Family Size Reduced Fat 11.5 oz, Triscuit Family Size Roasted Garlic 12.5 oz, Triscuit Family Size Rosemary & Olive Oil 12.5 oz, Chicken in a Biskit Family Size Original 12 oz, Chicken in a Biskit Family Size Ranch 12 oz
- `chips_ahoy` (Safeway): 'Nabisco Chips Ahoy! Cookies 7-13 oz. Selected varieties.' @ $3.49 (confidence 1.00)
  - Display: Chips Ahoy cookies
  - Subtitle: regular size, 9.5–13 oz
- `oreo_family_size` (Safeway): 'Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz.' @ $3.49 (confidence 1.00)
  - Display: Oreo cookies
  - Subtitle: family size, 10.68–18.71 oz
- `seedless_grapes_per_lb` (Safeway): 'Red Seedless Grapes' @ $2.99 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `cherries_per_lb` (Safeway): 'Red Cherries' @ $4.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $0.99 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `mangoes_each` (Safeway): 'Large Mango' @ $1.25 (confidence 0.70)
  - Display: Mangoes
  - Subtitle: each or multi-buy
- `plums_per_lb` (Safeway): 'Black Plums' @ $2.99 (confidence 0.90)
  - Display: Plums
  - Subtitle: per lb
- `sweet_corn` (Safeway): 'Sweet Corn' @ $0.5 (confidence 0.90)
  - Display: Sweet corn
  - Subtitle: each or multi-buy
- `pillsbury_refrigerated_dough` (Safeway): 'Pillsbury Grands! Biscuits, Cinnamon Rolls' @ $2.5 (confidence 0.70)
  - Display: Pillsbury ready-to-bake dough
  - Subtitle: 8–16.3 oz cans/tubes
- `chicken_breast_per_lb` (Safeway): 'O Organics Organic Fresh Boneless Skinless Chicken Breast Value Pack.' @ $5.99 (confidence 0.90)
  - Display: Chicken breast
  - Subtitle: per lb
