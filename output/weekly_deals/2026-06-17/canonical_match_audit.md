# Canonical match audit: 2026-06-17 to 2026-06-23

Generated: 2026-07-15T15:56:43.173782+00:00

## Summary

- **Accepted:** 20
- **Rejected:** 4
- **Manual review:** 1
- **Families updated:** doritos_5_13oz, lays_potato_chips_regular, lays_kettle_cooked, popcorners, cheetos_regular_bags, ruffles_regular_bags, sun_chips_7oz, cheez_it_crackers, goldfish_bags, breyers_ice_cream, strawberries_1_2lb, cherries_per_lb, sweet_corn, butter_16oz, tri_tip_roast, salmon

## Graph update safety check

### All-time low changes

- `cheetos_regular_bags` (Safeway): $2.49: Cheetos Mac'n Cheese
- `breyers_ice_cream` (Safeway): $2.5: Breyers Ice Cream 48 fl oz
- `cherries_per_lb` (Safeway): $2.99: Red Cherries
- `tri_tip_roast` (Safeway): $5.99: USDA Choice Boneless Beef Tri Tip Roast Untrimmed Twin Pack

### Graph preview changes

- `ritz_crackers` (Safeway): blocked $2.49: hard negative keyword/pattern hit: toasted chips
- `nabisco_snack_crackers` (Safeway): blocked $2.99: hard negative keyword/pattern hit: chips ahoy, cookies; ad product type 'chips_ahoy' is incompatible with canonical intent 'family_size_snack_crackers'
- `chips_ahoy` (Safeway): blocked $2.99: hard negative keyword/pattern hit: triscuit; ad product type 'triscuits' is incompatible with canonical intent 'chips_ahoy'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.65 needs review
- `coca_cola_12packs` (Safeway): blocked $1.5: confidence 0.55 < min 0.70
- `pepsi_12packs` (Safeway): blocked $5.99: hard negative keyword/pattern hit: 20 oz, gatorade, lipton, pure leaf, 20\s*oz, 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type 'single_bottle' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 364% vs prior week requires audit

### Blocked from tracker graph

- `ritz_crackers` (Safeway): **rejected**: 'Ritz Crackers or Toasted Chips, Nabisco Snack Crackers' @ $2.49
  - Reason: hard negative keyword/pattern hit: toasted chips
  - Hard negatives: toasted chips
- `nabisco_snack_crackers` (Safeway): **rejected**: 'Chips Ahoy! Cookies 7-13 oz, Nabisco Snack Crackers 3.5-9.1 oz, Triscuit Crackers 7-8.5 oz, Kettle Potato Chips 5-8.5 oz' @ $2.99
  - Reason: hard negative keyword/pattern hit: chips ahoy, cookies; ad product type 'chips_ahoy' is incompatible with canonical intent 'family_size_snack_crackers'
  - Hard negatives: chips ahoy, cookies
- `chips_ahoy` (Safeway): **rejected**: 'Chips Ahoy! Cookies 7-13 oz, Nabisco Snack Crackers 3.5-9.1 oz, Triscuit Crackers 7-8.5 oz, Kettle Potato Chips 5-8.5 oz' @ $2.99
  - Reason: hard negative keyword/pattern hit: triscuit; ad product type 'triscuits' is incompatible with canonical intent 'chips_ahoy'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.65 needs review
  - Hard negatives: triscuit
- `pepsi_12packs` (Safeway): **rejected**: 'Pepsi 12 Pack, 12 oz cans, 6 Pack, 16.9 oz bottles, Pepsi 100oz bottle, Lipton Tea 64 oz, Pure Leaf Tea 59 oz, Gatorade 8 pack, 20 oz' @ $5.99
  - Reason: hard negative keyword/pattern hit: 20 oz, gatorade, lipton, pure leaf, 20\s*oz, 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type 'single_bottle' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 364% vs prior week requires audit
  - Hard negatives: 20 oz, gatorade, lipton, pure leaf, 20\s*oz, 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz
- `coca_cola_12packs` (Safeway): **manual_review**: 'Coca-Cola, Pepsi' @ $1.5
  - Reason: confidence 0.55 < min 0.70

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `ritz_crackers`: 'Ritz Crackers or Toasted Chips, Nabisco Snack Crackers' @ $2.49: hard negative keyword/pattern hit: toasted chips
- `nabisco_snack_crackers`: 'Chips Ahoy! Cookies 7-13 oz, Nabisco Snack Crackers 3.5-9.1 oz, Triscuit Crackers 7-8.5 oz, Kettle Potato Chips 5-8.5 oz' @ $2.99: hard negative keyword/pattern hit: chips ahoy, cookies; ad product type 'chips_ahoy' is incompatible with canonical intent 'family_size_snack_crackers'
- `chips_ahoy`: 'Chips Ahoy! Cookies 7-13 oz, Nabisco Snack Crackers 3.5-9.1 oz, Triscuit Crackers 7-8.5 oz, Kettle Potato Chips 5-8.5 oz' @ $2.99: hard negative keyword/pattern hit: triscuit; ad product type 'triscuits' is incompatible with canonical intent 'chips_ahoy'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.65 needs review
- `pepsi_12packs`: 'Pepsi 12 Pack, 12 oz cans, 6 Pack, 16.9 oz bottles, Pepsi 100oz bottle, Lipton Tea 64 oz, Pure Leaf Tea 59 oz, Gatorade 8 pack, 20 oz' @ $5.99: hard negative keyword/pattern hit: 20 oz, gatorade, lipton, pure leaf, 20\s*oz, 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type 'single_bottle' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review; large price change 364% vs prior week requires audit

## Accepted matches

- `doritos_5_13oz` (Safeway): 'Ruffles, Doritos, SunChips' @ $2.49 (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `lays_potato_chips_regular` (Safeway): "Lay's Potato Chips" @ $2.15 (confidence 1.00)
  - Display: Lay's potato chips
  - Subtitle: regular size, 5–13 oz
- `lays_kettle_cooked` (Safeway): 'Kettle Cooked Chips' @ $2.15 (confidence 0.83)
  - Display: Lay's Kettle Cooked chips
  - Subtitle: regular size, 7.75–8 oz
- `popcorners` (Safeway): 'PopCorners' @ $2.49 (confidence 0.98)
  - Display: PopCorners
  - Subtitle: regular size, 5–10.75 oz
- `doritos_5_13oz` (Safeway): 'Ruffles, Doritos, SunChips' @ $2.49 (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `cheetos_regular_bags` (Safeway): "Cheetos Mac'n Cheese" @ $2.49 (confidence 0.90)
  - Display: Cheetos
  - Subtitle: regular size, 6.5–10 oz
- `lays_potato_chips_regular` (Safeway): "Lay's Potato Chips" @ $2.15 (confidence 1.00)
  - Display: Lay's potato chips
  - Subtitle: regular size, 5–13 oz
- `lays_kettle_cooked` (Safeway): 'Kettle Cooked Chips' @ $2.15 (confidence 0.83)
  - Display: Lay's Kettle Cooked chips
  - Subtitle: regular size, 7.75–8 oz
- `ruffles_regular_bags` (Safeway): 'Ruffles, Doritos, SunChips' @ $2.49 (confidence 0.70)
  - Display: Ruffles
  - Subtitle: regular size, 5–13 oz
- `sun_chips_7oz` (Safeway): 'Ruffles, Doritos, SunChips' @ $2.49 (confidence 0.70)
  - Display: Sun Chips
  - Subtitle: regular size, 7 oz
- `popcorners` (Safeway): 'PopCorners' @ $2.49 (confidence 0.98)
  - Display: PopCorners
  - Subtitle: regular size, 5–10.75 oz
- `cheez_it_crackers` (Safeway): "Cheez-It Crackers, Chex Mix, Bugles, Gardetto's, Nature Valley Crunchy Granola Bars, Fiber One Bars, Betty Crocker Fruit Snacks, Fruit by the Foot, Fruit Gushers, Fruit Roll-Ups, Mott's Fruit Flavored Snacks" @ $2.49 (confidence 0.70)
  - Display: Cheez-It crackers
  - Subtitle: regular size, 6.5–12.4 oz
- `goldfish_bags` (Safeway): 'Pepperidge Farm Goldfish Crackers' @ $3.49 (confidence 1.00)
  - Display: Goldfish
  - Subtitle: regular size, 6–8 oz
- `breyers_ice_cream` (Safeway): 'Breyers Ice Cream 48 fl oz' @ $2.5 (confidence 0.90)
  - Display: Breyers ice cream
  - Subtitle: tubs, including Carb Smart and Sunday Swirls
- `strawberries_1_2lb` (Safeway): 'Strawberries' @ $5.0 (confidence 0.90)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `cherries_per_lb` (Safeway): 'Red Cherries' @ $2.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `sweet_corn` (Safeway): 'Sweet Corn' @ $0.5 (confidence 0.90)
  - Display: Sweet corn
  - Subtitle: each or multi-buy
- `butter_16oz` (Safeway): 'Land O Lakes Butter' @ $3.49 (confidence 0.85)
  - Display: Butter
  - Subtitle: 16 oz sticks / quarters; normalize to 16 oz
- `tri_tip_roast` (Safeway): 'USDA Choice Boneless Beef Tri Tip Roast Untrimmed Twin Pack' @ $5.99 (confidence 0.70)
  - Display: Tri-tip roast
  - Subtitle: per lb
- `salmon` (Safeway): 'Fresh Atlantic Salmon Portion' @ $5.0 (confidence 1.00)
  - Display: Salmon
  - Subtitle: fresh salmon fillet
