# Canonical match audit: 2026-07-15 to 2026-07-21

Generated: 2026-07-15T04:12:03.113049+00:00

## Summary

- **Accepted:** 46
- **Rejected:** 16
- **Manual review:** 0
- **Families updated:** doritos_5_13oz, ritz_crackers, cheez_it_crackers, goldfish_bags, keebler_sandwich_crackers, cherries_per_lb, hass_avocados_each, sweet_corn, eggs_dozen_normalized, butter_16oz, chobani_yogurt_per_cup, tri_tip_roast, strawberries_1_2lb, seedless_grapes_per_lb, peaches_per_lb, nectarines_per_lb, fage_cups, general_mills_cereal_regular, chicken_breast_per_lb, salmon

## Graph update safety check

### All-time low changes

- `general_mills_cereal_regular` (Vons): $1.29: Cheerios Cereal 8.9 to 12 oz, Cinnamon Toast Crunch Cereal 12 oz
- `general_mills_cereal_regular` (Vons): $1.29: Cheerios Cereal 8.9 to 12 oz, Cinnamon Toast Crunch Cereal 12 oz

### Graph preview changes

- `coca_cola_12packs` (Safeway): blocked $3.99: ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review; new all-time low $3.99 requires confidence >= 0.90 (got 0.55)
- `pepsi_12packs` (Safeway): blocked $13.88: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review
- `berries_6oz` (Safeway): blocked $5.0: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.)
- `ritz_crackers` (Vons): blocked $5.0: hard negative keyword/pattern hit: oreo; ad product type 'oreo' is incompatible with canonical intent 'ritz_crackers'; medium pattern confidence 0.73 needs review; large price change 101% vs prior week requires audit
- `oreo_family_size` (Vons): blocked $5.0: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'oreo'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.55 needs review
- `pepsi_12packs` (Vons): blocked $2.5: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.40 needs review
- `dr_pepper_12packs` (Vons): blocked $2.5: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'
- `berries_6oz` (Vons): blocked $3.99: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.); large price change 303% vs prior week requires audit
- `coca_cola_12packs` (Safeway): blocked $3.99: ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review; new all-time low $3.99 requires confidence >= 0.90 (got 0.55)
- `pepsi_12packs` (Safeway): blocked $13.88: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review
- `berries_6oz` (Safeway): blocked $5.0: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.)
- `ritz_crackers` (Vons): blocked $5.0: hard negative keyword/pattern hit: oreo; ad product type 'oreo' is incompatible with canonical intent 'ritz_crackers'; medium pattern confidence 0.73 needs review; large price change 101% vs prior week requires audit
- `oreo_family_size` (Vons): blocked $5.0: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'oreo'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.55 needs review
- `pepsi_12packs` (Vons): blocked $2.5: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.40 needs review
- `dr_pepper_12packs` (Vons): blocked $2.5: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'
- `berries_6oz` (Vons): blocked $3.99: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.); large price change 303% vs prior week requires audit

### Blocked from tracker graph

- `coca_cola_12packs` (Safeway): **rejected**: 'Coca-Cola Products, Smartwater' @ $3.99
  - Reason: ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review; new all-time low $3.99 requires confidence >= 0.90 (got 0.55)
- `pepsi_12packs` (Safeway): **rejected**: 'Pepsi 12-pack, 12-oz. cans or 8-pack, 12-oz. bottles. Lipton Tea 12-pack, 16.9-oz. Pure Leaf 6-pack, 16.9-oz. Gatorade 8' @ $13.88
  - Reason: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review
  - Hard negatives: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle
- `berries_6oz` (Safeway): **rejected**: 'Blueberries' @ $5.0
  - Reason: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.)
- `ritz_crackers` (Vons): **rejected**: 'Nabisco Family Size! Oreo Cookies 12.2-20 oz or Ritz Crackers 17.8-20.6 oz' @ $5.0
  - Reason: hard negative keyword/pattern hit: oreo; ad product type 'oreo' is incompatible with canonical intent 'ritz_crackers'; medium pattern confidence 0.73 needs review; large price change 101% vs prior week requires audit
  - Hard negatives: oreo
- `oreo_family_size` (Vons): **rejected**: 'Nabisco Family Size! Oreo Cookies 12.2-20 oz or Ritz Crackers 17.8-20.6 oz' @ $5.0
  - Reason: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'oreo'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.55 needs review
  - Hard negatives: ritz
- `pepsi_12packs` (Vons): **rejected**: 'Pepsi, 7UP, Canada Dry, A&W, Sunkist, Squirt' @ $2.5
  - Reason: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.40 needs review
  - Hard negatives: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz
- `dr_pepper_12packs` (Vons): **rejected**: 'Dr Pepper' @ $2.5
  - Reason: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'
  - Hard negatives: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz
- `berries_6oz` (Vons): **rejected**: 'Blueberries' @ $3.99
  - Reason: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.); large price change 303% vs prior week requires audit
- `coca_cola_12packs` (Safeway): **rejected**: 'Coca-Cola Products, Smartwater' @ $3.99
  - Reason: ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; medium pattern confidence 0.55 needs review; new all-time low $3.99 requires confidence >= 0.90 (got 0.55)
- `pepsi_12packs` (Safeway): **rejected**: 'Pepsi 12-pack, 12-oz. cans or 8-pack, 12-oz. bottles. Lipton Tea 12-pack, 16.9-oz. Pure Leaf 6-pack, 16.9-oz. Gatorade 8' @ $13.88
  - Reason: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review
  - Hard negatives: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle
- `berries_6oz` (Safeway): **rejected**: 'Blueberries' @ $5.0
  - Reason: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.)
- `ritz_crackers` (Vons): **rejected**: 'Nabisco Family Size! Oreo Cookies 12.2-20 oz or Ritz Crackers 17.8-20.6 oz' @ $5.0
  - Reason: hard negative keyword/pattern hit: oreo; ad product type 'oreo' is incompatible with canonical intent 'ritz_crackers'; medium pattern confidence 0.73 needs review; large price change 101% vs prior week requires audit
  - Hard negatives: oreo
- `oreo_family_size` (Vons): **rejected**: 'Nabisco Family Size! Oreo Cookies 12.2-20 oz or Ritz Crackers 17.8-20.6 oz' @ $5.0
  - Reason: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'oreo'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.55 needs review
  - Hard negatives: ritz
- `pepsi_12packs` (Vons): **rejected**: 'Pepsi, 7UP, Canada Dry, A&W, Sunkist, Squirt' @ $2.5
  - Reason: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.40 needs review
  - Hard negatives: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz
- `dr_pepper_12packs` (Vons): **rejected**: 'Dr Pepper' @ $2.5
  - Reason: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'
  - Hard negatives: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz
- `berries_6oz` (Vons): **rejected**: 'Blueberries' @ $3.99
  - Reason: ad product type 'berries_large_pack' is incompatible with canonical intent 'berries_6oz_clamshell'; no family-size / eligible-size confirmation (needs one of: 6 oz, 6-oz, 6oz, 6 oz.); large price change 303% vs prior week requires audit

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `pepsi_12packs`: 'Pepsi 12-pack, 12-oz. cans or 8-pack, 12-oz. bottles. Lipton Tea 12-pack, 16.9-oz. Pure Leaf 6-pack, 16.9-oz. Gatorade 8' @ $13.88: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review
- `ritz_crackers`: 'Nabisco Family Size! Oreo Cookies 12.2-20 oz or Ritz Crackers 17.8-20.6 oz' @ $5.0: hard negative keyword/pattern hit: oreo; ad product type 'oreo' is incompatible with canonical intent 'ritz_crackers'; medium pattern confidence 0.73 needs review; large price change 101% vs prior week requires audit
- `oreo_family_size`: 'Nabisco Family Size! Oreo Cookies 12.2-20 oz or Ritz Crackers 17.8-20.6 oz' @ $5.0: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'oreo'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.55 needs review
- `pepsi_12packs`: 'Pepsi, 7UP, Canada Dry, A&W, Sunkist, Squirt' @ $2.5: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.40 needs review
- `dr_pepper_12packs`: 'Dr Pepper' @ $2.5: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'
- `pepsi_12packs`: 'Pepsi 12-pack, 12-oz. cans or 8-pack, 12-oz. bottles. Lipton Tea 12-pack, 16.9-oz. Pure Leaf 6-pack, 16.9-oz. Gatorade 8' @ $13.88: hard negative keyword/pattern hit: gatorade, lipton, pure leaf, 8\s*[- ]?pack.{0,20}bottle; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.58 needs review
- `ritz_crackers`: 'Nabisco Family Size! Oreo Cookies 12.2-20 oz or Ritz Crackers 17.8-20.6 oz' @ $5.0: hard negative keyword/pattern hit: oreo; ad product type 'oreo' is incompatible with canonical intent 'ritz_crackers'; medium pattern confidence 0.73 needs review; large price change 101% vs prior week requires audit
- `oreo_family_size`: 'Nabisco Family Size! Oreo Cookies 12.2-20 oz or Ritz Crackers 17.8-20.6 oz' @ $5.0: hard negative keyword/pattern hit: ritz; ad product type 'ritz_crackers' is incompatible with canonical intent 'oreo'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.55 needs review
- `pepsi_12packs`: 'Pepsi, 7UP, Canada Dry, A&W, Sunkist, Squirt' @ $2.5: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'; multi-item variant list (or/comma) needs review; medium pattern confidence 0.40 needs review
- `dr_pepper_12packs`: 'Dr Pepper' @ $2.5: hard negative keyword/pattern hit: 6\s*[- ]?pack.{0,20}bottle, 16\.9\s*oz; ad product type '8_pack_bottles' is incompatible with canonical intent '12_pack_cans'

## Accepted matches

- `doritos_5_13oz` (Safeway): 'Lay’s, Lay’s Kettle, Popcorners or Doritos 4.5-8 oz. Selected varieties.' @ $5.99 (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `ritz_crackers` (Safeway): 'Ritz Crackers or Cheez-It Crackers Selected varieties' @ $2.49 (confidence 0.83)
  - Display: Ritz crackers
  - Subtitle: regular size, 8.8–13.7 oz
- `cheez_it_crackers` (Safeway): 'Ritz Crackers or Cheez-It Crackers Selected varieties' @ $2.49 (confidence 0.70)
  - Display: Cheez-It crackers
  - Subtitle: regular size, 6.5–12.4 oz
- `goldfish_bags` (Safeway): 'Goldfish Crackers Selected varieties' @ $2.49 (confidence 1.00)
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
- `chobani_yogurt_per_cup` (Safeway): 'Chobani Yogurt 5.3 oz. Selected varieties.' @ $1.25 (confidence 0.70)
  - Display: Chobani yogurt
  - Subtitle: single cups or 4-packs; normalize per cup
- `tri_tip_roast` (Safeway): 'Chef’s Marinated Tri Tip Roast Boneless' @ $10.99 (confidence 0.70)
  - Display: Tri-tip roast
  - Subtitle: per lb
- `keebler_sandwich_crackers` (Vons): 'Keebler Sandwich Crackers 8 ct.' @ $2.49 (confidence 0.90)
  - Display: Keebler sandwich crackers
  - Subtitle: 8-pack boxes
- `strawberries_1_2lb` (Vons): 'Strawberries' @ $None (confidence 0.70)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `seedless_grapes_per_lb` (Vons): 'Black Seedless Grapes' @ $1.99 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `hass_avocados_each` (Vons): 'Medium Ripe Hass Avocados' @ $0.99 (confidence 0.90)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `peaches_per_lb` (Vons): 'Large Yellow Peaches' @ $2.99 (confidence 0.90)
  - Display: Peaches
  - Subtitle: per lb
- `nectarines_per_lb` (Vons): 'Nectarines' @ $2.99 (confidence 0.90)
  - Display: Nectarines
  - Subtitle: per lb
- `eggs_dozen_normalized` (Vons): 'Lucerne Large Eggs' @ $4.99 (confidence 1.00)
  - Display: Lucerne Eggs
  - Subtitle: Lucerne large eggs; per dozen (18 ct scaled to 12)
- `fage_cups` (Vons): 'Gatorade 28 oz., Rockstar Energy 16 oz., José Olé Burrito or Chimichanga 5 oz., Banquet Pot Pies 7 oz. Frozen, Green Giant Box Vegetables 7-8 oz. Frozen, Fage Greek Yogurt 5.3 oz., S&W Canned Beans 15-15.5 oz., Signature SELECT® Pasta 12-16 oz., Nissin Chow Mein 4 oz., StarKist Tuna Creations or Chunk Light Tuna Pouches 2.6-3 oz., Chunk Light Tuna in Oil or Water 5 oz., Kraft Macaroni & Cheese 5.7-25 oz. selected varieties, Kraft Macaroni & Cheese 7.25 oz. original or Heinz Yellow Mustard 14 oz.' @ $0.99 (confidence 0.70)
  - Display: Fage Greek yogurt cups
  - Subtitle: 5.3 oz cups
- `general_mills_cereal_regular` (Vons): 'Cheerios Cereal 8.9 to 12 oz, Cinnamon Toast Crunch Cereal 12 oz' @ $1.29 (confidence 0.70)
  - Display: General Mills cereal
  - Subtitle: regular size, 8.9–15 oz
- `chicken_breast_per_lb` (Vons): 'Fresh Boneless Skinless Chicken Breasts Available at the full service meat counter LIMIT 10 LBS' @ $1.99 (confidence 0.70)
  - Display: Chicken breast
  - Subtitle: per lb
- `salmon` (Vons): 'Fresh Atlantic Salmon Fillets' @ $8.99 (confidence 1.00)
  - Display: Salmon
  - Subtitle: fresh salmon fillet
- `doritos_5_13oz` (Safeway): 'Lay’s, Lay’s Kettle, Popcorners or Doritos 4.5-8 oz. Selected varieties.' @ $5.99 (confidence 0.70)
  - Display: Doritos
  - Subtitle: regular size, 5–13 oz
- `ritz_crackers` (Safeway): 'Ritz Crackers or Cheez-It Crackers Selected varieties' @ $2.49 (confidence 0.83)
  - Display: Ritz crackers
  - Subtitle: regular size, 8.8–13.7 oz
- `cheez_it_crackers` (Safeway): 'Ritz Crackers or Cheez-It Crackers Selected varieties' @ $2.49 (confidence 0.70)
  - Display: Cheez-It crackers
  - Subtitle: regular size, 6.5–12.4 oz
- `goldfish_bags` (Safeway): 'Goldfish Crackers Selected varieties' @ $2.49 (confidence 1.00)
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
- `chobani_yogurt_per_cup` (Safeway): 'Chobani Yogurt 5.3 oz. Selected varieties.' @ $1.25 (confidence 0.70)
  - Display: Chobani yogurt
  - Subtitle: single cups or 4-packs; normalize per cup
- `tri_tip_roast` (Safeway): 'Chef’s Marinated Tri Tip Roast Boneless' @ $10.99 (confidence 0.70)
  - Display: Tri-tip roast
  - Subtitle: per lb
- `keebler_sandwich_crackers` (Vons): 'Keebler Sandwich Crackers 8 ct.' @ $2.49 (confidence 0.90)
  - Display: Keebler sandwich crackers
  - Subtitle: 8-pack boxes
- `strawberries_1_2lb` (Vons): 'Strawberries' @ $None (confidence 0.70)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `seedless_grapes_per_lb` (Vons): 'Black Seedless Grapes' @ $1.99 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `hass_avocados_each` (Vons): 'Medium Ripe Hass Avocados' @ $0.99 (confidence 0.90)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `peaches_per_lb` (Vons): 'Large Yellow Peaches' @ $2.99 (confidence 0.90)
  - Display: Peaches
  - Subtitle: per lb
- `nectarines_per_lb` (Vons): 'Nectarines' @ $2.99 (confidence 0.90)
  - Display: Nectarines
  - Subtitle: per lb
- `eggs_dozen_normalized` (Vons): 'Lucerne Large Eggs' @ $4.99 (confidence 1.00)
  - Display: Lucerne Eggs
  - Subtitle: Lucerne large eggs; per dozen (18 ct scaled to 12)
- `fage_cups` (Vons): 'Gatorade 28 oz., Rockstar Energy 16 oz., José Olé Burrito or Chimichanga 5 oz., Banquet Pot Pies 7 oz. Frozen, Green Giant Box Vegetables 7-8 oz. Frozen, Fage Greek Yogurt 5.3 oz., S&W Canned Beans 15-15.5 oz., Signature SELECT® Pasta 12-16 oz., Nissin Chow Mein 4 oz., StarKist Tuna Creations or Chunk Light Tuna Pouches 2.6-3 oz., Chunk Light Tuna in Oil or Water 5 oz., Kraft Macaroni & Cheese 5.7-25 oz. selected varieties, Kraft Macaroni & Cheese 7.25 oz. original or Heinz Yellow Mustard 14 oz.' @ $0.99 (confidence 0.70)
  - Display: Fage Greek yogurt cups
  - Subtitle: 5.3 oz cups
- `general_mills_cereal_regular` (Vons): 'Cheerios Cereal 8.9 to 12 oz, Cinnamon Toast Crunch Cereal 12 oz' @ $1.29 (confidence 0.70)
  - Display: General Mills cereal
  - Subtitle: regular size, 8.9–15 oz
- `chicken_breast_per_lb` (Vons): 'Fresh Boneless Skinless Chicken Breasts Available at the full service meat counter LIMIT 10 LBS' @ $1.99 (confidence 0.70)
  - Display: Chicken breast
  - Subtitle: per lb
- `salmon` (Vons): 'Fresh Atlantic Salmon Fillets' @ $8.99 (confidence 1.00)
  - Display: Salmon
  - Subtitle: fresh salmon fillet
