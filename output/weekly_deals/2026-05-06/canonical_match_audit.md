# Canonical match audit: 2026-05-06 to 2026-05-12

Generated: 2026-07-14T15:15:35.456331+00:00

## Summary

- **Accepted:** 13
- **Rejected:** 1
- **Manual review:** 1
- **Families updated:** doritos_5_13oz, cheetos_regular_bags, sun_chips_7oz, oreo_family_size, pepsi_12packs, tillamook_ice_cream, hass_avocados_each, mangoes_each, peaches_per_lb, nectarines_per_lb, sweet_corn, butter_16oz, salmon

## Graph update safety check

### All-time low changes

- `sweet_corn` (Safeway): $0.5: Sweet Corn

### Graph preview changes

- `goldfish_bags` (Safeway): blocked $7.99: hard negative keyword/pattern hit: \b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b; ad product type 'goldfish_tub' is incompatible with canonical intent 'goldfish_crackers'; no family-size / eligible-size confirmation (needs one of: 4 to 8, 4-8, 4–8, 5.9, 6.1, 6-8, 6–8, 6 to 8, 6.6, 7.2, 8 oz, 8-oz, 8oz)
- `coca_cola_12packs` (Safeway): blocked $5.0: confidence 0.50 < min 0.70

### Blocked from tracker graph

- `goldfish_bags` (Safeway): **rejected**: 'Goldfish Crackers' @ $7.99
  - Reason: hard negative keyword/pattern hit: \b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b; ad product type 'goldfish_tub' is incompatible with canonical intent 'goldfish_crackers'; no family-size / eligible-size confirmation (needs one of: 4 to 8, 4-8, 4–8, 5.9, 6.1, 6-8, 6–8, 6 to 8, 6.6, 7.2, 8 oz, 8-oz, 8oz)
  - Hard negatives: \b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b
- `coca_cola_12packs` (Safeway): **manual_review**: 'Coca-Cola, Pepsi, 7UP' @ $5.0
  - Reason: confidence 0.50 < min 0.70

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `goldfish_bags`: 'Goldfish Crackers' @ $7.99: hard negative keyword/pattern hit: \b(?:2[0-9]|3[0-9]|4[0-9])\s*oz\b; ad product type 'goldfish_tub' is incompatible with canonical intent 'goldfish_crackers'; no family-size / eligible-size confirmation (needs one of: 4 to 8, 4-8, 4–8, 5.9, 6.1, 6-8, 6–8, 6 to 8, 6.6, 7.2, 8 oz, 8-oz, 8oz)

## Accepted matches

- `doritos_5_13oz` (Safeway): 'Lay’s, Doritos, Tostitos' @ $None (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `cheetos_regular_bags` (Safeway): "Cheetos Mac'n Cheese" @ $5.0 (confidence 0.90)
  - Display: Cheetos
  - Subtitle: regular size, 6.5–10 oz
- `sun_chips_7oz` (Safeway): 'SunChips 4.75 to 10.25-oz.' @ $None (confidence 0.70)
  - Display: Sun Chips
  - Subtitle: regular size, 7 oz
- `oreo_family_size` (Safeway): 'Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz.' @ $3.49 (confidence 1.00)
  - Display: Oreo cookies
  - Subtitle: family size, 10.68–18.71 oz
- `pepsi_12packs` (Safeway): 'Coca-Cola, Pepsi, 7UP' @ $5.0 (confidence 0.70)
  - Display: Pepsi
  - Subtitle: 12-pack, 12 fl oz cans
- `tillamook_ice_cream` (Safeway): 'Tillamook Ice Cream 48-oz. 3.99 MEMBER PRICE clip' @ $3.99 (confidence 0.70)
  - Display: Tillamook ice cream
  - Subtitle: 1.5 qt tubs or 4 ct bars when grouped
- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $1.67 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `mangoes_each` (Safeway): 'Large Mango' @ $1.0 (confidence 0.70)
  - Display: Mangoes
  - Subtitle: each or multi-buy
- `peaches_per_lb` (Safeway): 'Yellow Peaches' @ $2.99 (confidence 0.90)
  - Display: Peaches
  - Subtitle: per lb
- `nectarines_per_lb` (Safeway): 'Nectarines' @ $2.99 (confidence 0.90)
  - Display: Nectarines
  - Subtitle: per lb
- `sweet_corn` (Safeway): 'Sweet Corn' @ $0.5 (confidence 0.90)
  - Display: Sweet corn
  - Subtitle: each or multi-buy
- `butter_16oz` (Safeway): "Land O'Lakes Butter" @ $3.49 (confidence 0.85)
  - Display: Butter
  - Subtitle: 16 oz sticks / quarters; normalize to 16 oz
- `salmon` (Safeway): 'Fresh Atlantic Salmon Whole Fillet' @ $8.99 (confidence 1.00)
  - Display: Salmon
  - Subtitle: fresh salmon fillet
