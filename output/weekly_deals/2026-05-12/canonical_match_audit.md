# Canonical match audit: 2026-05-12 to 2026-05-19

Generated: 2026-07-14T14:22:10.547407+00:00

## Summary

- **Accepted:** 18
- **Rejected:** 1
- **Manual review:** 2
- **Families updated:** hass_avocados_each, mangoes_each, doritos_5_13oz, cheetos_regular_bags, ruffles_regular_bags, sun_chips_7oz, pepsi_12packs, simply_refrigerated_juice_lemonade, dreyers_tubs, strawberries_1_2lb, seedless_grapes_per_lb, sweet_corn, philadelphia_cream_cheese, nature_valley_bars, general_mills_cereal_regular, chicken_thigh_per_lb

## Graph update safety check

### All-time low changes

- `sun_chips_7oz` (Safeway): $1.99: Sunchips 7 oz., Lay's Potato Chips 5-8 oz., Kettle Potato Chips 5 oz.

### Graph preview changes

- `lays_potato_chips_regular` (Safeway): blocked $1.99: ambiguous match
- `berries_6oz` (Safeway): blocked $3.99: hard negative keyword/pattern hit: large pack; ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.); new all-time low $3.99 requires confidence >= 0.85 (got 0.58)
- `salmon` (Safeway): blocked $6.99: new all-time low $6.99 requires confidence >= 0.85 (got 0.75)

### Blocked from tracker graph

- `berries_6oz` (Safeway): **rejected**: 'Blueberries LARGE PACK' @ $3.99
  - Reason: hard negative keyword/pattern hit: large pack; ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.); new all-time low $3.99 requires confidence >= 0.85 (got 0.58)
  - Hard negatives: large pack
- `lays_potato_chips_regular` (Safeway): **manual_review**: "Sunchips 7 oz., Lay's Potato Chips 5-8 oz., Kettle Potato Chips 5 oz." @ $1.99
  - Reason: ambiguous match
- `salmon` (Safeway): **manual_review**: 'Waterfront Bistro Wild Alaskan Sockeye Salmon' @ $6.99
  - Reason: new all-time low $6.99 requires confidence >= 0.85 (got 0.75)

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `berries_6oz`: 'Blueberries LARGE PACK' @ $3.99: hard negative keyword/pattern hit: large pack; ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.); new all-time low $3.99 requires confidence >= 0.85 (got 0.58)

## Accepted matches

- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $1.25 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `mangoes_each` (Safeway): 'Mango' @ $1.25 (confidence 0.70)
  - Display: Mangoes
  - Subtitle: each or multi-buy
- `doritos_5_13oz` (Safeway): 'Doritos, Ruffles, Smartfood' @ $2.49 (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `cheetos_regular_bags` (Safeway): 'Cheetos, Tostitos, Fritos' @ $4.99 (confidence 0.70)
  - Display: Cheetos
  - Subtitle: regular size, 6.5–10 oz
- `ruffles_regular_bags` (Safeway): 'Doritos, Ruffles, Smartfood' @ $2.49 (confidence 0.70)
  - Display: Ruffles
  - Subtitle: regular size, 5–13 oz
- `sun_chips_7oz` (Safeway): "Sunchips 7 oz., Lay's Potato Chips 5-8 oz., Kettle Potato Chips 5 oz." @ $1.99 (confidence 0.70)
  - Display: Sun Chips
  - Subtitle: regular size, 7 oz
- `pepsi_12packs` (Safeway): 'Pepsi, Diet Pepsi, Starry' @ $1.85 (confidence 0.70)
  - Display: Pepsi
  - Subtitle: 12-pack, 12 fl oz cans
- `simply_refrigerated_juice_lemonade` (Safeway): 'Simply Orange Juice 52-oz. Selected varieties.' @ $8.99 (confidence 0.70)
  - Display: Simply juice
  - Subtitle: 46–52 fl oz bottles
- `dreyers_tubs` (Safeway): "Dreyer's Ice Cream 1.5 qt., Haagen-Dazs Ice Cream 14 oz., Novelties 3-6 ct., Nestle Outshine Fruit Bars 6-12 ct." @ $2.99 (confidence 0.70)
  - Display: Dreyer's ice cream
  - Subtitle: 1.5 qt tubs
- `strawberries_1_2lb` (Safeway): 'Strawberries LARGE PACK' @ $4.99 (confidence 0.70)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `seedless_grapes_per_lb` (Safeway): 'Red Seedless Grapes' @ $2.49 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $1.25 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `mangoes_each` (Safeway): 'Mango' @ $1.25 (confidence 0.70)
  - Display: Mangoes
  - Subtitle: each or multi-buy
- `sweet_corn` (Safeway): 'Sweet Corn' @ $0.5 (confidence 0.90)
  - Display: Sweet corn
  - Subtitle: each or multi-buy
- `philadelphia_cream_cheese` (Safeway): 'Philadelphia Cream Cheese' @ $2.49 (confidence 0.90)
  - Display: Philadelphia cream cheese
  - Subtitle: 7.5–8 oz tubs or bricks
- `nature_valley_bars` (Safeway): 'Nature Valley Bars' @ $1.99 (confidence 0.90)
  - Display: Nature Valley bars
  - Subtitle: roughly 5–12 ct boxes
- `general_mills_cereal_regular` (Safeway): 'General Mills Cheerios' @ $1.99 (confidence 0.70)
  - Display: General Mills cereal
  - Subtitle: regular size, 8.9–15 oz
- `chicken_thigh_per_lb` (Safeway): 'Open Nature Boneless Skinless Chicken Thighs' @ $5.99 (confidence 0.90)
  - Display: Chicken thighs
  - Subtitle: per lb
