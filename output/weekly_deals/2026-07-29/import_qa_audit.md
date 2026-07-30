# Weekly ad import QA: 2026-07-29

Auto checklist for crop-price overrides and tracked week-over-week worsens.
**Findings:** 89 crop overrides, 4 WoW worsens.

## Crop price overrides

| Feed | Pg | Idx | Product | First-pass → Final | Layout | Note |
|---|---|---|---|---|---|---|
| Safeway | 3 | 14 | Snapple Tea 6 pk. | $6.49 → $7.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 4 | 4 | Red Bull 4-pack, 12-oz. Selected varieties. | $3.99 → $9.99 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 4 | 7 | Red Bull Energy Drink 8.4 oz. Selected varieties. | $0.99 → $5.0 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 8 | 26 | Zyrtec Allergy Relief 24 to 40-ct. | $9.99 → $24.99 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 8 | 27 | Every Day | $2.99 → $11.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 8 | 3 | Secret or Old Spice Deodorant Selected varieties. | $5.99 → $7.99 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 1 | 10 | Challenger or Danish Creamery Butter Salted or Unsalted 16 oz | $3.49 → $3.49 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 1 | 11 | San Luis Sourdough Bread 24 oz, Dave’s Killer Thin Sliced Bread 18-21 oz, Bagels or Engli… | $4.49 → $4.49 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 1 | 15 | San Luis Sourdough Bread 24-oz. Dave's Killer Thin Sliced Bread 20.5-oz. Bagels or Englis… | $3.99 → $4.49 | standard_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 1 | 17 | Signature SELECT® 80% Lean Ground Beef Mega Pack | $? → $4.99 | points_promo_block | missing_or_unclear_price|unclear_product_name|first_pass_crop_disagreement|crop_verification_override|crop_override_pri… |
| Safeway | 1 | 18 | Nabisco Chips Ahoy! Cookies, Snack Crackers, Oreo or Ritz Crackers 3.5-13.7 oz | $1.99 → $1.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 1 | 5 | Signature SELECT® Pork Shoulder Country Style Ribs or Blade Steak Mix & Match. | $? → $? | front_page_hero | missing_or_unclear_price|missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_pro… |
| Safeway | 2 | 0 | Oatly Oatmilk | $4.99 → $4.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 1 | Nutella Hazelnut Spread | $5.99 → $5.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 10 | Gorton’s Fish Sticks or Fillets Selected varieties | $? → $3.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 10 | Gorton’s Fish Sticks or Fillets Selected varieties | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 16 | Honey Mango | $? → $1.0 | standard_grid_offer | tagged crop override in consolidated split |
| Safeway | 2 | 18 | Green or Red Seedless Grapes | $4.99 → $5.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 18 | Green | $? → $4.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 18 | Red Seedless Grapes | $? → $4.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 19 | Red, Orange, Yellow | $? → $1.5 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 19 | Green Bell Pepper | $? → $1.5 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 2 | Energy Drink Assorted varieties | $2.5 → $2.5 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 3 | Nabisco Ritz Crackers or BelVita Breakfast Biscuits | $2.5 → $2.5 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 4 | Kraft Macaroni & Cheese | $3.55 → $3.55 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 5 | all Laundry Detergent | $14.99 → $14.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 13 | Snyder's Mini Pretzels | $4.99 → $4.99 | coupon_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 3 | 14 | Snapple Tea 6 pk. | $? → $6.49 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 3 | 16 | Signature SELECT Refreshe Purified Drinking Water 24 pack, 16.9 oz. bottles | $3.99 → $3.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 17 | Kraft Macaroni & Cheese 10 pk. | $9.99 → $7.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 3 | 17 | Kraft Macaroni & Cheese 10 pk. | $? → $9.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 3 | 18 | Frosted Flakes, Mini Wheats, Rice Krispies | $4.99 → $4.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 3 | 19 | Hidden Valley Ranch or Secret Sauce | $0.99 → $0.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 2 | Johnsonville Sausage Links or Patties Selected varieties | $5.99 → $2.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 3 | 2 | Johnsonville Sausage Links or Patties Selected varieties | $? → $5.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 3 | 22 | Secret Deodorant Old Spice Deodorant | $6.99 → $6.99 | multi_product_group | missing_package_size|ambiguous_multi_product_offer|first_pass_crop_disagreement|crop_verification_override|crop_overrid… |
| Safeway | 3 | 3 | Waterfront Bistro Cooked Shrimp 31-40 ct. 16 oz. Frozen | $7.99 → $7.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 3 | 8 | DRUMSTICK VARIETY PACK | $5.99 → $5.99 | points_promo_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 4 | 1 | Oscar Mayer Lunchables 6-10.7 oz. Selected varieties. | $4.99 → $4.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 10 | Chicken Wings 22-26 oz. Selected varieties. Includes Hot & Spicy, Buffalo Style, Honey BB… | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 13 | Jennie-O 93% Lean Ground Turkey or Patties 16 oz. or Open Nature Lean Ground Turkey 16 oz. | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 15 | Sweet Corn | $0.5 → $0.5 | friday_only_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_promo_mechanic |
| Safeway | 4 | 16 | Hass Avocado | $1.25 → $0.5 | friday_only_block | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 4 | 19 | Pringles Potato Crisps 5.2-5.5 oz. | $? → $1.67 | friday_only_block | tagged crop override in consolidated split |
| Safeway | 4 | 19 | Signature SELECT Classic Potato Chips 7.5-8 oz. | $? → $1.67 | friday_only_block | tagged crop override in consolidated split |
| Safeway | 4 | 20 | Signature SELECT Potato Chips 7.75 to 8-oz. Pringles Chips 5.2 to 5.57-oz. Selected varie… | $2.5 → $1.67 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 4 | 21 | Ball Park Hot Dog or Hamburger Buns 8 ct. Selected varieties. | $2.5 → $2.5 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 4 | 23 | Signature SELECT Soda or Seltzer 2-liter, Crystal Geyser 1 Gallon. Member Price | $1.25 → $1.25 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 4 | 3 | Planters Cashews or Mixed Nuts 8 to 10.3-oz. Selected varieties. | $4.99 → $4.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 4 | 6 | Hershey's Single Candy Bar 1.4 to 2-oz. Selected varieties. | $1.89 → $1.89 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 4 | 9 | Saint James Tea 16 oz. Selected varieties. | $2.0 → $2.0 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 6 | 1 | Noosa Yoghurt | $2.0 → $2.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 7 | 5 | Bolthouse Juice Selected varieties | $2.99 → $2.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 7 | 7 | Frito-Lay Ruffles or Party Size! Chips 7.5-13 oz | $4.99 → $4.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 7 | 8 | Smartfood or Rold Gold Snacks Party Size! 6.25-10.5 oz | $4.99 → $4.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 8 | 1 | Native Body Wash | $10.99 → $10.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 8 | 10 | Neutrogena Makeup Remover Wipes 25 ct. | $7.99 → $7.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 8 | 11 | Neutrogena Acne Patches | $8.99 → $8.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 8 | 12 | Mighty Patch Hero Variety Pack | $12.99 → $12.99 | points_promo_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 8 | 13 | Oral B Glide Floss Picks 75-ct. Selected varieties. | $4.99 → $4.99 | points_promo_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 8 | 14 | Listerine Mouthwash Selected varieties. | $6.99 → $6.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 8 | 15 | Crest VALUE 2 PACK | $8.99 → $8.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 8 | 17 | CURAD Bandages | $6.99 → $6.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 8 | 19 | Band Aid Bandages | $5.99 → $5.99 | points_promo_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 8 | 2 | Pantene or Aussie | $7.99 → $5.99 | points_promo_block | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 8 | 20 | Children's Tylenol or Motrin | $8.99 → $8.99 | points_promo_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 8 | 22 | Neosporin Ointment or Benadryl Allergy Relief | $8.99 → $8.99 | points_promo_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 8 | 23 | Tylenol Extra Strength Pain Relief | $13.99 → $13.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 8 | 27 | Every Day | $? → $2.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 8 | 5 | Garnier Fructis Shampoo or Conditioner Selected varieties. | $5.99 → $5.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 8 | 6 | method Body Wash | $9.99 → $9.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 8 | 7 | Olay or Secret Select varieties. | $? → $? | points_promo_block | missing_or_unclear_price|missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_pro… |
| Safeway | 9 | 1 | Mike & Ike or Hot Tamales Theater Box | $1.49 → $1.49 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 9 | 10 | Gerber Organic Pouch | $6.0 → $6.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 12 | 5-hour Energy Shot | $5.0 → $5.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 9 | 15 | Nature Made Vitamins or Supplements | $? → $8.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 15 | Nature Made Vitamins | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 15 | Supplements | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 16 | MiraLAX Laxative Powder | $25.99 → $19.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 16 | MiraLAX Laxative Powder | $? → $25.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 21 | Lunch Kit or Bento Box | $? → $? | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 22 | Hydration Bottles or Tumblers | $? → $19.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 22 | Hydration Bottles | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 22 | Tumblers | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 26 | Cryo Ice Pack | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 27 | Hot Wheels | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 4 | Nerds Clusters Candy | $4.99 → $4.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 9 | 8 | CLIF BUILDERS Bar | $5.0 → $5.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 9 | 9 | GoMacro Bar | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |

## Tracked week-over-week worsens

| Feed | Family | Prior → New | Ratio | Offer |
|---|---|---|---|---|
| Safeway | `nature_valley_bars` | $1.99 (2026-07-01) → $3.99 | 2.01× | Nature Valley Bars |
| Safeway | `sweet_corn` | $0.25 (2026-07-15) → $0.50 | 2.00× | Sweet Corn |
| Safeway | `betty_crocker_fruit_snacks` | $2.50 (2026-07-01) → $3.99 | 1.60× | Betty Crocker Fruit Snacks or Annie's Fruit Snacks |
| Safeway | `frito_lay_multipack_chips` | $4.99 (2026-07-22) → $7.99 | 1.60× | Frito-Lay Multipack Snacks |

## What to do

1. Open the flyer page for each crop override — especially `coupon_grid_offer` rows where first-pass and final prices disagree.
2. For WoW worsens, confirm the new ad size/price is real (not bleed from a neighbor tile, party-size, or multipack).
3. Correct sibling `split_offer_items.csv`, then rematch:
   `/usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-ids <id> --feed safeway`

