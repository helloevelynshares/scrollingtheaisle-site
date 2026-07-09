# Content gap analysis — Safeway 2026-07-08

_Generated 2026-07-08T15:33:09.907808+00:00 · CONTENT ANALYSIS ONLY (no website UI changed, no tracker graph updated)._

## Why the manual shortlist differs from the previous report.

The previous `fresh_costco_deal_report` was optimized for canonical tracker-graph-safe matches: an item only ranked well if it had a canonical family, an exact/usable baseline, and a same-product Costco match that was safe to write to a price graph. That is the right bar for the tracker graphs (it is what keeps smoked salmon from overwriting the fresh-salmon chart), but it is the wrong bar for content. As a result the graph-safe report omitted or buried items that are excellent *content* deals but are ad-deal-only (raw shrimp, bell peppers, Nestle Drumstick, beef chuck short ribs, Sargento cheese), have no Costco mapping, rely on a proxy/comparable match, or are Friday-only. This content-first view keeps the same-strict 'beats Costco' guardrails but scores items on shopper interest, absolute price, category, seasonality, and TikTok hook — so a $5 Friday shrimp or a $0.99 avocado surfaces even when the graph pipeline would never chart it. Canonical eligibility is untouched; nothing here updates any tracker graph.

## Missing/downranked item table

All Costco comparisons use **Costco San Francisco** (Safeway → San Francisco; Vons → Tustin).

### Table A — shortlist item, ad provenance, availability

| Item from shortlist | Raw weekly ad offer text | Source PDF & page | Parsed ad price | Parsed package size / unit | Full-week or Friday-only |
|---|---|---|---|---|---|
| Hass avocados | Hass Avocado 99¢ EA MEMBER PRICE | safeway 7-8 - 7-14.pdf p1 | $0.99 (each) | each | full-week |
| Nestle Drumstick ice cream cones | Nestlé Drumstick 8-ct. 5.00 ea Member Price | safeway 7-8 - 7-14.pdf p4 | $5.00 (8-ct box ($0.63/cone)) | 8-ct. | Friday-only |
| Pork shoulder country-style ribs | Signature SELECT Pork Shoulder Country Style Ribs or Blade Steaks Pork Spareribs 2.99 LB MEMBER PRICE | safeway 7-8 - 7-14.pdf p1 | $2.99 (lb) | lb | full-week |
| Sweet corn | Sweet Corn 10 for $5 Member Price | safeway 7-8 - 7-14.pdf p4 | $0.50 (ear (10 for $5)) | 10 for $5 | Friday-only |
| Berry deal (blackberries / raspberries / blueberries) | Blueberries Pint, Raspberries or Blackberries 6 oz 2.99 EA MEMBER PRICE MIX & MATCH | safeway 7-8 - 7-14.pdf p1 | $2.99 (6 oz (mix & match)) | Pint, 6 oz | full-week |
| Doritos tortilla chips | Doritos Tortilla Chips or Ruffles Potato Chips 2 for $5 Member Price | safeway 7-8 - 7-14.pdf p4 | $2.50 (bag (2 for $5)) | 2 for $5 | Friday-only |
| Bell peppers (red/orange/yellow/green) | Red, Orange, Yellow or Green Bell Pepper 5 for $5 Member Price | safeway 7-8 - 7-14.pdf p4 | $1.00 (each (5 for $5)) | 5 for $5 | Friday-only |
| Sargento string/stick cheese | Sargento String or Stick Cheese or Ritz Shareables $4.99 Member Price | safeway 7-8 - 7-14.pdf p6 | $4.99 (pack) | pack | full-week |
| Raw shrimp (Waterfront Bistro 31-40 ct) | $5 lb Member Price Waterfront Bistro Large Raw Shrimp 31-40 ct, 2 lb bag, Frozen | safeway 7-8 - 7-14.pdf p4 | $5.00 (lb ($5 Friday; 2 lb bag)) | 31-40 ct, 2 lb bag | Friday-only |
| Oreo family size | Nabisco Family Size Oreo Cookies 10.68 to 18.71-oz. Snack Crackers 11.5 to 14-oz. Selected varieties. Limit 4 items. 3.49 EA MEMBER PRICE | safeway 7-8 - 7-14.pdf p1 | $3.49 (family-size pack) | 10.68 to 18.71-oz. | full-week |
| Chobani Greek yogurt (3/$4 single-serve) | Chobani Greek Yogurt, Oikos Triple Zero Greek Yogurt, or Danone Light + Fit Greek Yogurt Selected varieties. 4.5-5.3 oz. 3/$4 Member Price | safeway 7-8 - 7-14.pdf p3 | $1.33 (cup (3 for $4)) | 4.5-5.3 oz. | full-week |
| Beef chuck short ribs | USDA Choice Beef Chuck Short Ribs 7.99 LB MEMBER PRICE | safeway 7-8 - 7-14.pdf p1 | $7.99 (lb) | lb | full-week |

### Table B — Costco comparison, match quality, verdict

| Item from shortlist | Costco matched item | Costco warehouse | Costco price | Costco size / unit | Grocery unit price | Costco unit price | % diff | Match type | Updates canonical graph | Safe for content script | Why previously missed/downranked |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Hass avocados | AVOCADOS HASS VARIETY 6 COUNT | Costco San Francisco | $7.99 | 6 each | $0.990/each | $1.332/each | +26% (grocery cheaper) | exact same product | yes | lead-worthy | not missed - already lead-worthy |
| Nestle Drumstick ice cream cones | unknown (coverage gap) | Costco San Francisco | unknown | unknown | $0.625/cone | unknown | unknown | proxy / manual-review | no | manual verification | missing Costco mapping |
| Pork shoulder country-style ribs | PORK SHOULDER COUNTRY RIBS BONELESS PER LB. | Costco San Francisco | $3.79 | 1 lb | $2.990/lb | $3.790/lb | +21% (grocery cheaper) | exact same product | no | lead-worthy | missing canonical tracker family |
| Sweet corn | unknown (coverage gap) | Costco San Francisco | unknown | unknown | $0.500/each | unknown | unknown | proxy / manual-review | yes | strong supporting mention | Friday-only penalty |
| Berry deal (blackberries / raspberries / blueberries) | ORGANIC BLACKBERRIES 12 OZ | Costco San Francisco | $8.99 | 12 oz | $0.498/oz | $0.749/oz | +34% (grocery cheaper) | same category comparable | yes | strong supporting mention | missing Costco mapping |
| Doritos tortilla chips | DORITOS NACHO CHEESE 30 OUNCES | Costco San Francisco | $6.99 | 30 oz | $0.270/oz | $0.233/oz | -16% (Costco cheaper) | same product different size | yes | quick mention | Friday-only penalty |
| Bell peppers (red/orange/yellow/green) | unknown (coverage gap) | Costco San Francisco | unknown | unknown | $1.000/each | unknown | unknown | proxy / manual-review | no | strong supporting mention | category not prioritized |
| Sargento string/stick cheese | GALBANI WHOLE MILK STRING CHEESE 60 COUNT 1 OUNCE EACH | Costco San Francisco | $11.49 | 60 stick | $0.416/stick | $0.192/stick | -117% (Costco cheaper) | same category comparable | no | strong supporting mention | category not prioritized |
| Raw shrimp (Waterfront Bistro 31-40 ct) | unknown (coverage gap) | Costco San Francisco | unknown | unknown | $5.000/lb | unknown | unknown | proxy / manual-review | no | manual verification | missing canonical tracker family |
| Oreo family size | unknown (coverage gap) | Costco San Francisco | unknown | unknown | $0.237/oz | unknown | unknown | proxy / manual-review | yes | quick mention | missing Costco mapping |
| Chobani Greek yogurt (3/$4 single-serve) | CHOBANI GREEK YOGURT VARIETY 20 COUNT 5.3 OUNCES EA | Costco San Francisco | $17.89 | 20 cup | $1.330/cup | $0.894/cup | -49% (Costco cheaper) | same product different size | no | quick mention | broad promo block |
| Beef chuck short ribs | CHOICE BEEF CHUCK BONELESS SHORT RIBS VAC PACK PER LB | Costco San Francisco | $12.29 | 1 lb | $7.990/lb | $12.290/lb | +35% (grocery cheaper) | same category comparable | no | manual verification | missing canonical tracker family |

## Costco mapping coverage gaps

| Item | Costco SF data exists? | Proposed mapping | Coverage gap? | Notes |
|---|---|---|---|---|
| raw shrimp | no | — (none) | yes | No raw frozen shrimp SKU in SF crawl. Prepared only (Kirkland Garlic Butter Shrimp 2 lb $15.99, Shrimp Cocktail $10.99/lb). Coverage gap for an exact raw-shrimp comparison. |
| bell peppers | no | — (none) | yes | No fresh bell peppers in SF crawl. Coverage gap (Costco 6-ct exists in stores ~$1/ea but not crawled). |
| drumsticks (Nestle ice cream) | no | — (none) | yes | No Nestle Drumstick ice cream in SF crawl; only FRESH ORGANIC CHICKEN DRUMSTICK #22501 $1.99/lb (different product). Coverage gap. |
| Doritos | yes | #933402 DORITOS NACHO CHEESE 30 OUNCES $6.99 / 30 oz bag → already mapped (canonical doritos_nacho_cheese, config/costco_item_mappings.csv) | no | DORITOS NACHO CHEESE 30 OZ — already mapped for the canonical tracker. |
| avocados | yes | #647465 AVOCADOS HASS VARIETY 6 COUNT $7.99 / 6 count → already mapped (canonical avocados) | no | AVOCADOS HASS VARIETY 6 COUNT — already mapped. |
| blackberries | yes | #791185 ORGANIC BLACKBERRIES 12 OZ $8.99 / 12 oz (organic) → config/content_costco_mappings.csv (berry_mix_6oz) | no | ORGANIC BLACKBERRIES 12 OZ — exists; add as content-mode comparable (organic vs conventional caveat). |
| raspberries | yes | #56366 RASPBERRIES 12 OZ $6.99 / 12 oz → config/content_costco_mappings.csv (new raspberries row) | no | RASPBERRIES 12 OZ — exists; conventional, good same-product comparable. |
| blueberries | yes | #57554 BLUEBERRIES 18 OZ $5.99 / 18 oz → config/content_costco_mappings.csv (new blueberries row) | no | BLUEBERRIES 18 OZ — exists; same-product comparable. |
| Chobani | yes | #1005641 CHOBANI GREEK YOGURT VARIETY 20 COUNT 5.3 OUNCES EA $17.89 / 20 ct 5.3 oz → config/content_costco_mappings.csv (chobani_yogurt) | no | CHOBANI GREEK YOGURT VARIETY 20 COUNT 5.3 OZ — exists but was unmapped; matches the Safeway single-serve 3/$4 cups (Costco is cheaper per cup). Protein 16-ct #1920008 relates to the Vons 4-ct protein deal, not Safeway. |
| beef chuck short ribs | yes | #34044 CHOICE BEEF CHUCK BONELESS SHORT RIBS VAC PACK PER LB $12.29 / per lb (Choice boneless) → config/content_costco_mappings.csv (beef_chuck_short_ribs) | no | CHOICE BEEF CHUCK BONELESS SHORT RIBS $12.29/lb — exists; Prime bone-in #12329 $7.99/lb and #12239 $10.99/lb also exist. Add as content comparable (grade/bone caveat). |
| pork shoulder ribs | yes | #33997 PORK SHOULDER COUNTRY RIBS BONELESS PER LB. $3.79 / per lb → config/content_costco_mappings.csv (pork_shoulder_ribs) | no | PORK SHOULDER COUNTRY RIBS BONELESS $3.79/lb — exists; near-exact same product. Add as content comparable. |
| Sargento / string cheese | yes | #1352319 GALBANI WHOLE MILK STRING CHEESE 60 COUNT 1 OUNCE EACH $11.49 / 60 ct 1 oz → config/content_costco_mappings.csv (sargento_cheese, category comparable) | no | GALBANI WHOLE MILK STRING CHEESE 60 COUNT $11.49 — bulk store-brand; no Sargento SKU. Bulk is cheaper per stick, so this is NOT a Costco beat. |
| Oreo regular packs | no | — (none) | yes | No regular Oreo SKU in SF crawl (only mini/assorted cookies). Coverage gap; Costco Oreo (~$3.79) known in stores but not crawled. |
| Oreo BTS / single-serve / snack packs | no | — (none) | yes | No Oreo single-serve/snack multipack SKU in SF crawl. Coverage gap. |
