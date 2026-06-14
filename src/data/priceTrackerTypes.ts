import type { MatchConfidence } from "./weeklyAdPrices.generated";
import type { CanonicalProduct } from "./canonicalProducts";
import type { PriceComparisonView } from "./priceComparisonTypes";

export type { MatchConfidence, CanonicalProduct };

/** Weekly slot for a single feed + canonical product. */
export type WeeklyPrice = {
  weekStart: string;
  price: number;
  adPrice: number | null;
  matchConfidence: MatchConfidence | null;
  priceType: "baseline" | "weekly_ad";
  sourceLabel?: string;
  offerText?: string;
  isBaselineFallback: boolean;
};

/**
 * View model for one canonical product under an active feed.
 * feed_id determines which regional/store price data is shown.
 */
export type FeedProductView = {
  canonicalId: string;
  displayName: string;
  productFamily: string;
  sizeLabel?: string;
  costcoComparable: boolean;
  confidence: "high" | "medium" | "low";
  feedId: string;
  feedLabel: string;
  regionLabel: string;
  /** False when this feed has no baseline/match yet (e.g. Vons coming soon). */
  hasFeedData: boolean;
  baselinePrice: number | null;
  baselineSource: string | null;
  weeklyPrices: WeeklyPrice[];
  /** Grocery vs Costco per-unit comparison for this feed, when available. */
  priceComparison?: PriceComparisonView | null;
};

/** feed_product_matches row — maps canonical item to a retailer SKU for price fetching. */
export type FeedProductMatch = {
  canonicalProductId: string;
  feedId: string;
  retailerProductId: string | null;
  upc: string | null;
  retailerProductName: string | null;
  size: string | null;
  baselinePrice: number;
  baselineSource: string | null;
};

/** weekly_price_observations row — one week of prices for canonical + feed. */
export type WeeklyPriceObservation = {
  canonicalProductId: string;
  feedId: string;
  weekStart: string;
  weekEnd: string | null;
  adPrice: number | null;
  effectivePrice: number;
  matchConfidence: MatchConfidence | null;
  priceType: "baseline" | "weekly_ad";
  isBaselineFallback: boolean;
  sourceLabel: string | null;
  offerText: string | null;
};
