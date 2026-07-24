# Weekly ad import QA: 2026-07-22

Auto checklist for crop-price overrides and tracked week-over-week worsens.
**Findings:** 75 crop overrides, 1 WoW worsens.

## Crop price overrides

| Feed | Pg | Idx | Product | First-pass → Final | Layout | Note |
|---|---|---|---|---|---|---|
| Safeway | 2 | 3 | Kellogg's Pop-Tarts 12 ct | $2.99 → $5.0 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 2 | 5 | Bush's Best Baked Beans 16 oz | $2.5 → $4.0 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 3 | 22 | Thoroughbred Bleach | $8.99 → $16.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 3 | 5 | Yoplait Fridge Pack 8-pack, 6 oz. Go-Gurt Yogurt | $0.99 → $3.99 | coupon_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 8 | 1 | Birch Benders Pancake & Waffle Mix | $2.99 → $9.0 | standard_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 9 | 13 | Top Flight 70 Sheet Notebook | $1.49 → $9.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 9 | 14 | BIC Wite-Out Correction | $2.99 → $10.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 1 | 15 | Doritos, Lay’s, Miss Vickie’s or Simply NKD | $2.49 → $2.49 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 1 | 8 | Waterfront Bistro Raw Shrimp | $6.99 → $6.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 10 | 1 | Aleve Pain Relief Select varieties | $7.99 → $7.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 10 | 4 | Signature Care® or Signature SELECT™ Liquid Hand Soap or Travel Size Hand Sanitizer | $3.0 → $3.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 2 | 1 | Tillamook Ice Cream 48 oz | $5.7 → $5.7 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 13 | Waterfront BISTRO Cooked Shrimp | $14.0 → $14.99 | hero_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 13 | Waterfront BISTRO Cooked Shrimp | $? → $14.0 | hero_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 18 | O Organics! Organic Blueberries pint | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 2 | Pepsi Soda 12-pack, 12-oz cans or 8-pack, 12-oz bottles | $5.4 → $1.25 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 2 | 2 | Pepsi Soda 12-pack, 12-oz cans | $? → $5.4 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 2 | 8-pack, 12-oz bottles | $? → $5.4 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 3 | Kellogg's Pop-Tarts 12 ct | $? → $2.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 4 | Poppi Prebiotic Soda 12-oz. Selected varieties. Member Price | $4.99 → $4.0 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic_product_name |
| Safeway | 2 | 5 | Bush's Best Baked Beans 16 oz | $? → $2.5 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 6 | McCormick Spice | $? → $? | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 7 | Quilted Northern Bath Tissue 6 Mega Rolls or Brawny Paper Towels 4 Double Rolls | $6.99 → $6.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 11 | Kettle Potato Chips | $1.99 → $1.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 3 | 13 | Gatorade 8-pack, 20-oz. Selected varieties. | $6.99 → $6.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 3 | 15 | Nabisco Snack Crackers | $4.99 → $4.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 2 | Waterfront Bistro Tilapia Fillets | $9.99 → $9.99 | coupon_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 3 | 22 | Thoroughbred Bleach | $? → $8.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 3 | 3 | Summ! Spring Rolls or Dumplings | $4.99 → $4.99 | coupon_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 3 | 4 | The Buik Mac & Cheese Bowls Selected varieties | $4.99 → $4.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 7 | Popsicle Ice Pops Klondike Ice Cream Bars | $3.99 → $3.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 3 | 8 | Yasso Greek Yogurt Bars | $5.99 → $5.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 9 | Lactaid Cottage Cheese | $3.99 → $3.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 1 | Honey Nut Cheerios, Cinnamon Toast Crunch | $1.99 → $1.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 4 | 13 | Signature SELECT Salad Bowl | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 17 | Hostess Donettes | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 18 | Kellogg’s Eggo Thick & Fluffy Waffles | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 19 | Cape Cod Kettle Cooked Potato Chips, Sun Chips | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 21 | Value Corner 6 Roll Paper Towels | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 4 | Totino’s Pizza Rolls | $4.99 → $3.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 4 | Totino’s Pizza Rolls | $? → $4.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 4 | 9 | Chicken Tenders | $5.0 → $5.0 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 5 | 0 | Califia Farms Organic Almond Creamer | $4.99 → $4.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 5 | 1 | Nabisco Chips Ahoy! Cookies | $3.49 → $3.49 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 5 | 2 | Kellogg's Nutri-Grain Bars or Rice Krispies Treats Bars 6-8 ct. or Special K Bars 5 ct. | $1.99 → $1.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 5 | 3 | Kellogg's Nutri-Grain Bars or Rice Krispies Treats 8-ct. or Special K Bars 6-ct. Selected… | $2.49 → $1.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 6 | 3 | Yerba Madre Herbal Tea Beverage 15.5-16 oz. cans. Selected varieties. | $3.0 → $3.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 6 | 5 | Chobani Zero Sugar Yogurt 5.3 oz. Selected varieties. | $1.5 → $1.5 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 7 | 3 | Noosa Yoghurt | $4.0 → $4.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 8 | 5 | Lifeway Kefir | $3.99 → $3.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 8 | 6 | Planet Oat Oatmilk | $2.99 → $2.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 8 | 7 | Cheetos | $2.99 → $2.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 8 | 8 | Frito-Lay Variety Pack | $4.99 → $4.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 9 | 0 | Nature's Truth Vitamins | $? → $? | standard_grid_offer | missing_or_unclear_price|missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_pro… |
| Safeway | 9 | 1 | Quest Bar | $5.0 → $5.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 9 | 12 | Top Flight 2-Pocket Folder | $1.49 → $1.49 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 13 | Top Flight 70 Sheet Notebook | $? → $1.49 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 14 | BIC Wite-Out Correction | $? → $2.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 17 | Post-it Notes | $3.49 → $1.49 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 17 | Post-it Notes | $? → $3.49 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 18 | Command Hooks | $? → $2.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 18 | Command Hooks | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 19 | Hot Wheels | $5.0 → $4.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 19 | Hot Wheels | $? → $5.0 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 21 | Hydration Bottles | $? → $1.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 21 | Hydration Bottles | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 22 | Lunch Kit or Container | $? → $1.49 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 22 | Lunch Kit or Container | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 23 | Cryo Ice Gel Pack | $5.0 → $4.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 9 | 23 | Cryo Ice Gel Pack | $? → $5.0 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 4 | 5-hour Energy 6 pack | $10.99 → $5.0 | standard_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 6 | Boost Original 6 pack | $9.99 → $7.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 6 | Boost Original 6 pack | $? → $9.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 7 | CLIF Builders Protein Bars 6 ct | $10.99 → $6.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 7 | CLIF Builders Protein Bars 6 ct | $? → $10.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |

## Tracked week-over-week worsens

| Feed | Family | Prior → New | Ratio | Offer |
|---|---|---|---|---|
| Safeway | `tillamook_ice_cream` | $3.50 (2026-06-24) → $5.70 | 1.63× | Tillamook Ice Cream 48 oz |

## What to do

1. Open the flyer page for each crop override — especially `coupon_grid_offer` rows where first-pass and final prices disagree.
2. For WoW worsens, confirm the new ad size/price is real (not bleed from a neighbor tile, party-size, or multipack).
3. Correct sibling `split_offer_items.csv`, then rematch:
   `/usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-ids <id> --feed safeway`

