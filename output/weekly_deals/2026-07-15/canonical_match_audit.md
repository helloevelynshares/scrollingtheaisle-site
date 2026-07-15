# Canonical match audit: 2026-07-15 to 2026-07-21

Generated: 2026-07-15T15:56:43.186755+00:00

## Summary

- **Accepted:** 20
- **Rejected:** 3
- **Manual review:** 0
- **Families updated:** doritos_5_13oz, lays_potato_chips_regular, lays_kettle_cooked, popcorners, ritz_crackers, cheez_it_crackers, chips_ahoy, goldfish_bags, keebler_sandwich_crackers, cherries_per_lb, hass_avocados_each, sweet_corn, eggs_dozen_normalized, butter_16oz, chobani_yogurt_per_cup, tri_tip_roast

## Graph update safety check

### All-time low changes

- `chips_ahoy` (Safeway): $2.49: Nabisco Chips Ahoy! Cookies 9.5 to 13-oz. Selected varieties.
- `goldfish_bags` (Safeway): $1.99: Pepperidge Farm Goldfish Crackers or Crisps 4 to 8-oz. Selected varieties.

### Graph preview changes

- `coca_cola_12packs` (Safeway): blocked $3.99: ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review; new all-time low $3.99 requires confidence >= 0.90 (got 0.55)
- `pepsi_12packs` (Safeway): blocked $13.88: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review
- `berries_6oz` (Safeway): blocked $5.0: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.)

### Blocked from tracker graph

- `coca_cola_12packs` (Safeway): **rejected**: 'Coca-Cola Products, Smartwater' @ $3.99
  - Reason: ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review; new all-time low $3.99 requires confidence >= 0.90 (got 0.55)
- `pepsi_12packs` (Safeway): **rejected**: 'Pepsi 12-pack, 12-oz. cans or 8-pack, 12-oz. bottles. Lipton Tea 12-pack, 16.9-oz. Pure Leaf 6-pack, 16.9-oz. Gatorade 8' @ $13.88
  - Reason: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review
  - Hard negatives: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle
- `berries_6oz` (Safeway): **rejected**: 'Blueberries' @ $5.0
  - Reason: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.)

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `pepsi_12packs`: 'Pepsi 12-pack, 12-oz. cans or 8-pack, 12-oz. bottles. Lipton Tea 12-pack, 16.9-oz. Pure Leaf 6-pack, 16.9-oz. Gatorade 8' @ $13.88: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review

## Accepted matches

- `doritos_5_13oz` (Safeway): 'Doritos' @ $2.49 (confidence 0.90)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `lays_potato_chips_regular` (Safeway): "Lay's Potato Chips" @ $2.49 (confidence 1.00)
  - Display: Lay's potato chips
  - Subtitle: regular size, 5–13 oz
- `lays_kettle_cooked` (Safeway): "Lay's Kettle Cooked Chips" @ $2.49 (confidence 1.00)
  - Display: Lay's Kettle Cooked chips
  - Subtitle: regular size, 7.75–8 oz
- `popcorners` (Safeway): 'PopCorners' @ $2.49 (confidence 0.98)
  - Display: PopCorners
  - Subtitle: regular size, 5–10.75 oz
- `doritos_5_13oz` (Safeway): 'Doritos' @ $2.49 (confidence 0.90)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `lays_potato_chips_regular` (Safeway): "Lay's Potato Chips" @ $2.49 (confidence 1.00)
  - Display: Lay's potato chips
  - Subtitle: regular size, 5–13 oz
- `lays_kettle_cooked` (Safeway): "Lay's Kettle Cooked Chips" @ $2.49 (confidence 1.00)
  - Display: Lay's Kettle Cooked chips
  - Subtitle: regular size, 7.75–8 oz
- `popcorners` (Safeway): 'PopCorners' @ $2.49 (confidence 0.98)
  - Display: PopCorners
  - Subtitle: regular size, 5–10.75 oz
- `ritz_crackers` (Safeway): 'Ritz Crackers or Cheez-It Crackers Selected varieties' @ $2.49 (confidence 0.83)
  - Display: Ritz crackers
  - Subtitle: regular size, 8.8–13.7 oz
- `cheez_it_crackers` (Safeway): 'Ritz Crackers or Cheez-It Crackers Selected varieties' @ $2.49 (confidence 0.70)
  - Display: Cheez-It crackers
  - Subtitle: regular size, 6.5–12.4 oz
- `chips_ahoy` (Safeway): 'Nabisco Chips Ahoy! Cookies 9.5 to 13-oz. Selected varieties.' @ $2.49 (confidence 1.00)
  - Display: Chips Ahoy cookies
  - Subtitle: regular size, 9.5–13 oz
- `goldfish_bags` (Safeway): 'Pepperidge Farm Goldfish Crackers or Crisps 4 to 8-oz. Selected varieties.' @ $1.99 (confidence 0.89)
  - Display: Goldfish
  - Subtitle: regular size, 6–8 oz
- `keebler_sandwich_crackers` (Safeway): 'Keebler Sandwich Crackers 8 ct.' @ $3.0 (confidence 0.90)
  - Display: Keebler sandwich crackers
  - Subtitle: 8-pack boxes
- `cherries_per_lb` (Safeway): 'Red Cherries' @ $2.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `hass_avocados_each` (Safeway): 'Hass Avocado' @ $1.25 (confidence 0.70)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `sweet_corn` (Safeway): 'Sweet Corn' @ $0.25 (confidence 0.90)
  - Display: Sweet corn
  - Subtitle: each or multi-buy
- `eggs_dozen_normalized` (Safeway): 'Lucerne® Large Eggs 18-CT.' @ $1.99 (confidence 1.00)
  - Display: Lucerne Eggs
  - Subtitle: Lucerne large eggs; per dozen (18 ct scaled to 12)
- `butter_16oz` (Safeway): 'Lucerne Butter Quarters Salted' @ $3.99 (confidence 1.00)
  - Display: Butter
  - Subtitle: 16 oz sticks / quarters; normalize to 16 oz
- `chobani_yogurt_per_cup` (Safeway): 'Chobani Greek, Less Sugar' @ $1.0 (confidence 0.70)
  - Display: Chobani yogurt cups
  - Subtitle: single cups or 4-packs; normalize per cup
- `tri_tip_roast` (Safeway): 'Chef’s Marinated Tri Tip Roast Boneless' @ $10.99 (confidence 0.70)
  - Display: Tri-tip roast
  - Subtitle: per lb
