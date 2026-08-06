# Weekly ad import QA: 2026-08-05

Auto checklist for crop-price overrides and tracked week-over-week worsens.
**Findings:** 122 crop overrides, 3 WoW worsens.

## Crop price overrides

| Feed | Pg | Idx | Product | First-pass → Final | Layout | Note |
|---|---|---|---|---|---|---|
| Safeway | 10 | 7 | RXBAR Protein Bar | $2.0 → $4.0 | standard_grid_offer | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 3 | 7 | Signature SELECT Pizza 17.2-31.5 oz | $5.49 → $9.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 8 | 1 | Mariani Snack Packs | $2.99 → $4.99 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 8 | 16 | Picwest Farms Grilling Vegetables Selected varieties | $1.99 → $3.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 8 | 9 | Mahatma Basmati Rice | $3.99 → $5.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 9 | 11 | Gillette or Old Spice Shave Gel Selected varieties. | $4.99 → $8.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 9 | 12 | Mighty Patch Selected varieties. | $6.99 → $12.99 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 9 | 8 | Method Body Wash Selected varieties. | $7.99 → $9.99 | points_promo_block | crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 2 | 18 | Gatorade 8 pk. | $5.99 → $7.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 2 | 19 | Lindt Truffles | $5.99 → $7.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Vons | 2 | 5 | Stouffer’s, Lean Cuisine Entrees, Signature SELECT Shredded Cheese | $2.79 → $4.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop raised price vs first-pass — check adjacent-tile bleed |
| Safeway | 1 | 1 | Sweet Corn | $1.0 → $1.0 | front_page_hero | first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 1 | 10 | Doritos, Fritos, PopCorners or Smartfood 5 to 10.75 oz. | $? → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 1 | 11 | Coca-Cola 6 pack, Dasani Water 24 pack, Monster Energy Drinks | $? → $3.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 1 | 11 | Coca-Cola 12-pack 12-oz cans | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 1 | 11 | LESSER VALUE MEMBER PRICE WHEN YOU BUY 4 | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 1 | 7 | Thomas’ Bagels, English Muffins or Swirl Bread 12 to 18-oz. Artesano Bread or Buns 13.55 … | $? → $? | standard_grid_offer | missing_or_unclear_price|missing_package_size|ambiguous_multi_product_offer|first_pass_crop_disagreement|crop_verificat… |
| Safeway | 1 | 8 | Thomas’ Bagels, English Muffins or Swirl Bread 6 to 13 oz. or Oroweat Bread 24 oz. | $? → $? | standard_grid_offer | missing_or_unclear_price|first_pass_crop_disagreement|crop_verification_override|crop_override_package |
| Safeway | 10 | 1 | Mike & Ike or Hot Tamales Theater Box | $1.49 → $1.49 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 10 | 10 | Gerber Organic Pouch | $1.2 → $1.2 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 10 | 11 | Barbells Protein Bars | $8.99 → $8.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 10 | 4 | Nerds Clusters Candy or Sweetarts Chewy Fusions | $4.99 → $4.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 2 | 1 | Halo Top Ice Cream | $5.99 → $5.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 11 | Main St. Bistro Roasted Potatoes | $4.99 → $4.99 | standard_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 2 | 14 | Taylor Farms Chopped Salad Kit | $4.49 → $4.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 14 | Taylor Farms Chopped Salad Kit | $? → $4.49 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 2 | 18 | Envy Apples | $2.99 → $2.99 | standard_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 2 | 19 | Primo Taglio Ham off the Bone Or Cheddar Cheese | $9.99 → $8.99 | standard_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 2 | 2 | Kellogg's Raisin Bran or Frosted Flakes Cereal | $2.99 → $2.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 23 | Jumbo Cookies 8-ct. Fresh Baked. Selected varieties. | $5.99 → $5.99 | standard_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 2 | 3 | Lay's Potato Chips | $1.99 → $1.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 4 | McCormick Grill Mates or Lawry's Marinades | $2.39 → $2.39 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 2 | 5 | Gain Laundry Detergent | $15.99 → $15.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 13 | Tate's Bake Shop Cookies 7 oz | $3.99 → $4.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 13 | Tate's Bake Shop Cookies 7 oz | $? → $3.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 3 | 14 | Oreo Cookies 12.2-20 oz | $3.99 → $3.49 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 14 | Oreo Cookies 12.2-20 oz | $? → $3.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 3 | 17 | La Tortilla Factory Sonora Style Flour Tortillas 10 ct | $3.99 → $3.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 21 | Dixie Paper Plates, Quilted Northern Bath Tissue 6 mega rolls, Angel Soft Bath Tissue 6 m… | $12.99 → $12.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 22 | Tide Laundry Detergent 92 oz | $9.99 → $9.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 7 | Signature SELECT Pizza 17.2-31.5 oz | $? → $5.49 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 3 | 9 | Redwood Hill Farm Goat Milk Yogurt 24 oz | $4.49 → $3.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 3 | 9 | Redwood Hill Farm Goat Milk Yogurt 24 oz | $? → $4.49 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 4 | 1 | Signature SELECT® Lunchmeat | $5.99 → $5.99 | price_lock_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 4 | 10 | 8-Piece Fried or | $5.0 → $5.0 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 4 | 14 | 8-Piece Fried or Roasted Chicken | $5.0 → $5.0 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Safeway | 4 | 16 | Hass Avocado | $5.0 → $5.0 | friday_only_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 2 | Essentia Water | $4.0 → $4.0 | price_lock_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package |
| Safeway | 4 | 20 | Sukhi’s Gourmet Entrée New York Style Sausage Del Real Tamales | $5.0 → $5.0 | friday_only_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic_product_name |
| Safeway | 4 | 6 | Nature’s Harvest® Sandwich Bread | $3.49 → $2.69 | price_lock_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 4 | 6 | Nature’s Harvest® Sandwich Bread | $? → $3.49 | price_lock_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 6 | 0 | Capri Sun 10-pack, 6 oz. Selected varieties. | $7.0 → $7.0 | front_page_hero | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Safeway | 7 | 2 | Fage Yogurt | $5.99 → $5.99 | standard_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 8 | 0 | Bonduelle Bistro Grande Bowl | $5.99 → $5.99 | points_promo_block | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_product_name |
| Safeway | 8 | 10 | Blue Diamond Almondmilk 48-oz. Selected varieties. | $3.99 → $3.99 | standard_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Safeway | 8 | 13 | Don Francisco's Coffee Selected varieties | $14.99 → $3.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 8 | 13 | Don Francisco's Coffee Selected varieties | $? → $14.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 8 | 14 | Yakult Probiotic Drink Live & Active Probiotic Drink | $2.99 → $3.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 8 | 14 | Yakult Probiotic Drink Live & Active Probiotic Drink | $? → $2.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 8 | 15 | Bays English Muffins | $2.99 → $3.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 8 | 15 | Bays English Muffins | $? → $2.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 8 | 16 | Picwest Farms Grilling Vegetables Selected varieties | $? → $1.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 8 | 18 | Home Run Inn Pizza or Deep Dish Pizza | $5.99 → $3.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 8 | 18 | Home Run Inn Pizza | $? → $5.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 8 | 18 | Deep Dish Pizza | $? → $5.99 | coupon_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 8 | 19 | Frito-Lay Snack Pack | $10.99 → $10.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 8 | 20 | Ruffles, Doritos or Sabritas Gold Series Potato Chips | $4.99 → $4.99 | coupon_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 8 | 21 | Scott Bath Tissue | $10.99 → $2.99 | coupon_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 8 | 5 | BelGioioso Mozzarella, Fresh Mozzarella, Burrata or Ricotta | $5.99 → $5.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 8 | 7 | Icelandic Yogurt | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Safeway | 8 | 9 | Mahatma Basmati Rice | $? → $3.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 10 | Mighty Patch Hero Mighty Patch Value 2 Pack | $12.99 → $7.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 10 | Mighty Patch Hero Mighty Patch Value 2 Pack | $? → $12.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 11 | Gillette or Old Spice Shave Gel Selected varieties. | $? → $4.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 13 | Crest Toothpaste Selected varieties. | $8.99 → $4.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 13 | Crest Toothpaste Selected varieties. | $? → $8.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Safeway | 9 | 5 | Pantene Aussie Hair Care Selected varieties. | $9.99 → $5.99 | points_promo_block | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 6 | Olay or Secret Outlast Deodorant Selected varieties. | $7.99 → $7.99 | points_promo_block | first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Safeway | 9 | 7 | Garnier Fructis Shampoo or Conditioner Selected varieties. | $9.99 → $5.99 | points_promo_block | crop lowered price vs first-pass — confirm which is correct |
| Safeway | 9 | 9 | Neutrogena Rapid Wrinkle Repair Selected varieties. | $8.99 → $8.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 1 | 0 | Fresh Boneless Skinless Chicken Breasts Value Pack | $1.99 → $1.99 | front_page_hero | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price |
| Vons | 1 | 11 | Soleil Sparkling Water 8 pk, 12 oz cans | $2.99 → $2.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package_promo_mechanic |
| Vons | 1 | 12 | Soleil™ Sparkling Water | $? → $2.99 | brand_ad_panel | missing_or_unclear_price|unclear_product_name|first_pass_crop_disagreement|crop_verification_override|crop_override_pri… |
| Vons | 1 | 2 | Butterball 85% Lean Ground Turkey | $2.99 → $2.99 | front_page_hero | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Vons | 1 | 4 | Large Yellow Peaches, Yellow Nectarines or Plums | $1.99 → $1.99 | front_page_hero | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_product_name |
| Vons | 1 | 6 | Taylor Farms Chopped Salad Kits | $3.0 → $1.99 | front_page_hero | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Vons | 1 | 6 | Taylor Farms Chopped Salad Kits | $? → $3.0 | front_page_hero | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 1 | 8 | Coke, Pepsi Canada Dry or Dr Pepper | $? → $? | multi_product_group | missing_or_unclear_price|first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Vons | 1 | 9 | Lucerne Butter 16 oz. Signature SELECT Ice Cream or Novelties 1.5 qt. or 12-16 ct. Select… | $2.99 → $2.99 | standard_grid_offer | missing_package_size|first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic… |
| Vons | 2 | 1 | BodyArmor SuperDrink 16 oz. vitanminwater 20 oz. Powerade 28 oz. Coke de Mexico 12 oz. +C… | $0.99 → $0.99 | multi_product_group | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Vons | 2 | 11 | Frito Lay Party Size Tortilla Chips, Tostitos, Simply, Ruffles, Doritos, Lay’s Kettle Chi… | $4.99 → $5.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 2 | 11 | Frito Lay Party Size Tortilla Chips, Tostitos, Simply, Ruffles, Doritos, Lay’s Kettle Chi… | $? → $4.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 2 | 12 | Signature SELECT Pizza, Red Baron Pizza, Hot Pockets, Bagel Bites, Totino’s Pizza Rolls, … | $4.99 → $3.49 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Vons | 2 | 12 | Signature SELECT Pizza, Red Baron Pizza, Hot Pockets, Bagel Bites, Totino’s Pizza Rolls, … | $? → $4.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 2 | 17 | Listerine Mouthwash, Benadryl Allergy Tablet | $6.99 → $7.99 | points_promo_block | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 2 | 17 | Listerine Mouthwash, Benadryl Allergy Tablet | $? → $6.99 | points_promo_block | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 2 | 18 | Gatorade 8 pk. | $? → $5.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 2 | 19 | Lindt Truffles | $? → $5.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 2 | 2 | Gatorade 28 oz. Poppi Prebiotic Singles 12 oz. +CRV Pringles 5.2-5.57 oz. Hamburger Helpe… | $1.49 → $1.49 | multi_product_group | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Vons | 2 | 20 | Werther’s Caramel or Reisen Chews | $1.99 → $1.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_promo_mechanic_product_name |
| Vons | 2 | 21 | The Sausage Project Chicken Sausage | $3.49 → $3.49 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 2 | 22 | Yoplait Yogurt | $0.69 → $0.69 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_promo_mechanic |
| Vons | 2 | 27 | Florida's Natural Lemonade | $2.99 → $2.99 | standard_grid_offer | first_pass_crop_disagreement|crop_verification_override|crop_override_package_product_name |
| Vons | 2 | 3 | Florida's Natural Lemonade 59 oz., Refrigerated Starbucks Frappuccino 9.5 oz. Tree Top 10… | $1.99 → $1.99 | multi_product_group | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Vons | 2 | 30 | Fage Total Greek Yogurt | $5.99 → $5.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 2 | 31 | Mission Carb Balance Tortillas | $4.99 → $4.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 2 | 32 | Redvines Red or Black Licorice Twists | $3.59 → $3.59 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 2 | 4 | Dole Fruit 4 ct. cups Capri Sun 10 pack Quaker Simply Granola 18-24.1 oz. Instant Oatmeal… | $2.99 → $2.99 | multi_product_group | first_pass_crop_disagreement|crop_verification_override|crop_override_price_package_product_name |
| Vons | 2 | 5 | Stouffer’s, Lean Cuisine Entrees, Signature SELECT Shredded Cheese | $? → $2.79 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 2 | 6 | Clausen Pickles, Vlasic Pickles, Mt. Olive Pickles, Nathan’s Pickles, Ba Tampte Pickles | $3.99 → $4.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 2 | 6 | Clausen Pickles, Vlasic Pickles, Mt. Olive Pickles, Nathan’s Pickles, Ba Tampte Pickles | $? → $3.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 3 | 0 | Kellogg’s Nutri-Grain Bars, Rice Krispies Treats, Pop-Tarts, Town House or Club Crackers | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 3 | 1 | Kellogg’s Cereal | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 3 | 11 | USDA Choice Beef Loin Boneless New York Steaks Value Pack | $7.99 → $4.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Vons | 3 | 11 | USDA Choice Beef Loin Boneless New York Steaks Value Pack | $? → $7.99 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 3 | 2 | General Mills Cereal | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 3 | 3 | Hostess Multipack Snacks | $5.0 → $2.99 | standard_grid_offer | crop lowered price vs first-pass — confirm which is correct |
| Vons | 3 | 4 | Kellogg’s Eggo Waffles | $5.0 → $2.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop; crop lowered price vs first-pass — confirm which is correct |
| Vons | 3 | 4 | Kellogg’s Eggo Waffles | $? → $5.0 | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 3 | 5 | Ziploc Bags | $? → $3.99 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |
| Vons | 3 | 5 | Ziploc Bags | $? → $? | standard_grid_offer | crop_tile_mismatch in consolidated split — do not trust for tracked match |
| Vons | 3 | 8 | Large Hass Avocados | $5.0 → $5.0 | standard_grid_offer | crop_tile_mismatch — first-pass tile identity disagreed with crop |

## Tracked week-over-week worsens

| Feed | Family | Prior → New | Ratio | Offer |
|---|---|---|---|---|
| Safeway | `ruffles_regular_bags` | $2.50 (2026-07-08) → $4.99 | 2.00× | Ruffles Potato Chips 6-8.5 oz |
| Vons | `cheez_it_crackers` | $1.67 (2026-07-08) → $4.99 | 2.99× | Signature SELECT Pizza, Red Baron Pizza, Hot Pockets, Bagel Bites, Totino’s Pizza Rolls, … |
| Vons | `doritos_5_13oz` | $2.75 (2026-07-29) → $4.99 | 1.81× | Frito Lay Party Size Tortilla Chips, Tostitos, Simply, Ruffles, Doritos, Lay’s Kettle Chi… |

## What to do

1. Open the flyer page for each crop override — especially `coupon_grid_offer` rows where first-pass and final prices disagree.
2. For WoW worsens, confirm the new ad size/price is real (not bleed from a neighbor tile, party-size, or multipack).
3. Correct sibling `split_offer_items.csv`, then rematch:
   `/usr/bin/python3 scripts/generate_weekly_ad_prices.py --product-ids <id> --feed safeway`

