# Fresh Costco highlight recommendations: Safeway 2026-07-15 → 2026-07-21

_Generated 2026-07-15 · ANALYSIS ONLY (handpicked YAML / homepage not updated)._

**Costco source:** `2026-07-15_san-francisco_consolidated.csv` (imported into observations cache).  
**Tracker input:** `output/weekly_deals/2026-07-15/_ranked_deal_report.json` (Safeway vs Costco SF only).  
**Ad status:** Calendar-active week (started Wed Jul 15).

> Use this file for scripting / handpicked curation. Cherries↔grapes and raw egg unit bugs in the auto scorer are corrected below with manual unit math.

---

## Quick ranking: what to highlight (Safeway)

### Lead-worthy
1. **Cherries $2.99/lb** — ~50% under shelf baseline; strong seasonal staple. No fair fresh-cherry Costco SKU in this crawl (ignore any grapes proxy).
2. **Sweet corn 4 for $1 ($0.25/ear)** — absolute price smash; full week; no Costco fresh-ear comparable.
3. **Lucerne eggs 18-ct $1.99** (~**$1.33/dozen**) — **beats Costco SF** Kirkland 5-dozen @ $11.99 (~**$2.40/dozen**) by ~45%. Frame as dozen-normalized.
4. **Cheez-It / Ritz $2.49** (8.8–13.7 oz mix & match) — **Cheez-It is a tracked historical low** (~55% under baseline). Unit vs Costco Cheez-It 48 oz $9.99 is roughly **tied**; sell as smaller-buy + variety (not a huge Costco crush).
5. **Goldfish $2.49** (6.1–8 oz) — strong Safeway pantry deal (~38% under baseline). Costco still cheaper per oz on the 66 oz bag; frame as no-bulk / kid size.
6. **Chobani cups ~$1.00–$1.25** (clip 10/$10 or similar) — great absolute dairy deal. Costco Chobani 20-ct variety ≈ **$0.89/cup**, so Costco still wins bulk; Safeway wins for 1–few cups / flavor variety.

### Solid supporting
7. **Lucerne butter $3.99 / 16 oz** — ~33% under baseline; no clean Land O' Lakes / Lucerne 1-lb Costco row in this crawl → Safeway-only deal copy.
8. **Keebler sandwich crackers $3.00** — good absolute; no Keebler in SF crawl.
9. **Doritos Mix & Match $2.49** (5–10.75 oz, clip) — good ad price and fixed from the bad $5.99 bleed. Costco Nacho 30 oz $6.99 still ~**16% cheaper per oz**; say “solid bag deal / smaller quantity,” not “cheaper than Costco.”
10. **Tri-tip $10.99/lb** — decent meat, not a crush; medium-confidence match.

### Friday-only (badge it)
11. **Hass avocados 4 for $5 ($1.25 each)** — **barely beats Costco** 6-ct Hass @ $7.99 (**$1.33/ea**, ~6%). Worth a Friday callout; weaker than last week’s full-week 99¢.

### Skip / weak for highlights
- Eggs auto-rank “beats Costco by 99%” was a **unit bug** — use the dozen math above, not the raw scorer %.
- Cherries must **not** be scripted as beating Costco grapes.
- Strawberries large-pack remains off-tracker / ambiguous.
- Pepsi / Coke mega-tiles stay out unless verified on PDF.

---

## Costco SF winners (Safeway cheaper on a fair unit)

| Item | Safeway | Costco SF (7/15) | Verdict |
|---|---|---|---|
| **Eggs (dozen-normalized)** | $1.99 / 18-ct ≈ **$1.33/dz** | Kirkland cage-free 5 dz **$11.99** ≈ **$2.40/dz** | **Safeway wins ~45%** |
| **Hass avocados (Friday)** | **$1.25 each** | Hass 6-ct **$7.99** = **$1.33 each** | **Safeway wins ~6%** (Friday only) |
| **Cheez-It (approx oz)** | $2.49 / ~12 oz ≈ $0.208/oz | 48 oz **$9.99** ≈ $0.208/oz | **Tie** — Safeway wins on small pack / ATL story |

**Near Costco / smaller-buy only (do not claim cheaper than Costco):** Doritos, Goldfish, Ritz, Chobani cups.

**No usable Costco row this crawl:** cherries (fresh), sweet corn, Lucerne butter, Keebler, tri-tip.

### Costco price moves vs last crawl (tracked comps)

| Item | Prior SF | 2026-07-15 SF | Note |
|---|---|---|---|
| Strawberries 2 lb | $3.99 (7/12) | **$5.49** | Costco got worse — helps any grocery berry story directionally |
| Organic green grapes 3 lb | $7.99 | **$8.49** | Costco up |
| Hass avocados 6-ct | $7.99 | **$7.99** | Stable |
| Doritos Nacho 30 oz | $6.99 | **$6.99** | Stable |
| Kirkland eggs 5 dz | $11.99 | **$11.99** | Stable |
| Chobani 20-ct 5.3 oz | $17.89 | **$17.89** | Stable |

---

## All-time / historical lows (Safeway tracker history)

| Family | Ad price | Hist label | Notes |
|---|---|---|---|
| **Cheez-It crackers** | $2.49 | **Historical low** | Best pantry ATL story this week |
| Cherries | $2.99 | Strong vs median | Not ATL in scorer, but deep vs baseline |
| Sweet corn | $0.25 | Strong vs median | Absolute smash |
| Goldfish | $2.49 | Strong vs median | Solid |

(Ritz shares the same ad tile; hist bucket “Unknown” on Ritz family — still sell with Cheez-It.)

---

## Great Safeway deals without needing Costco

1. Sweet corn **4/$1**
2. Cherries **$2.99/lb**
3. Chobani cups **~$1**
4. Butter **$3.99**
5. Goldfish / Ritz / Cheez-It **$2.49**
6. Keebler **$3**

---

## Suggested handpicked order (7–8 cards)

1. Cherries $2.99/lb — PRODUCE  
2. Sweet corn 4/$1 — PRODUCE / DEAL  
3. Lucerne eggs $1.99 (18-ct) — with Costco-beat dozen framing — DEAL  
4. Cheez-It/Ritz $2.49 — SNACKS (+ ATL on Cheez-It)  
5. Goldfish $2.49 — SNACKS  
6. Chobani ~$1 — DAIRY (smaller-buy vs Costco)  
7. Butter $3.99 — DAIRY  
8. Friday avocados $1.25 — FRIDAY (optional)

---

## Vons glance (same Costco SF math for avo; Tustin for others if mapped)

Not the focus of this run’s SF crawl, but tracker still matched: **chicken breast $1.99/lb**, **avocados 99¢** (stronger Costco beat than Safeway Friday), **grapes $1.99/lb**, **Cheerios/CTC $1.29**, **salmon $8.99/lb**, **Fage 99¢**. If you want a Vons+Tustin pass next, drop a fresh Tustin consolidated file.

---

## Artifacts

- `output/weekly_deals/2026-07-15/_ranked_deal_report.json` — raw scorer  
- `scripts/_tmp_ranked_deal_report_jul15.py` — regenerator  
- Costco import: `data/processed/costco/observations.json` includes `2026-07-15_san-francisco_consolidated.csv`

_Await your curated handpicked list before touching `data/popular_this_week.yaml` / homepage._
