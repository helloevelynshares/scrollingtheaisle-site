# Canonical match audit: 2026-06-24 to 2026-06-30

Generated: 2026-07-15T15:56:43.176432+00:00

## Summary

- **Accepted:** 26
- **Rejected:** 4
- **Manual review:** 2
- **Families updated:** doritos_5_13oz, lays_potato_chips_regular, lays_party_size, kettle_brand_chips, ruffles_regular_bags, oreo_family_size, goldfish_bags, coca_cola_12packs, tillamook_ice_cream, strawberries_1_2lb, seedless_grapes_per_lb, cherries_per_lb, mangoes_each, peaches_per_lb, nectarines_per_lb, sweet_corn, eggs_dozen_normalized, butter_16oz, philadelphia_cream_cheese, chobani_yogurt_per_cup, kings_hawaiian_rolls, clif_bars, tri_tip_roast, salmon

## Graph update safety check

### All-time low changes

- `goldfish_bags` (Safeway): $2.0: Goldfish Crackers or Crisps 4 to 8-oz.
- `tillamook_ice_cream` (Safeway): $3.5: Tillamook Ice Cream
- `peaches_per_lb` (Safeway): $1.99: Yellow Peaches
- `nectarines_per_lb` (Safeway): $1.99: Nectarines

### Graph preview changes

- `lays_kettle_cooked` (Safeway): blocked $4.99: hard negative keyword/pattern hit: party size, family size; ad product type 'party_size' is incompatible with canonical intent 'kettle_cooked'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 132% vs prior week requires audit
- `lays_kettle_cooked` (Safeway): blocked $4.99: hard negative keyword/pattern hit: party size, family size; ad product type 'party_size' is incompatible with canonical intent 'kettle_cooked'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 132% vs prior week requires audit
- `nabisco_snack_crackers` (Safeway): blocked $2.49: no family-size / eligible-size confirmation (needs one of: family size, family-size, 11.5, 12 oz, 12.5, 13 oz, 14 oz, 11.5-14, 11.5 to 14, 10-14, 10 to 14)
- `pepsi_12packs` (Safeway): blocked $2.5: confidence 0.50 < min 0.70
- `dr_pepper_12packs` (Safeway): blocked $7.21: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'
- `berries_6oz` (Safeway): blocked $2.99: hard negative keyword/pattern hit: strawberries, 1 lb; ad product type 'strawberries_clamshell' is incompatible with canonical intent 'berries_6oz_clamshell'

### Blocked from tracker graph

- `lays_kettle_cooked` (Safeway): **rejected**: "Lay's Party Size Potato Chips or Kettle Cooked Chips or Rold Gold Selects or Chex Mix Family Size" @ $4.99
  - Reason: hard negative keyword/pattern hit: party size, family size; ad product type 'party_size' is incompatible with canonical intent 'kettle_cooked'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 132% vs prior week requires audit
  - Hard negatives: party size, family size
- `lays_kettle_cooked` (Safeway): **rejected**: "Lay's Party Size Potato Chips or Kettle Cooked Chips or Rold Gold Selects or Chex Mix Family Size" @ $4.99
  - Reason: hard negative keyword/pattern hit: party size, family size; ad product type 'party_size' is incompatible with canonical intent 'kettle_cooked'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 132% vs prior week requires audit
  - Hard negatives: party size, family size
- `dr_pepper_12packs` (Safeway): **rejected**: 'Dr Pepper' @ $7.21
  - Reason: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'
  - Hard negatives: 6\s*[- ]?pack.{0,20}bottle, 8\s*[- ]?pack.{0,20}bottle
- `berries_6oz` (Safeway): **rejected**: 'Strawberries 1 lb, Blueberries, Raspberries or Blackberries 6 oz' @ $2.99
  - Reason: hard negative keyword/pattern hit: strawberries, 1 lb; ad product type 'strawberries_clamshell' is incompatible with canonical intent 'berries_6oz_clamshell'
  - Hard negatives: strawberries, 1 lb
- `nabisco_snack_crackers` (Safeway): **manual_review**: 'Nabisco Snack Crackers' @ $2.49
  - Reason: no family-size / eligible-size confirmation (needs one of: family size, family-size, 11.5, 12 oz, 12.5, 13 oz, 14 oz, 11.5-14, 11.5 to 14, 10-14, 10 to 14)
- `pepsi_12packs` (Safeway): **manual_review**: 'Pepsi, Dr. Pepper, 7UP, A&W, Sunkist, Canada Dry, Squirt, Mug' @ $2.5
  - Reason: confidence 0.50 < min 0.70

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `lays_kettle_cooked`: "Lay's Party Size Potato Chips or Kettle Cooked Chips or Rold Gold Selects or Chex Mix Family Size" @ $4.99: hard negative keyword/pattern hit: party size, family size; ad product type 'party_size' is incompatible with canonical intent 'kettle_cooked'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 132% vs prior week requires audit
- `lays_kettle_cooked`: "Lay's Party Size Potato Chips or Kettle Cooked Chips or Rold Gold Selects or Chex Mix Family Size" @ $4.99: hard negative keyword/pattern hit: party size, family size; ad product type 'party_size' is incompatible with canonical intent 'kettle_cooked'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 132% vs prior week requires audit
- `dr_pepper_12packs`: 'Dr Pepper' @ $7.21: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'
- `berries_6oz`: 'Strawberries 1 lb, Blueberries, Raspberries or Blackberries 6 oz' @ $2.99: hard negative keyword/pattern hit: strawberries, 1 lb; ad product type 'strawberries_clamshell' is incompatible with canonical intent 'berries_6oz_clamshell'

## Accepted matches

- `doritos_5_13oz` (Safeway): 'Fritos, Ruffles, Doritos' @ $2.49 (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `lays_potato_chips_regular` (Safeway): "Lay's Potato Chips" @ $2.99 (confidence 1.00)
  - Display: Lay's potato chips
  - Subtitle: regular size, 5–13 oz
- `doritos_5_13oz` (Safeway): 'Fritos, Ruffles, Doritos' @ $2.49 (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `lays_potato_chips_regular` (Safeway): "Lay's Potato Chips" @ $2.99 (confidence 1.00)
  - Display: Lay's potato chips
  - Subtitle: regular size, 5–13 oz
- `lays_party_size` (Safeway): "Lay's Party Size Potato Chips or Kettle Cooked Chips or Rold Gold Selects or Chex Mix Family Size" @ $4.99 (confidence 0.70)
  - Display: Lay's Party Size
  - Subtitle: family size, 12.5–13 oz
- `kettle_brand_chips` (Safeway): 'Kettle Brand Potato Chips' @ $2.5 (confidence 0.90)
  - Display: Kettle Brand potato chips
  - Subtitle: regular size, 6.5–8.5 oz
- `ruffles_regular_bags` (Safeway): 'Fritos, Ruffles, Doritos' @ $2.49 (confidence 0.70)
  - Display: Ruffles
  - Subtitle: regular size, 5–13 oz
- `oreo_family_size` (Safeway): 'Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz.' @ $None (confidence 0.80)
  - Display: Oreo cookies
  - Subtitle: family size, 10.68–18.71 oz
- `goldfish_bags` (Safeway): 'Goldfish Crackers or Crisps 4 to 8-oz.' @ $2.0 (confidence 0.86)
  - Display: Goldfish
  - Subtitle: regular size, 6–8 oz
- `coca_cola_12packs` (Safeway): 'Coca-Cola 6-pk. 16.9-oz. btls. Selected varieties.' @ $5.99 (confidence 0.75)
  - Display: Coca-Cola
  - Subtitle: 12-pack, 12 fl oz cans
- `tillamook_ice_cream` (Safeway): 'Tillamook Ice Cream' @ $3.5 (confidence 0.90)
  - Display: Tillamook ice cream
  - Subtitle: 1.5 qt tubs or 4 ct bars when grouped
- `strawberries_1_2lb` (Safeway): 'Strawberries 1 lb, Blueberries, Raspberries or Blackberries 6 oz' @ $2.99 (confidence 0.70)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `seedless_grapes_per_lb` (Safeway): 'Red Seedless Grapes' @ $1.67 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `cherries_per_lb` (Safeway): 'Red Cherries' @ $5.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `mangoes_each` (Safeway): 'Large Mango, Cucumber, Red, Orange, Yellow' @ $1.25 (confidence 0.70)
  - Display: Mangoes
  - Subtitle: each or multi-buy
- `peaches_per_lb` (Safeway): 'Yellow Peaches' @ $1.99 (confidence 0.90)
  - Display: Peaches
  - Subtitle: per lb
- `nectarines_per_lb` (Safeway): 'Nectarines' @ $1.99 (confidence 0.90)
  - Display: Nectarines
  - Subtitle: per lb
- `sweet_corn` (Safeway): 'Sweet Corn' @ $0.5 (confidence 0.90)
  - Display: Sweet corn
  - Subtitle: each or multi-buy
- `eggs_dozen_normalized` (Safeway): 'Lucerne® Cage Free Eggs' @ $None (confidence 0.74)
  - Display: Lucerne Eggs
  - Subtitle: Lucerne large eggs; per dozen (18 ct scaled to 12)
- `butter_16oz` (Safeway): 'Lucerne Quarters Butter' @ $3.99 (confidence 1.00)
  - Display: Butter
  - Subtitle: 16 oz sticks / quarters; normalize to 16 oz
- `philadelphia_cream_cheese` (Safeway): 'Philadelphia Cream Cheese' @ $2.49 (confidence 0.90)
  - Display: Philadelphia cream cheese
  - Subtitle: 7.5–8 oz tubs or bricks
- `chobani_yogurt_per_cup` (Safeway): 'Chobani Greek, Less Sugar Yogurt 5.3 oz' @ $0.89 (confidence 0.70)
  - Display: Chobani yogurt cups
  - Subtitle: single cups or 4-packs; normalize per cup
- `kings_hawaiian_rolls` (Safeway): "King's Hawaiian Rolls" @ $4.99 (confidence 0.90)
  - Display: King's Hawaiian rolls
  - Subtitle: 12 ct / 12 oz
- `clif_bars` (Safeway): 'CLIF Bars' @ $1.25 (confidence 0.90)
  - Display: Clif Bars
  - Subtitle: per bar (multipack price ÷ bar count)
- `tri_tip_roast` (Safeway): "Chef's Counter Marinated Tri Tip Roast selected varieties" @ $10.99 (confidence 0.70)
  - Display: Tri-tip roast
  - Subtitle: per lb
- `salmon` (Safeway): 'Fresh Atlantic Salmon Portion' @ $5.99 (confidence 1.00)
  - Display: Salmon
  - Subtitle: fresh salmon fillet
