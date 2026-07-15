# Weekly ad import QA: 2026-07-15

Auto checklist for crop-price overrides and tracked week-over-week worsens.
**Findings:** 55 crop overrides, 4 WoW worsens.

## Crop price overrides

| Feed | Pg | Idx | Product | First-pass → Final | Layout | Note |
|---|---|---|---|---|---|---|
| Safeway | 1 | 17 | Lay’s, Lay’s Kettle, Popcorners or Doritos 4.5-8 oz. Selected varieties. | $2.49 → $5.99 | coupon_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 1 | 19 | Barilla Pasta 12-16 oz. Selected varieties. | $0.99 → $2.49 | coupon_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 3 | 23 | Pacifico or Heineken 12-pack, 11.2 to 12 oz. Coors or Bud 18-pack, 12-oz. selected variet… | $12.99 → $15.99 | coupon_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 7 | 5 | Bolthouse Juice | $5.0 → $16.99 | standard_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 7 | 9 | Party Size Ruffles, Fritos or Sabra | $4.99 → $9.0 | coupon_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 3 | 15 | Beef Chuck Shoulder Style Ribs Value Pack | $3.99 → $6.99 | standard_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 3 | 3 | Sweet Corn | $1.25 → $5.0 | friday_only_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 1 | 10 | smartwater 6-pack, 16.9-oz. | $? → $3.99 | standard_grid_offer | missing_or_unclear_price|first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_na… |
| Safeway | 1 | 11 | Pepsi 12-pack, 12-oz. cans or 8-pack, 12-oz. bottles. Lipton Tea 12-pack, 16.9-oz. Pure L… | $13.88 → $13.88 | standard_grid_offer | excluded_category|first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 1 | 13 | Red Cherries | $2.99 → $2.99 | coupon_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 1 | 16 | Waterfront Bistro Fish Fillets, Salmon Portions or Raw Shrimp 16-32 oz. Frozen. Selected … | $5.99 → $2.99 | coupon_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 1 | 18 | Quaker Life, Cap’n Crunch’s or Oatmeal Squares Cereal 10.3 to 14.5-oz. Selected varieties. | $2.49 → $2.49 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 1 | 2 | Sweet Corn | $1.0 → $1.0 | front_page_hero | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 1 | 20 | Barilla Pasta 12 to 16-oz. Selected varieties. Limit 8 items. | $7.99 → $0.99 | coupon_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 2 | 13 | Wells Ice Cream Candy Bars 4-6 ct. | $5.99 → $4.0 | points_promo_block | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 2 | 17 | Kinder’s Dry Rub Seasoning 3.9-5.9 oz. | $4.99 → $4.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 2 | 18 | Kingsford Charcoal Briquets 16 lb. | $15.99 → $15.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 2 | 8 | Cucumber or Green Bell Pepper Medium Size. | $5.0 → $1.25 | standard_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 3 | 1 | Oscar Mayer Beef Franks Selected varieties | $3.99 → $3.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 3 | 11 | Betty Crocker Cake Mix | $1.99 → $1.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 3 | 13 | California Pizza Kitchen Selected varieties | $7.99 → $7.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 3 | 14 | Ritz Crackers or Cheez-It Crackers Selected varieties | $2.49 → $2.49 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 3 | 18 | Naked Juice Selected varieties | $8.99 → $2.49 | coupon_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 3 | 2 | Land O’Frost Premium Lunchmeat Mega Pack Selected varieties. | $7.99 → $7.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 3 | 20 | Vitali Vodka | $9.99 → $2.49 | coupon_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 3 | 22 | Signature SELECT refreshe Purified Drinking Water | $3.99 → $3.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 3 | 3 | Open Nature® Sockeye Salmon Fillet | $14.99 → $14.99 | coupon_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 3 | 4 | Blount's Chicken Pot Pie | $9.99 → $9.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 3 | 5 | Starbucks Iced Coffee | $4.99 → $4.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 3 | 6 | Dannon Oikos Triple Zero or Light + Fit Greek Yogurt | $3.99 → $3.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 3 | 7 | Mission Corn Tortillas | $1.99 → $1.99 | coupon_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 4 | 1 | Signature SELECT Lunchmeat | $5.99 → $5.99 | price_lock_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 5 | 0 | Nabisco Chips Ahoy! Cookies 9.5 to 13-oz. Selected varieties. | $2.49 → $2.49 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 7 | 0 | Betty Crocker Suddenly! Salad | $5.0 → $5.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 7 | 6 | Scott Bath Tissue | $16.99 → $9.0 | coupon_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 7 | 7 | Truff Hot Sauce | $9.99 → $8.99 | coupon_grid_offer |  |
| Safeway | 8 | 0 | Nature's Truth Vitamins | $? → $? | standard_grid_offer | missing_or_unclear_price|missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_pro… |
| Safeway | 8 | 1 | Quest Bar | $5.0 → $5.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 8 | 6 | Boost Original 6 pack | $9.99 → $7.99 | standard_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 8 | 7 | CLIF Builders Protein Bars 6 ct | $10.99 → $7.99 | standard_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Vons | 1 | 1 | Fresh Boneless Skinless Chicken Breasts Available at the full service meat counter LIMIT … | $1.99 → $1.99 | front_page_hero | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Vons | 1 | 10 | Coke or Sprite 6 pack, 16.9 oz. Selected varieties | $14.0 → $14.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Vons | 1 | 3 | Pork Loin Center Cut Chops Value pack or Roast Boneless | $2.99 → $2.99 | front_page_hero | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Vons | 1 | 6 | Blueberries | $3.99 → $1.99 | front_page_hero | crop lowered price vs first-pass — confirm which is correct |
| Vons | 1 | 8 | Medium Ripe Hass Avocados, Roma Tomatoes, White Onions, Tomatillos or Jalapeños | $1.99 → $0.99 | front_page_hero | crop lowered price vs first-pass — confirm which is correct |
| Vons | 2 | 1 | Club, Town House 9.2-13.8 oz. or Keebler Sandwich Crackers 8 ct. | $2.49 → $2.49 | multi_product_group | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Vons | 2 | 11 | Tide Liquid Laundry Detergent 92-132 oz. or PODS 45-76 ct. selected varieties | $16.99 → $16.99 | coupon_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Vons | 2 | 2 | Gatorade 28 oz., Rockstar Energy 16 oz., José Olé Burrito or Chimichanga 5 oz., Banquet P… | $0.99 → $0.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic_product_name |
| Vons | 2 | 4 | Kraft Singles | $2.99 → $2.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic_product_name |
| Vons | 2 | 6 | Dennison’s Chili With Beans 15 oz. Signature SELECT® Croutons 5 oz. or Ripe Pitted Olives… | $5.99 → $1.49 | standard_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Vons | 2 | 8 | Signature SELECT Orange Juice | $4.49 → $4.49 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Vons | 3 | 1 | Farmer John Links 28 oz. Wieners 48 oz. or Hoffy Premium Bacon 12 oz. | $5.99 → $5.0 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Vons | 3 | 14 | Fresh Atlantic Salmon Fillets | $8.99 → $9.99 | standard_grid_offer | crop_tile_mismatch |
| Vons | 3 | 2 | Fresh Baked Mini Brownies 12 ct or Mini Muffins 9-12 ct | $2.5 → $0.5 | friday_only_block | crop lowered price vs first-pass — confirm which is correct |
| Vons | 3 | 7 | Lucerne Large Eggs | $4.99 → $5.99 | standard_grid_offer | crop_tile_mismatch |

## Tracked week-over-week worsens

| Feed | Family | Prior → New | Ratio | Offer |
|---|---|---|---|---|
| Safeway | `eggs_dozen_normalized` | $0.11 (2026-06-10) → $1.99 | 18.09× | Lucerne® Large Eggs 18-CT. |
| Vons | `eggs_dozen_normalized` | $2.49 (2026-07-08) → $4.99 | 2.00× | Lucerne Large Eggs |
| Vons | `nectarines_per_lb` | $1.99 (2026-07-01) → $2.99 | 1.50× | Nectarines |
| Vons | `peaches_per_lb` | $1.99 (2026-07-01) → $2.99 | 1.50× | Large Yellow Peaches |

## What to do

1. Open the flyer page for each crop override — especially `coupon_grid_offer` rows where first-pass and final prices disagree.
2. For WoW worsens, confirm the new ad size/price is real (not bleed from a neighbor tile, party-size, or multipack).
3. Correct sibling `split_offer_items.csv`, then rematch:
   `/usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-ids <id> --feed safeway`

