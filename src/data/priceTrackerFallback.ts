import { CANONICAL_PRODUCTS } from "./canonicalProducts";
import { getPriceFeed } from "./priceFeeds";
import type { FeedProductView, WeeklyPrice } from "./priceTrackerTypes";
import {
  WEEKLY_AD_PRICES,
  WEEKLY_AD_WEEKS,
  type GeneratedWeeklyAdPrice,
} from "./weeklyAdPrices.generated";
import {
  VONS_WEEKLY_AD_PRICES,
  VONS_WEEKLY_AD_WEEKS,
} from "./vonsWeeklyAdPrices.generated";

import { VONS_BASELINE_BY_CANONICAL } from "./vonsBaseline.generated";
import { getFallbackComparison, getCostcoPriceHistory } from "./priceComparisonUtils";
import { appendFamiliesToFeedProducts } from "./trackerFamilyUtils";
import {
  INFERRED_BASELINE_SOURCE,
  inferBaselineFromWeeklyPrices,
} from "./priceTrackerUtils";

const SAFEWAY_FEED_ID = "safeway_bay_area";
const VONS_FEED_ID = "vons_albertsons_socal";

/** Safeway baselines keyed by canonical / family id; used when Supabase is unavailable. */
export const SAFEWAY_BASELINES: Record<
  string,
  { price: number; source: string; retailerProductName: string }
> = {
  "ben_jerrys_ice_cream": {
    price: 6.99,
    source: "Safeway search result CSV",
    retailerProductName: "HERSHEY'S Sliced Strawberries Covered in Milk Chocolate - 8 Oz",
  },
  "berries_6oz": {
    price: 4.99,
    source: "Safeway search result CSV",
    retailerProductName: "Blueberries Prepacked - 6 Oz",
  },
  "breyers_ice_cream": {
    price: 7.99,
    source: "Safeway search result CSV",
    retailerProductName: "Protein Pints High Protein Salted Caramel Ice Cream - 16 Oz",
  },
  "butter_16oz": {
    price: 5.99,
    source: "Safeway search result CSV",
    retailerProductName: "Lucerne Unsalted Sweet Cream Butter Quarters - 16 Oz",
  },
  "cheetos_party_size": {
    price: 5.99,
    source: "Safeway search result CSV",
    retailerProductName: "CHEETOS Snacks Cheese Flavored Crunchy Party Size - 15 Oz",
  },
  "cheez_it_crackers": {
    price: 5.49,
    source: "Safeway search result CSV",
    retailerProductName: "Cheez-It DUOZ Baked Snack Crackers Sharp Cheddar and Parmesan Lunch Snacks - 12.4 Oz",
  },
  "cherries_per_lb": {
    price: 5.99,
    source: "Safeway search result CSV",
    retailerProductName: "Red Cherries - 1.75 Lb",
  },
  "chicken_breast_per_lb": {
    price: 8.99,
    source: "Safeway search result CSV",
    retailerProductName: "Foster Farms Free Range Boneless Skinless Chicken Breast Fillets - 2.25 Lb",
  },
  "chicken_thigh_per_lb": {
    price: 2.99,
    source: "Safeway search result CSV",
    retailerProductName: "Signature Select Chicken Thigh Boneless Skinless Value Pack - 3 lb",
  },
  "chips_ahoy": {
    price: 5.99,
    source: "Safeway search result CSV",
    retailerProductName: "Chips Ahoy! Original Chocolate Chip Cookies - 13 Oz",
  },
  "clif_bars": {
    price: 7.99,
    source: "Safeway search result CSV",
    retailerProductName: "CLIF BAR White Chocolate Macadamia Nut Energy Protein Bars - 5 Count",
  },
  "dr_pepper_12packs": {
    price: 14.43,
    source: "Safeway search result CSV",
    retailerProductName: "Dr Pepper Soda Fridge Pack - 12-12 Fl. Oz.",
  },
  "dreyers_novelties": {
    price: 5.99,
    source: "Safeway search result CSV",
    retailerProductName: "Haagen-Dazs Ice Cream Bars Coffee Toffee Almond Crunch Ice Cream - 3-3 Fl. Oz.",
  },
  "dreyers_tubs": {
    price: 6.99,
    source: "Safeway search result CSV",
    retailerProductName: "Breyers Classics Natural Vanilla Ice Cream - 48 Oz",
  },
  "fage_cups": {
    price: 1.99,
    source: "Safeway search result CSV",
    retailerProductName: "Fage Total 2% Yogurt Greek Lowfat Strained with Strawberry - 5.3 Oz",
  },
  "general_mills_cereal_family_size": {
    price: 6.99,
    source: "Safeway search result CSV",
    retailerProductName: "Cheerios Whole Grain Oats Cereal Family Size - 18 Oz",
  },
  "goldfish_bags": {
    price: 3.99,
    source: "Safeway search result CSV",
    retailerProductName: "Goldfish Baby Cheddar Baked Snack Crackers - 7.2 Oz",
  },
  "haagen_dazs_bars_novelties": {
    price: 5.99,
    source: "Safeway search result CSV",
    retailerProductName: "Haagen-Dazs Dark Chocolate Ice Cream Snack Bars Ice Cream - 3 Count",
  },
  "keebler_sandwich_crackers": {
    price: 4.99,
    source: "Safeway search result CSV",
    retailerProductName: "Keebler Sandwich Crackers Cheese and Peanut Butter Single Serve Snack Crackers 8 Count - 11 Oz",
  },
  "kings_hawaiian_rolls": {
    price: 4.99,
    source: "Safeway search result CSV",
    retailerProductName: "King's Hawaiian Original Sweet Rolls - 12 Oz",
  },
  "lacroix_8pack": {
    price: 4.5,
    source: "Safeway search result CSV",
    retailerProductName: "LaCroix Pure Sparkling Water - 8-12 Fl. Oz.",
  },
  "lays_kettle_cooked": {
    price: 4.29,
    source: "Safeway search result CSV",
    retailerProductName: "Lays Potato Chips Kettle Cooked Original - 8 Oz",
  },
  "lays_potato_chips_regular": {
    price: 4.29,
    source: "Safeway search result CSV",
    retailerProductName: "Lays Potato Chips Classic - 8 Oz",
  },
  "lucerne_cream_cheese": {
    price: 3.99,
    source: "Safeway search result CSV",
    retailerProductName: "Lucerne Cream Cheese - 8 Oz",
  },
  "lucerne_yogurt_tubs": {
    price: 2.69,
    source: "Safeway search result CSV",
    retailerProductName: "Lucerne Yogurt Lowfat Strawberry Flavored - 32 Oz",
  },
  "mangoes_each": {
    price: 1.25,
    source: "Safeway search result CSV",
    retailerProductName: "Large Mango",
  },
  "nabisco_snack_crackers": {
    price: 5.49,
    source: "Safeway search result CSV",
    retailerProductName: "Wheat Thins Snacks Big 100% Whole Grain - 8 Oz",
  },
  "nectarines_per_lb": {
    price: 1.2,
    source: "Safeway search result CSV",
    retailerProductName: "Yellow Nectarine",
  },
  "peaches_per_lb": {
    price: 1.5,
    source: "Safeway search result CSV",
    retailerProductName: "Yellow Peach",
  },
  "pepsi_12packs": {
    price: 14.43,
    source: "Safeway search result CSV",
    retailerProductName: "Pepsi Soda Pop Cola - 12-12 Oz",
  },
  "philadelphia_cream_cheese": {
    price: 3.99,
    source: "Safeway search result CSV",
    retailerProductName: "Philadelphia Original Cream Cheese - 8 Oz",
  },
  "pillsbury_refrigerated_dough": {
    price: 4.99,
    source: "Safeway search result CSV",
    retailerProductName: "Pillsbury Grands! Biscuits Flaky Layers Buttermilk 8 Count - 16.3 Oz",
  },
  "plums_per_lb": {
    price: 0.85,
    source: "Safeway search result CSV",
    retailerProductName: "Organic Red Plum",
  },
  "post_cereal_giant_size": {
    price: 4.49,
    source: "Safeway search result CSV",
    retailerProductName: "Signature SELECT Cereal Shredded Wheat Bite-Sized - 16.4 Oz",
  },
  "post_cereal_regular": {
    price: 6.99,
    source: "Safeway search result CSV",
    retailerProductName: "Nature Valley Protein Granola Oats N Honey - 11 Oz",
  },
  "ribeye_steak": {
    price: 12.99,
    source: "Safeway search result CSV",
    retailerProductName: "USDA Choice Bone In Beef Rib Steak Mega Pack - 3.5 Lb",
  },
  "ritz_crackers": {
    price: 5.99,
    source: "Safeway search result CSV",
    retailerProductName: "RITZ Fresh Stacks Original Crackers - 8-11.8 Oz",
  },
  "ritz_toasted_chips": {
    price: 4.99,
    source: "Safeway search result CSV",
    retailerProductName: "RITZ Toasted Chips Original Crackers - 8.1 Oz",
  },
  "ruffles_regular_bags": {
    price: 5.49,
    source: "Safeway search result CSV",
    retailerProductName: "Ruffles Potato Chips Original - 8.5 OZ",
  },
  "salmon": {
    price: 9.29,
    source: "Safeway search result CSV",
    retailerProductName: "Atlantic Salmon Skin On Fillet 1 Count - 7 Oz Each",
  },
  "simply_party_size": {
    price: 3.99,
    source: "Safeway search result CSV",
    retailerProductName: "Lucerne Milk - Half Gallon (container may vary)",
  },
  "simply_refrigerated_juice_lemonade": {
    price: 3.0,
    source: "Safeway search result CSV",
    retailerProductName: "Minute Maid Zero Sugar Lemonade Juice - 52 Fl. Oz. Bottle",
  },
  "simply_snacks": {
    price: 5.49,
    source: "Safeway search result CSV",
    retailerProductName: "CHEETOS Snacks Cheese Flavored Crunchy XXTRA Flamin Hot - 8.5 Oz",
  },
  "sliced_or_shredded_cheese_6_8oz": {
    price: 4.49,
    source: "Safeway search result CSV",
    retailerProductName: "Lucerne Cheese Finely Shredded Mexican Style 4 Cheese Blend - 8 Oz",
  },
  "sun_chips_7oz": {
    price: 4.79,
    source: "Safeway search result CSV",
    retailerProductName: "SunChips Snacks Whole Grain Original - 7 Oz",
  },
  "sweet_corn": {
    price: 0.13,
    source: "Safeway search result CSV",
    retailerProductName: "Sweet Corn",
  },
  "thomas_bagels_muffins_bread": {
    price: 2.99,
    source: "Safeway search result CSV",
    retailerProductName: "Thomas Plain Bagels 6 Count - 18 OZ",
  },
  "tri_tip_roast": {
    price: 18.99,
    source: "Safeway search result CSV",
    retailerProductName: "USDA Choice Beef Loin Tri Tip Roast - 2.5 Lb",
  },
  strawberries: {
    price: 4.99,
    source: "Safeway search result CSV",
    retailerProductName: "Strawberries 1 lb",
  },
  avocados: {
    price: 2.0,
    source: "Safeway search result CSV",
    retailerProductName: "Medium Hass Avocado",
  },
  doritos_nacho_cheese: {
    price: 5.49,
    source: "Safeway search result CSV",
    retailerProductName: "Doritos Nacho Cheese Tortilla Chips",
  },
  cheetos_crunchy: {
    price: 5.49,
    source: "Safeway search result CSV",
    retailerProductName: "Cheetos Cheese Flavored Crunchy Snacks",
  },
  coke_zero: {
    price: 12.99,
    source: "Safeway search result CSV",
    retailerProductName: "Coca-Cola Zero Sugar Soda",
  },
  chobani_greek_yogurt: {
    price: 7.99,
    source: "Safeway search result CSV",
    retailerProductName: "Chobani Non-Fat Plain Greek Yogurt",
  },
  cheerios: {
    price: 6.99,
    source: "Safeway search result CSV",
    retailerProductName: "Cheerios Whole Grain Oat Toasted Cereal",
  },
  tillamook_ice_cream: {
    price: 6.99,
    source: "Safeway search result CSV",
    retailerProductName: "Tillamook Oregon Strawberry Ice Cream",
  },
  mission_tortilla_chips: {
    price: 4.49,
    source: "Safeway search result CSV",
    retailerProductName: "Mission Round Yellow Corn Tortilla Chips",
  },
  nature_valley_bars: {
    price: 4.99,
    source: "Safeway search result CSV",
    retailerProductName: "Nature Valley Crunchy Oats 'n Honey Granola Bars",
  },
  "eggs_18_count": {
    price: 3.99,
    source: "Safeway search result CSV (Lucerne 12-count shelf)",
    retailerProductName: "Lucerne Farms Eggs Large Cage Free - 12 Count",
  },
  "fage_greek_yogurt": {
    price: 6.99,
    source: "Safeway search result CSV",
    retailerProductName: "FAGE Total 0% Milkfat Plain Greek Yogurt - 32 Oz",
  },
  "frito_lay_multipack_chips": {
    price: 11.99,
    source: "Safeway search result CSV",
    retailerProductName: "Frito Lay Classic Mix Variety Pack - 18 Count",
  },
  "grapes": {
    price: 4.99,
    source: "Safeway search result CSV",
    retailerProductName: "Green Seedless Grapes Prepacked Bag - 2 Lb",
  },
  "haagen_dazs_ice_cream": {
    price: 7.99,
    source: "Safeway search result CSV",
    retailerProductName: "Protein Pints High Protein Salted Caramel Ice Cream - 16 Oz",
  },
  "kettle_brand_chips": {
    price: 3.99,
    source: "Safeway search result CSV",
    retailerProductName: "Kettle Brand Sea Salt Kettle Potato Chip - 7.5 Oz",
  },
  "oreos_sandwich_cookies": {
    price: 6.99,
    source: "Safeway search result CSV",
    retailerProductName: "Nabisco Chips Ahoy/Nutter Butter/OREO Variety Pack - 10 Count",
  },
  "protein_bars": {
    price: 3.99,
    source: "Safeway search result CSV",
    retailerProductName: "Signature SELECT Chewy Bars Protein Peanut Butter Dark Chocolate Flavored - 5-1.4 Oz",
  },
};

function effectiveWeeklyPrice(
  baselinePrice: number | null,
  entry: GeneratedWeeklyAdPrice | undefined,
  sourceLabel: string,
): WeeklyPrice & { weekStart: string } {
  const adPrice = entry?.price ?? null;
  const matchConfidence = entry?.confidence ?? null;
  const useAd =
    adPrice != null && matchConfidence != null && matchConfidence !== "low";

  const fallbackPrice = baselinePrice ?? adPrice ?? 0;

  return {
    weekStart: "",
    price: useAd ? adPrice : fallbackPrice,
    adPrice,
    matchConfidence,
    priceType: useAd ? "weekly_ad" : "baseline",
    offerText: entry?.offerText ?? undefined,
    isBaselineFallback: !useAd,
    sourceLabel,
    availabilityType: entry?.availabilityType ?? undefined,
    promoNote: entry?.promoNote ?? undefined,
  };
}

/** Static Safeway feed built from generated weekly ad files (offline fallback). */
export function buildSafewayFallbackProducts(): FeedProductView[] {
  const feed = getPriceFeed(SAFEWAY_FEED_ID)!;

  const products = CANONICAL_PRODUCTS.map((canonical) => {
    const baseline = SAFEWAY_BASELINES[canonical.id];
    const byWeek = WEEKLY_AD_PRICES[canonical.id] ?? {};

    const weeklyPrices: WeeklyPrice[] = WEEKLY_AD_WEEKS.map((week) => {
      const entry = byWeek[week.weekStart];
      const slot = effectiveWeeklyPrice(
        baseline?.price ?? null,
        entry,
        `${week.sourceLabel} · ${week.sourceFile}`,
      );
      return { ...slot, weekStart: week.weekStart };
    });

    const hasAdMatches = weeklyPrices.some(
      (w) => w.adPrice != null && w.matchConfidence !== "low",
    );
    const inferredBaseline = inferBaselineFromWeeklyPrices(weeklyPrices);
    const effectiveBaseline = baseline?.price ?? inferredBaseline;

    if (effectiveBaseline != null && baseline == null) {
      for (const week of weeklyPrices) {
        if (week.isBaselineFallback) {
          week.price = effectiveBaseline;
        }
      }
    }

    return {
      canonicalId: canonical.id,
      displayName: canonical.displayName,
      productFamily: canonical.productFamily,
      sizeLabel: canonical.sizeLabel,
      costcoComparable: canonical.costcoComparable,
      confidence: canonical.confidence,
      feedId: feed.id,
      feedLabel: feed.label,
      regionLabel: feed.regionLabel,
      hasFeedData: Boolean(baseline) || hasAdMatches,
      baselinePrice: effectiveBaseline,
      baselineSource:
        baseline?.source ??
        (inferredBaseline != null ? INFERRED_BASELINE_SOURCE : null),
      weeklyPrices,
      priceComparison: getFallbackComparison(canonical.id, feed.id),
      costcoPriceHistory: getCostcoPriceHistory(canonical.id, feed.id),
    };
  });

  return appendFamiliesToFeedProducts(products, SAFEWAY_FEED_ID);
}

export function buildVonsFallbackProducts(): FeedProductView[] {
  const feed = getPriceFeed(VONS_FEED_ID)!;
  const hasBaselines = Object.keys(VONS_BASELINE_BY_CANONICAL).length > 0;
  const hasWeeklyAds = VONS_WEEKLY_AD_WEEKS.length > 0;

  if (!hasBaselines && !hasWeeklyAds) {
    return appendFamiliesToFeedProducts(
      buildEmptyFeedProducts(VONS_FEED_ID),
      VONS_FEED_ID,
    );
  }

  const products = CANONICAL_PRODUCTS.map((canonical) => {
    const match = VONS_BASELINE_BY_CANONICAL[canonical.id];
    const baselinePrice = match?.baselinePrice ?? null;
    const byWeek = VONS_WEEKLY_AD_PRICES[canonical.id] ?? {};

    const weeklyPrices: WeeklyPrice[] = hasWeeklyAds
      ? VONS_WEEKLY_AD_WEEKS.map((week) => {
          const entry = byWeek[week.weekStart];
          const slot = effectiveWeeklyPrice(
            baselinePrice,
            entry,
            `${week.sourceLabel} · ${week.sourceFile}`,
          );
          return { ...slot, weekStart: week.weekStart };
        })
      : [];

    const hasAdMatches = weeklyPrices.some(
      (w) => w.adPrice != null && w.matchConfidence !== "low",
    );

    return {
      canonicalId: canonical.id,
      displayName: canonical.displayName,
      productFamily: canonical.productFamily,
      sizeLabel: canonical.sizeLabel,
      costcoComparable: canonical.costcoComparable,
      confidence: canonical.confidence,
      feedId: feed.id,
      feedLabel: feed.label,
      regionLabel: feed.regionLabel,
      hasFeedData: (match != null && baselinePrice != null) || hasAdMatches,
      baselinePrice,
      baselineSource: match?.baselineSource ?? null,
      weeklyPrices,
      priceComparison: getFallbackComparison(canonical.id, feed.id),
      costcoPriceHistory: getCostcoPriceHistory(canonical.id, feed.id),
    };
  });

  return appendFamiliesToFeedProducts(products, VONS_FEED_ID);
}

export function buildEmptyFeedProducts(feedId: string): FeedProductView[] {
  const feed = getPriceFeed(feedId);
  if (!feed) {
    return [];
  }

  return CANONICAL_PRODUCTS.map((canonical) => ({
    canonicalId: canonical.id,
    displayName: canonical.displayName,
    productFamily: canonical.productFamily,
    sizeLabel: canonical.sizeLabel,
    costcoComparable: canonical.costcoComparable,
    confidence: canonical.confidence,
    feedId: feed.id,
    feedLabel: feed.label,
    regionLabel: feed.regionLabel,
    hasFeedData: false,
    baselinePrice: null,
    baselineSource: null,
    weeklyPrices: [],
  }));
}
