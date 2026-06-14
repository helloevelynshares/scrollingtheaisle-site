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
import { getFallbackComparison } from "./priceComparisonUtils";

const SAFEWAY_FEED_ID = "safeway_bay_area";
const VONS_FEED_ID = "vons_albertsons_socal";

/** Safeway baselines keyed by canonical id — used when Supabase is unavailable. */
const SAFEWAY_BASELINES: Record<
  string,
  { price: number; source: string; retailerProductName: string }
> = {
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
  };
}

/** Static Safeway feed built from generated weekly ad files (offline fallback). */
export function buildSafewayFallbackProducts(): FeedProductView[] {
  const feed = getPriceFeed(SAFEWAY_FEED_ID)!;

  return CANONICAL_PRODUCTS.map((canonical) => {
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
      baselinePrice: baseline?.price ?? null,
      baselineSource: baseline?.source ?? null,
      weeklyPrices,
      priceComparison: getFallbackComparison(canonical.id, feed.id),
    };
  });
}

export function buildVonsFallbackProducts(): FeedProductView[] {
  const feed = getPriceFeed(VONS_FEED_ID)!;
  const hasBaselines = Object.keys(VONS_BASELINE_BY_CANONICAL).length > 0;
  const hasWeeklyAds = VONS_WEEKLY_AD_WEEKS.length > 0;

  if (!hasBaselines && !hasWeeklyAds) {
    return buildEmptyFeedProducts(VONS_FEED_ID);
  }

  return CANONICAL_PRODUCTS.map((canonical) => {
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
    };
  });
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
