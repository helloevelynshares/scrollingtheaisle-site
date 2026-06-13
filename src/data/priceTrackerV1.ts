/**
 * @deprecated Import from canonicalProducts, priceTrackerUtils, priceTrackerFallback instead.
 * Kept for scripts/docs that still reference this path.
 */
export { CANONICAL_PRODUCTS } from "./canonicalProducts";
export { buildSafewayFallbackProducts as trackedProductsFallback } from "./priceTrackerFallback";
export {
  countWeeklyAdMatches,
  formatDiscount,
  formatDiscountVsBaseline,
  formatPrice,
  formatWeekLabel,
  getAllPricePoints,
  getChartPricePoints,
  getCurrentPrice,
  getDiscountPercent,
  getLowestObservedPrice,
} from "./priceTrackerUtils";
export type { FeedProductView as TrackedProduct } from "./priceTrackerTypes";
export type { WeeklyPrice, MatchConfidence } from "./priceTrackerTypes";
export { WEEKLY_AD_WEEKS } from "./weeklyAdPrices.generated";

import { buildSafewayFallbackProducts } from "./priceTrackerFallback";

/** @deprecated Use fetchFeedProducts() with feedId safeway_bay_area */
export const trackedProducts = buildSafewayFallbackProducts();
export const TRACKED_PRODUCTS_V1 = trackedProducts;

export function getLatestWeeklyAd(product: import("./priceTrackerTypes").FeedProductView) {
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    b.weekStart.localeCompare(a.weekStart),
  );
  return sorted[0] ?? null;
}
