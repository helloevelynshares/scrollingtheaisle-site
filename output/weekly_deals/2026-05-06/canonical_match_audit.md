# Canonical match audit: 2026-05-06 to 2026-05-12

Generated: 2026-07-14T14:22:10.546381+00:00

## Summary

- **Accepted:** 15
- **Rejected:** 2
- **Manual review:** 1
- **Families updated:** hass_avocados_each, mangoes_each, doritos_5_13oz, cheetos_regular_bags, sun_chips_7oz, pepsi_12packs, simply_refrigerated_juice_lemonade, tillamook_ice_cream, cherries_per_lb, berries_6oz, sweet_corn, butter_16oz, salmon

## Graph update safety check

### All-time low changes

- `sweet_corn` (Safeway): $0.5: Sweet Corn
- `salmon` (Safeway): $8.99: Fresh Atlantic Salmon Whole Fillet

### Graph preview changes

- `oreo_family_size` (Safeway): blocked $3.49: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'oreo'
- `goldfish_bags` (Safeway): blocked $7.99: hard negative keyword/pattern hit: \b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b; ad product type 'goldfish_tub' is incompatible with canonical intent 'goldfish_crackers'; no family-size / eligible-size confirmation (needs one of: 4 to 8, 4-8, 4–8, 5.9, 6.1, 6-8, 6–8, 6 to 8, 6.6, 7.2, 8 oz, 8-oz, 8oz)
- `coca_cola_12packs` (Safeway): blocked $14.99: confidence 0.40 < min 0.70

### Blocked from tracker graph

- `oreo_family_size` (Safeway): **rejected**: 'Nabisco Family Size Oreo Cookies or Chips Ahoy! Cookies 13.1 to 20-oz.' @ $3.49
  - Reason: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'oreo'
  - Hard negatives: chips ahoy
- `goldfish_bags` (Safeway): **rejected**: 'Goldfish Crackers' @ $7.99
  - Reason: hard negative keyword/pattern hit: \b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b; ad product type 'goldfish_tub' is incompatible with canonical intent 'goldfish_crackers'; no family-size / eligible-size confirmation (needs one of: 4 to 8, 4-8, 4–8, 5.9, 6.1, 6-8, 6–8, 6 to 8, 6.6, 7.2, 8 oz, 8-oz, 8oz)
  - Hard negatives: \b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b
- `coca_cola_12packs` (Safeway): **manual_review**: 'Coca-Cola, Pepsi 24 pack, 12 oz. cans' @ $14.99
  - Reason: confidence 0.40 < min 0.70

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `oreo_family_size`: 'Nabisco Family Size Oreo Cookies or Chips Ahoy! Cookies 13.1 to 20-oz.' @ $3.49: hard negative keyword/pattern hit: chips ahoy; ad product type 'chips_ahoy' is incompatible with canonical intent 'oreo'
- `goldfish_bags`: 'Goldfish Crackers' @ $7.99: hard negative keyword/pattern hit: \b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b; ad product type 'goldfish_tub' is incompatible with canonical intent 'goldfish_crackers'; no family-size / eligible-size confirmation (needs one of: 4 to 8, 4-8, 4–8, 5.9, 6.1, 6-8, 6–8, 6 to 8, 6.6, 7.2, 8 oz, 8-oz, 8oz)

## Accepted matches

- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $1.67 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `mangoes_each` (Safeway): 'Large Mango' @ $1.0 (confidence 0.70)
  - Display: Mangoes
  - Subtitle: each or multi-buy
- `doritos_5_13oz` (Safeway): 'Lay’s, Doritos, Tostitos' @ $None (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `cheetos_regular_bags` (Safeway): "Cheetos Mac'n Cheese" @ $5.0 (confidence 0.90)
  - Display: Cheetos
  - Subtitle: regular size, 6.5–10 oz
- `sun_chips_7oz` (Safeway): 'SunChips 4.75 to 10.25-oz.' @ $None (confidence 0.70)
  - Display: Sun Chips
  - Subtitle: regular size, 7 oz
- `pepsi_12packs` (Safeway): 'Coca-Cola, Pepsi 24 pack, 12 oz. cans' @ $14.99 (confidence 0.70)
  - Display: Pepsi
  - Subtitle: 12-pack, 12 fl oz cans
- `simply_refrigerated_juice_lemonade` (Safeway): 'Simply Orange Juice' @ $8.99 (confidence 0.70)
  - Display: Simply juice
  - Subtitle: 46–52 fl oz bottles
- `tillamook_ice_cream` (Safeway): 'Tillamook Ice Cream 48-oz. 3.99 MEMBER PRICE clip' @ $3.99 (confidence 0.70)
  - Display: Tillamook ice cream
  - Subtitle: 1.5 qt tubs or 4 ct bars when grouped
- `cherries_per_lb` (Safeway): 'Red Cherries' @ $6.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `berries_6oz` (Safeway): 'Blackberries' @ $5.0 (confidence 0.98)
  - Display: Blueberries / raspberries / blackberries
  - Subtitle: 6 oz clamshells
- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $1.67 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `mangoes_each` (Safeway): 'Large Mango' @ $1.0 (confidence 0.70)
  - Display: Mangoes
  - Subtitle: each or multi-buy
- `sweet_corn` (Safeway): 'Sweet Corn' @ $0.5 (confidence 0.90)
  - Display: Sweet corn
  - Subtitle: each or multi-buy
- `butter_16oz` (Safeway): "Land O'Lakes Butter" @ $3.49 (confidence 0.85)
  - Display: Butter
  - Subtitle: 16 oz sticks / quarters; normalize to 16 oz
- `salmon` (Safeway): 'Fresh Atlantic Salmon Whole Fillet' @ $8.99 (confidence 1.00)
  - Display: Salmon
  - Subtitle: fresh salmon fillet
