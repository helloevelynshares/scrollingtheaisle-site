# AisleCheck tracker language coverage

Generated: **2026-08-04**

Authoritative source: `data/canonical_tracker_families.yaml` (this report is derived — do not edit tracker lists by hand).

## Summary

- Active trackers: **86**
- Protected phrases: **47**
- Exclusions: **0**

### Resolution classes

- `category_context_required`: 1
- `exact_alias_safe`: 57
- `package_clarification_required`: 18
- `protected_phrase_required`: 10

### Reachability (NL probes via production contract)

- Reachable: **86** / 86
- Unreachable: **0**


### Collision inventory

- `brand_is_generic_food_term`: 1
- `embedded_category_token`: 47
- `keep_separate_peer`: 114
- `multi_package_brand`: 9
- `shared_alias`: 18

Full collision rows: `evals/entity-resolution/collision-report.json`.

## Per-tracker

| ID | Display | Class | Brand-only safe | Protected phrases | Reachable |
|---|---|---|---|---|---|
| `doritos_5_13oz` | Doritos | `exact_alias_safe` | yes | — | yes |
| `cheetos_regular_bags` | Cheetos | `package_clarification_required` | no | — | yes |
| `cheetos_party_size` | Cheetos Party Size | `package_clarification_required` | no | — | yes |
| `lays_potato_chips_regular` | Lay's potato chips | `package_clarification_required` | no | lay's potato chips | yes |
| `lays_kettle_cooked` | Lay's Kettle Cooked chips | `protected_phrase_required` | yes | lay's kettle cooked chips, kettle cooked potato chips, kettle cooked chips | yes |
| `lays_party_size` | Lay's Party Size | `package_clarification_required` | no | — | yes |
| `kettle_brand_chips` | Kettle Brand potato chips | `protected_phrase_required` | yes | kettle brand potato chips, kettle brand chips, kettle potato chips | yes |
| `ruffles_regular_bags` | Ruffles | `protected_phrase_required` | yes | ruffles potato chips | yes |
| `sun_chips_7oz` | Sun Chips | `protected_phrase_required` | yes | sun chips, sun chips original, sun chips harvest cheddar | yes |
| `tostitos_tortilla_chips` | Tostitos tortilla chips | `protected_phrase_required` | yes | tostitos tortilla chips | yes |
| `simply_snacks` | Simply snacks | `exact_alias_safe` | yes | — | yes |
| `simply_party_size` | Simply Party Size | `exact_alias_safe` | yes | — | yes |
| `popcorners` | PopCorners | `exact_alias_safe` | yes | — | yes |
| `ritz_crackers` | Ritz crackers | `exact_alias_safe` | yes | — | yes |
| `ritz_toasted_chips` | Nabisco Ritz Toasted Chips | `protected_phrase_required` | yes | nabisco ritz toasted chips, ritz toasted chips | yes |
| `nabisco_snack_crackers_regular` | Wheat Thins, Triscuit & Chicken in a Biskit — regular size | `package_clarification_required` | no | — | yes |
| `nabisco_snack_crackers` | Wheat Thins, Triscuit & Chicken in a Biskit | `package_clarification_required` | no | — | yes |
| `cheez_it_crackers` | Cheez-It crackers | `exact_alias_safe` | yes | — | yes |
| `chips_ahoy` | Chips Ahoy cookies | `protected_phrase_required` | yes | chips ahoy cookies, chips ahoy, chips ahoy original | yes |
| `oreo_family_size` | Oreo cookies | `exact_alias_safe` | yes | — | yes |
| `goldfish_bags` | Goldfish | `protected_phrase_required` | yes | goldfish | yes |
| `keebler_sandwich_crackers` | Keebler sandwich crackers | `exact_alias_safe` | yes | — | yes |
| `coca_cola_12packs` | Coca-Cola | `exact_alias_safe` | yes | — | yes |
| `pepsi_12packs` | Pepsi | `exact_alias_safe` | yes | — | yes |
| `dr_pepper_12packs` | Dr Pepper | `exact_alias_safe` | yes | — | yes |
| `lacroix_8pack` | LaCroix sparkling water | `exact_alias_safe` | yes | — | yes |
| `simply_refrigerated_juice_lemonade` | Simply juice | `exact_alias_safe` | yes | — | yes |
| `haagen_dazs_pints` | Häagen-Dazs ice cream pints | `package_clarification_required` | no | — | yes |
| `ben_jerrys_ice_cream` | Ben & Jerry's ice cream | `exact_alias_safe` | yes | — | yes |
| `dreyers_tubs` | Dreyer's ice cream | `exact_alias_safe` | yes | — | yes |
| `breyers_ice_cream` | Breyers ice cream | `exact_alias_safe` | yes | — | yes |
| `tillamook_ice_cream` | Tillamook ice cream | `exact_alias_safe` | yes | — | yes |
| `haagen_dazs_bars_novelties` | Häagen-Dazs bars / novelties | `package_clarification_required` | no | — | yes |
| `dreyers_novelties` | Dreyer's novelties | `exact_alias_safe` | yes | — | yes |
| `strawberries_1_2lb` | Strawberries | `exact_alias_safe` | yes | — | yes |
| `seedless_grapes_per_lb` | Seedless grapes | `exact_alias_safe` | yes | — | yes |
| `cherries_per_lb` | Cherries | `exact_alias_safe` | yes | — | yes |
| `berries_6oz` | Blueberries / raspberries / blackberries | `exact_alias_safe` | yes | — | yes |
| `hass_avocados_each` | Hass avocados | `exact_alias_safe` | yes | — | yes |
| `mangoes_each` | Mangoes | `exact_alias_safe` | yes | — | yes |
| `peaches_per_lb` | Peaches | `exact_alias_safe` | yes | — | yes |
| `nectarines_per_lb` | Nectarines | `exact_alias_safe` | yes | — | yes |
| `plums_per_lb` | Plums | `exact_alias_safe` | yes | — | yes |
| `sweet_corn` | Sweet corn | `exact_alias_safe` | yes | — | yes |
| `eggs_dozen_normalized` | Lucerne Eggs | `exact_alias_safe` | yes | — | yes |
| `lucerne_eggs_18` | Lucerne Eggs (18-count) | `exact_alias_safe` | yes | — | yes |
| `butter_16oz` | Butter | `category_context_required` | no | — | yes |
| `sliced_or_shredded_cheese_6_8oz` | Sliced or shredded cheese | `exact_alias_safe` | yes | — | yes |
| `philadelphia_cream_cheese` | Philadelphia cream cheese | `exact_alias_safe` | yes | — | yes |
| `lucerne_cream_cheese` | Lucerne cream cheese | `package_clarification_required` | no | — | yes |
| `chobani_yogurt_per_cup` | Chobani yogurt cups | `package_clarification_required` | no | — | yes |
| `chobani_yogurt_tub` | Chobani yogurt tub | `package_clarification_required` | no | — | yes |
| `fage_cups` | Fage Greek yogurt cups | `package_clarification_required` | no | — | yes |
| `fage_tub` | Fage Greek yogurt tub | `package_clarification_required` | no | — | yes |
| `lucerne_yogurt_tubs` | Lucerne yogurt tubs | `package_clarification_required` | no | — | yes |
| `nature_valley_bars` | Nature Valley bars | `exact_alias_safe` | yes | — | yes |
| `general_mills_cereal_regular` | General Mills cereal | `package_clarification_required` | no | general mills cereal, chex cereal, honey nut cheerios cereal | yes |
| `general_mills_cereal_family_size` | General Mills cereal (family size) | `package_clarification_required` | no | general mills cereal (family size), general mills family size cereal, family size cereal | yes |
| `post_cereal_regular` | Post cereal | `package_clarification_required` | no | post cereal | yes |
| `post_cereal_giant_size` | Post cereal (giant size) | `package_clarification_required` | no | post cereal (giant size), giant size post cereal, post giant size cereal | yes |
| `thomas_bagels_muffins_bread` | Thomas bagels / English muffins / swirl bread | `exact_alias_safe` | yes | — | yes |
| `kings_hawaiian_rolls` | King's Hawaiian rolls | `exact_alias_safe` | yes | — | yes |
| `pillsbury_refrigerated_dough` | Pillsbury ready-to-bake dough | `exact_alias_safe` | yes | — | yes |
| `quest_bars` | Quest bars | `exact_alias_safe` | yes | — | yes |
| `clif_bars` | Clif Bars | `exact_alias_safe` | yes | — | yes |
| `chicken_breast_per_lb` | Chicken breast | `exact_alias_safe` | yes | — | yes |
| `chicken_thigh_per_lb` | Chicken thighs | `exact_alias_safe` | yes | — | yes |
| `ribeye_steak` | Ribeye steak | `exact_alias_safe` | yes | — | yes |
| `tri_tip_roast` | Tri-tip roast | `exact_alias_safe` | yes | — | yes |
| `salmon` | Salmon | `exact_alias_safe` | yes | — | yes |
| `cape_cod_chips` | Cape Cod potato chips | `protected_phrase_required` | yes | cape cod potato chips, cape cod chips, cape cod kettle chips | yes |
| `smartfood_popcorn` | Smartfood popcorn | `exact_alias_safe` | yes | smartfood | yes |
| `pringles` | Pringles | `protected_phrase_required` | yes | pringles chips | yes |
| `snyders_pretzels` | Snyder's pretzels | `exact_alias_safe` | yes | — | yes |
| `frito_lay_multipack_chips` | Frito-Lay variety pack | `exact_alias_safe` | yes | — | yes |
| `pop_tarts` | Pop-Tarts | `exact_alias_safe` | yes | — | yes |
| `kellogg_breakfast_bars` | Nutri-Grain & Special K bars | `exact_alias_safe` | yes | — | yes |
| `betty_crocker_fruit_snacks` | Gushers / Fruit by the Foot | `exact_alias_safe` | yes | — | yes |
| `waterloo_sparkling_water` | Waterloo sparkling water | `exact_alias_safe` | yes | — | yes |
| `bell_peppers` | Bell peppers | `exact_alias_safe` | yes | — | yes |
| `chicken_wings_per_lb` | Chicken wings | `exact_alias_safe` | yes | — | yes |
| `mandarins_3lb` | Mandarin oranges (Cuties) | `exact_alias_safe` | yes | — | yes |
| `beef_short_ribs_per_lb` | Beef short ribs | `exact_alias_safe` | yes | — | yes |
| `pork_spare_ribs_per_lb` | Pork spare ribs | `exact_alias_safe` | yes | — | yes |
| `oscar_mayer_hot_dogs` | Oscar Mayer hot dogs | `exact_alias_safe` | yes | — | yes |
| `cake_mix` | Cake mix | `exact_alias_safe` | yes | — | yes |

## Notes

- `exact_alias_safe`: short brand/name uniquely maps to one family.
- `protected_phrase_required`: name embeds a category heuristic token; multiword phrase must be protected.
- `package_clarification_required`: same brand, multiple package/form trackers.
- Reachability probes use queries like `Safeway <name> are $2.49`. A `clarify` that already selects the correct tracker counts as reachable.

