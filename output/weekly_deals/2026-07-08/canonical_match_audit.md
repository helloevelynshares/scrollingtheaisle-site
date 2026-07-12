# Canonical match audit: 2026-07-08 to 2026-07-14

Generated: 2026-07-12T23:45:51.211340+00:00

## Summary

- **Accepted:** 50
- **Rejected:** 6
- **Manual review:** 4
- **Families updated:** doritos_5_13oz, ruffles_regular_bags, nabisco_snack_crackers, oreo_family_size, pepsi_12packs, seedless_grapes_per_lb, cherries_per_lb, berries_6oz, hass_avocados_each, mangoes_each, plums_per_lb, sweet_corn, pillsbury_refrigerated_dough, chicken_breast_per_lb, ritz_crackers, cheez_it_crackers, simply_refrigerated_juice_lemonade, strawberries_1_2lb, eggs_dozen_normalized, butter_16oz

## Graph update safety check

### All-time low changes

- `cheez_it_crackers` (Vons): $1.67: Cheez-It Crackers, Keebler Fudge Shoppe Cookies
- `cheez_it_crackers` (Vons): $1.67: Cheez-It Crackers, Keebler Fudge Shoppe Cookies

### Graph preview changes

- `coca_cola_12packs` (Safeway): blocked $3.99: confidence 0.40 < min 0.70
- `butter_16oz` (Safeway): blocked $3.49: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'; ad product type 'butter_spread' not in allowed types ['butter_sticks']
- `salmon` (Safeway): blocked $4.99: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'; ad product type 'smoked_salmon' not in allowed types ['fresh_salmon_fillets']
- `nabisco_snack_crackers` (Vons): blocked $2.49: no family-size / eligible-size confirmation (needs one of: family size, family-size, 11.5, 12 oz, 12.5, 13 oz, 14 oz, 11.5-14, 11.5 to 14, 10-14, 10 to 14)
- `coca_cola_12packs` (Vons): blocked $0.99: hard negative keyword/pattern hit: 2 liter, 2 l, 2\s*[- ]?liter; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; ad product type '2_liter_bottle' not in allowed types ['12_pack_cans']
- `coca_cola_12packs` (Safeway): blocked $3.99: confidence 0.40 < min 0.70
- `butter_16oz` (Safeway): blocked $3.49: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'; ad product type 'butter_spread' not in allowed types ['butter_sticks']
- `salmon` (Safeway): blocked $4.99: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'; ad product type 'smoked_salmon' not in allowed types ['fresh_salmon_fillets']
- `nabisco_snack_crackers` (Vons): blocked $2.49: no family-size / eligible-size confirmation (needs one of: family size, family-size, 11.5, 12 oz, 12.5, 13 oz, 14 oz, 11.5-14, 11.5 to 14, 10-14, 10 to 14)
- `coca_cola_12packs` (Vons): blocked $0.99: hard negative keyword/pattern hit: 2 liter, 2 l, 2\s*[- ]?liter; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; ad product type '2_liter_bottle' not in allowed types ['12_pack_cans']

### Blocked from tracker graph

- `butter_16oz` (Safeway): **rejected**: "Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties." @ $3.49
  - Reason: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'; ad product type 'butter_spread' not in allowed types ['butter_sticks']
  - Hard negatives: spread, 13\s*to\s*15
- `salmon` (Safeway): **rejected**: 'Acme Smoked Nova Salmon 4 oz' @ $4.99
  - Reason: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'; ad product type 'smoked_salmon' not in allowed types ['fresh_salmon_fillets']
  - Hard negatives: smoked, nova, 4 oz, acme, \b[234]\s*oz\b
- `coca_cola_12packs` (Vons): **rejected**: 'Coca-Cola 2 liter' @ $0.99
  - Reason: hard negative keyword/pattern hit: 2 liter, 2 l, 2\s*[- ]?liter; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; ad product type '2_liter_bottle' not in allowed types ['12_pack_cans']
  - Hard negatives: 2 liter, 2 l, 2\s*[- ]?liter
- `butter_16oz` (Safeway): **rejected**: "Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties." @ $3.49
  - Reason: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'; ad product type 'butter_spread' not in allowed types ['butter_sticks']
  - Hard negatives: spread, 13\s*to\s*15
- `salmon` (Safeway): **rejected**: 'Acme Smoked Nova Salmon 4 oz' @ $4.99
  - Reason: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'; ad product type 'smoked_salmon' not in allowed types ['fresh_salmon_fillets']
  - Hard negatives: smoked, nova, 4 oz, acme, \b[234]\s*oz\b
- `coca_cola_12packs` (Vons): **rejected**: 'Coca-Cola 2 liter' @ $0.99
  - Reason: hard negative keyword/pattern hit: 2 liter, 2 l, 2\s*[- ]?liter; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; ad product type '2_liter_bottle' not in allowed types ['12_pack_cans']
  - Hard negatives: 2 liter, 2 l, 2\s*[- ]?liter
- `coca_cola_12packs` (Safeway): **manual_review**: 'Coca-Cola, Pepsi' @ $3.99
  - Reason: confidence 0.40 < min 0.70
- `nabisco_snack_crackers` (Vons): **manual_review**: 'Wheat Thins' @ $2.49
  - Reason: no family-size / eligible-size confirmation (needs one of: family size, family-size, 11.5, 12 oz, 12.5, 13 oz, 14 oz, 11.5-14, 11.5 to 14, 10-14, 10 to 14)
- `coca_cola_12packs` (Safeway): **manual_review**: 'Coca-Cola, Pepsi' @ $3.99
  - Reason: confidence 0.40 < min 0.70
- `nabisco_snack_crackers` (Vons): **manual_review**: 'Wheat Thins' @ $2.49
  - Reason: no family-size / eligible-size confirmation (needs one of: family size, family-size, 11.5, 12 oz, 12.5, 13 oz, 14 oz, 11.5-14, 11.5 to 14, 10-14, 10 to 14)

## Rejected tempting items

These looked like deals but were blocked from updating canonical trackers:

- `butter_16oz`: "Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties." @ $3.49: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'; ad product type 'butter_spread' not in allowed types ['butter_sticks']
- `salmon`: 'Acme Smoked Nova Salmon 4 oz' @ $4.99: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'; ad product type 'smoked_salmon' not in allowed types ['fresh_salmon_fillets']
- `coca_cola_12packs`: 'Coca-Cola 2 liter' @ $0.99: hard negative keyword/pattern hit: 2 liter, 2 l, 2\s*[- ]?liter; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; ad product type '2_liter_bottle' not in allowed types ['12_pack_cans']
- `butter_16oz`: "Land O'Lakes Butter 16-oz. Spread 13 to 15-oz. Selected varieties." @ $3.49: hard negative keyword/pattern hit: spread, 13\s*to\s*15; ad product type 'butter_spread' is incompatible with canonical intent 'butter_sticks'; ad product type 'butter_spread' not in allowed types ['butter_sticks']
- `salmon`: 'Acme Smoked Nova Salmon 4 oz' @ $4.99: hard negative keyword/pattern hit: smoked, nova, 4 oz, acme, \b[234]\s*oz\b; ad product type 'smoked_salmon' is incompatible with canonical intent 'fresh_salmon_fillets'; ad product type 'smoked_salmon' not in allowed types ['fresh_salmon_fillets']
- `coca_cola_12packs`: 'Coca-Cola 2 liter' @ $0.99: hard negative keyword/pattern hit: 2 liter, 2 l, 2\s*[- ]?liter; ad product type '2_liter_bottle' is incompatible with canonical intent '12_pack_cans'; ad product type '2_liter_bottle' not in allowed types ['12_pack_cans']

## Accepted matches

- `doritos_5_13oz` (Safeway): 'Doritos Tortilla Chips' @ $2.5 (confidence 0.90)
  - Display: Doritos
  - Subtitle: 5–13 oz bags
- `ruffles_regular_bags` (Safeway): 'Ruffles Potato Chips' @ $2.5 (confidence 0.90)
  - Display: Ruffles
  - Subtitle: regular bags, roughly 5–13 oz
- `nabisco_snack_crackers` (Safeway): 'Nabisco Family Size Snack Crackers 10-14 oz' @ $3.49 (confidence 0.89)
  - Display: Wheat Thins, Triscuit & Chicken in a Biskit
  - Subtitle: Nabisco family-size snack crackers, 11.5–14 oz
  - Manufacturer family: Nabisco
  - Allowed product lines: Wheat Thins, Triscuit, Chicken in a Biskit
  - Package: family_size_box, 11.5–14 oz
  - Eligible item examples: Wheat Thins Family Size Original 14 oz, Wheat Thins Family Size Reduced Fat 12.5 oz, Triscuit Family Size Original 12.5 oz, Triscuit Family Size Reduced Fat 11.5 oz, Triscuit Family Size Roasted Garlic 12.5 oz, Triscuit Family Size Rosemary & Olive Oil 12.5 oz, Chicken in a Biskit Family Size Original 12 oz, Chicken in a Biskit Family Size Ranch 12 oz
- `oreo_family_size` (Safeway): 'Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz.' @ $3.49 (confidence 1.00)
  - Display: Oreo cookies
  - Subtitle: family size, roughly 10.68–18.71 oz
- `pepsi_12packs` (Safeway): 'Coca-Cola, Pepsi' @ $3.99 (confidence 0.70)
  - Display: Pepsi
  - Subtitle: 12-pack, 12 fl oz cans
- `seedless_grapes_per_lb` (Safeway): 'Red Seedless Grapes' @ $2.99 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `cherries_per_lb` (Safeway): 'Red Cherries' @ $4.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `berries_6oz` (Safeway): 'Blackberries 6 oz' @ $2.99 (confidence 0.86)
  - Display: Blueberries / raspberries / blackberries
  - Subtitle: 6 oz clamshells
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
- `ritz_crackers` (Vons): 'Ritz Crackers' @ $2.49 (confidence 1.00)
  - Display: Ritz crackers
  - Subtitle: 8.8–13.7 oz boxes
- `cheez_it_crackers` (Vons): 'Cheez-It Crackers, Keebler Fudge Shoppe Cookies' @ $1.67 (confidence 0.70)
  - Display: Cheez-It crackers
  - Subtitle: 6.5–12.4 oz boxes/bags
- `oreo_family_size` (Vons): 'Oreo Cookies 10-15.35 oz' @ $3.99 (confidence 1.00)
  - Display: Oreo cookies
  - Subtitle: family size, roughly 10.68–18.71 oz
- `pepsi_12packs` (Vons): 'Pepsi 2 liter' @ $0.99 (confidence 0.90)
  - Display: Pepsi
  - Subtitle: 12-pack, 12 fl oz cans
- `simply_refrigerated_juice_lemonade` (Vons): 'Simply Juice 46-52 oz., +CRV Chobani 20g Protein Yogurt 4 ct. Frigo CheeseHeads String Cheese 6.3-12 oz. or Challenge Butter 13-16 oz. Selected varieties' @ $3.99 (confidence 0.70)
  - Display: Simply juice
  - Subtitle: 46–52 fl oz bottles
- `strawberries_1_2lb` (Vons): 'Fresh Strawberries' @ $2.5 (confidence 0.90)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `seedless_grapes_per_lb` (Vons): 'Green Seedless Grapes' @ $1.99 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `cherries_per_lb` (Vons): 'Cherries' @ $2.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `hass_avocados_each` (Vons): 'Large Hass Avocados' @ $1.5 (confidence 0.90)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `eggs_dozen_normalized` (Vons): 'Lucerne Large Eggs' @ $2.49 (confidence 1.00)
  - Display: Eggs
  - Subtitle: large eggs; normalized to 12-count/dozen
- `butter_16oz` (Vons): 'Lucerne Butter' @ $3.99 (confidence 0.75)
  - Display: Butter
  - Subtitle: 16 oz sticks / quarters; normalize to 16 oz
- `doritos_5_13oz` (Safeway): 'Doritos Tortilla Chips' @ $2.5 (confidence 0.90)
  - Display: Doritos
  - Subtitle: 5–13 oz bags
- `ruffles_regular_bags` (Safeway): 'Ruffles Potato Chips' @ $2.5 (confidence 0.90)
  - Display: Ruffles
  - Subtitle: regular bags, roughly 5–13 oz
- `nabisco_snack_crackers` (Safeway): 'Nabisco Family Size Snack Crackers 10-14 oz' @ $3.49 (confidence 0.89)
  - Display: Wheat Thins, Triscuit & Chicken in a Biskit
  - Subtitle: Nabisco family-size snack crackers, 11.5–14 oz
  - Manufacturer family: Nabisco
  - Allowed product lines: Wheat Thins, Triscuit, Chicken in a Biskit
  - Package: family_size_box, 11.5–14 oz
  - Eligible item examples: Wheat Thins Family Size Original 14 oz, Wheat Thins Family Size Reduced Fat 12.5 oz, Triscuit Family Size Original 12.5 oz, Triscuit Family Size Reduced Fat 11.5 oz, Triscuit Family Size Roasted Garlic 12.5 oz, Triscuit Family Size Rosemary & Olive Oil 12.5 oz, Chicken in a Biskit Family Size Original 12 oz, Chicken in a Biskit Family Size Ranch 12 oz
- `oreo_family_size` (Safeway): 'Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz.' @ $3.49 (confidence 1.00)
  - Display: Oreo cookies
  - Subtitle: family size, roughly 10.68–18.71 oz
- `pepsi_12packs` (Safeway): 'Coca-Cola, Pepsi' @ $3.99 (confidence 0.70)
  - Display: Pepsi
  - Subtitle: 12-pack, 12 fl oz cans
- `seedless_grapes_per_lb` (Safeway): 'Red Seedless Grapes' @ $2.99 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `cherries_per_lb` (Safeway): 'Red Cherries' @ $4.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `berries_6oz` (Safeway): 'Blackberries 6 oz' @ $2.99 (confidence 0.86)
  - Display: Blueberries / raspberries / blackberries
  - Subtitle: 6 oz clamshells
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
- `ritz_crackers` (Vons): 'Ritz Crackers' @ $2.49 (confidence 1.00)
  - Display: Ritz crackers
  - Subtitle: 8.8–13.7 oz boxes
- `cheez_it_crackers` (Vons): 'Cheez-It Crackers, Keebler Fudge Shoppe Cookies' @ $1.67 (confidence 0.70)
  - Display: Cheez-It crackers
  - Subtitle: 6.5–12.4 oz boxes/bags
- `oreo_family_size` (Vons): 'Oreo Cookies 10-15.35 oz' @ $3.99 (confidence 1.00)
  - Display: Oreo cookies
  - Subtitle: family size, roughly 10.68–18.71 oz
- `pepsi_12packs` (Vons): 'Pepsi 2 liter' @ $0.99 (confidence 0.90)
  - Display: Pepsi
  - Subtitle: 12-pack, 12 fl oz cans
- `simply_refrigerated_juice_lemonade` (Vons): 'Simply Juice 46-52 oz., +CRV Chobani 20g Protein Yogurt 4 ct. Frigo CheeseHeads String Cheese 6.3-12 oz. or Challenge Butter 13-16 oz. Selected varieties' @ $3.99 (confidence 0.70)
  - Display: Simply juice
  - Subtitle: 46–52 fl oz bottles
- `strawberries_1_2lb` (Vons): 'Fresh Strawberries' @ $2.5 (confidence 0.90)
  - Display: Strawberries
  - Subtitle: 1 lb or 2 lb packs; normalize per lb
- `seedless_grapes_per_lb` (Vons): 'Green Seedless Grapes' @ $1.99 (confidence 0.90)
  - Display: Seedless grapes
  - Subtitle: per lb; normalize bags to per lb
- `cherries_per_lb` (Vons): 'Cherries' @ $2.99 (confidence 0.90)
  - Display: Cherries
  - Subtitle: per lb
- `hass_avocados_each` (Vons): 'Large Hass Avocados' @ $1.5 (confidence 0.90)
  - Display: Hass avocados
  - Subtitle: each or multi-buy
- `eggs_dozen_normalized` (Vons): 'Lucerne Large Eggs' @ $2.49 (confidence 1.00)
  - Display: Eggs
  - Subtitle: large eggs; normalized to 12-count/dozen
- `butter_16oz` (Vons): 'Lucerne Butter' @ $3.99 (confidence 0.75)
  - Display: Butter
  - Subtitle: 16 oz sticks / quarters; normalize to 16 oz
