# Weekly ad import QA: 2026-07-22

Auto checklist for crop-price overrides and tracked week-over-week worsens.
**Findings:** 126 crop overrides, 2 WoW worsens.

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
| Vons | 1 | 16 | Gain Laundry Detergent Flings | $5.99 → $12.99 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 1 | 20 | Crest Toothpaste | $2.99 → $6.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 1 | 7 | Blueberries | $0.99 → $5.99 | front_page_hero | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 2 | 3 | Bounty Paper Towels 6 double plus rolls Selected varieties | $9.99 → $14.99 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 2 | 6 | Dawn Dish Soap 6.5-7 oz. | $4.99 → $8.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 3 | 10 | Planet Oat Oatmilk 52 oz. Jell-O 4 ct. Refrigerated Selected varieties | $4.99 → $7.0 | standard_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 3 | 4 | Signature SELECT Ice Cream 1.5 qt. | $2.49 → $4.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 3 | 5 | Eggo Waffles 8 to 12 ct. | $2.56 → $4.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 3 | 8 | Corona, Stella Artois 24 pack, 11.2-12 oz. bottles Pacifico or Modelo 24 pack, 12 oz. bot… | $2.99 → $24.99 | standard_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 3 | 9 | Oscar Mayer Lunchables 2.25 to 4.4 oz. | $1.99 → $5.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 4 | 16 | Signature SELECT Frozen Fruit | $5.0 → $10.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
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
| Vons | 1 | 0 | Fresh 80% Lean Ground Beef | $3.99 → $3.99 | front_page_hero | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Vons | 1 | 11 | Coke, Diet Coke, Sprite, Dr Pepper, Pepsi, Diet Pepsi or Mountain Dew | $? → $? | multi_product_group | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 1 | 12 | Doritos, Ruffles, Lay’s Potato Chips, Lay’s Kettle Cooked Potato Chips, Lay’s Poppables o… | $6.0 → $5.0 | multi_product_group | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 1 | 12 | Doritos 5 to 8.25 oz | $? → $6.0 | multi_product_group | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 12 | Ruffles 5 to 8.25 oz | $? → $6.0 | multi_product_group | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 12 | Lay’s Potato Chips 5 to 8.25 oz | $? → $6.0 | multi_product_group | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 12 | Lay’s Kettle Cooked Potato Chips 5 to 8.25 oz | $? → $6.0 | multi_product_group | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 12 | Lay’s Poppables 5 to 8.25 oz | $? → $6.0 | multi_product_group | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 12 | Lay’s Simply Snacks 5 to 8.25 oz | $? → $6.0 | multi_product_group | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 18 | Trash Odor Fighter Starter Kit 1 ct. Refill 2 ct., 0.16 oz. or Puffs Facial Tissues 4 pac… | $7.99 → $5.99 | points_promo_block | crop lowered price vs first-pass — confirm which is correct |
| Vons | 1 | 19 | Pantene 16-17.9 oz. Head & Shoulders 10.9-12.5 oz. Shampoo & Conditioner or Pantene Styli… | $6.99 → $6.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Vons | 1 | 20 | Crest Toothpaste | $? → $2.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 21 | Signature SELECT Purified Water | $1.99 → $1.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 1 | 3 | Petite Sirloin Steaks or Chuck Roast Boneless | $5.99 → $5.99 | front_page_hero | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Vons | 1 | 5 | Large Strawberries, Raspberries or Blackberries | $3.99 → $0.99 | front_page_hero | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Vons | 1 | 5 | Large Strawberries, Raspberries | $? → $3.99 | front_page_hero | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 5 | Blackberries | $? → $3.99 | front_page_hero | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 7 | Blueberries | $? → $0.99 | front_page_hero | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 9 | 8 Piece Bucket, Fried or Baked | $5.99 → $0.6 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Vons | 1 | 9 | 8 Piece Bucket, Fried | $? → $5.99 | friday_only_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 9 | Baked | $? → $5.99 | friday_only_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 2 | 1 | Charmin Bath Tissue 12 Double Rolls or Bounty Paper Towels 6 Big Rolls | $14.99 → $14.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Vons | 2 | 2 | Bounty Paper Towels 8 Single Plus Rolls | $14.99 → $14.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Vons | 2 | 4 | Cascade ActionPacs Dishwasher Detergent 14-25 ct. or Dawn Powerwash 16 oz. | $9.99 → $9.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Vons | 2 | 6 | Dawn Dish Soap 6.5-7 oz. | $? → $4.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 3 | 2 | Poppi Prebiotic Singles 12 oz. +CRV Rosarita Beans 15-16 oz. Betty Crocker Instant Potato… | $1.99 → $1.49 | multi_product_group | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic_product_name |
| Vons | 3 | 3 | Signature SELECT® Cooking Spray 5-6 oz. Nabisco Snak-Saks 8 oz. or La Victoria Enchilada … | $1.99 → $1.99 | multi_product_group | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic_product_name |
| Vons | 3 | 4 | Signature SELECT Ice Cream 1.5 qt. | $? → $2.49 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 3 | 5 | Eggo Waffles 8 to 12 ct. | $? → $2.56 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 3 | 9 | Oscar Mayer Lunchables 2.25 to 4.4 oz. | $? → $1.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 4 | 1 | Hass Avocados | $5.0 → $5.0 | friday_only_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Vons | 4 | 13 | Large Mangos or Avocados | $10.0 → $10.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 4 | 16 | Signature SELECT Frozen Fruit | $? → $5.0 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 4 | 17 | Signature SELECT Salad Blends or Kits | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 4 | 2 | Signature SELECT Pizza | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 4 | 3 | Signature SELECT Ice Cream | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 4 | 4 | Signature SELECT Cheese | $5.0 → $5.0 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Vons | 4 | 7 | Fresh Sushi | $5.0 → $5.0 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic_product_name |
| Vons | 4 | 8 | Bakery Fresh Mini Croissants | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 4 | 9 | Bakery Fresh Mini Muffins | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |

## Tracked week-over-week worsens

| Feed | Family | Prior → New | Ratio | Offer |
|---|---|---|---|---|
| Safeway | `tillamook_ice_cream` | $3.50 (2026-06-24) → $5.70 | 1.63× | Tillamook Ice Cream 48 oz |
| Vons | `seedless_grapes_per_lb` | $1.99 (2026-07-15) → $3.99 | 2.01× | Black Seedless Grapes |

## What to do

1. Open the flyer page for each crop override — especially `coupon_grid_offer` rows where first-pass and final prices disagree.
2. For WoW worsens, confirm the new ad size/price is real (not bleed from a neighbor tile, party-size, or multipack).
3. Correct sibling `split_offer_items.csv`, then rematch:
   `/usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-ids <id> --feed safeway`

