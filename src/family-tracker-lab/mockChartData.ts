/** Mock FeedProductView chart payloads for family lab; local only, no Supabase. */

import type { FeedProductView, WeeklyPrice } from "../data/priceTrackerTypes";

const WEEKS = [
  "2026-03-25",
  "2026-04-01",
  "2026-05-06",
  "2026-05-12",
  "2026-06-03",
  "2026-06-10",
  "2026-06-17",
  "2026-06-24",
  "2026-07-01",
] as const;

function baselineWeek(weekStart: string, price: number): WeeklyPrice {
  return {
    weekStart,
    price,
    adPrice: null,
    matchConfidence: null,
    priceType: "baseline",
    isBaselineFallback: true,
  };
}

function saleWeek(
  weekStart: string,
  price: number,
  offerText?: string,
): WeeklyPrice {
  return {
    weekStart,
    price,
    adPrice: price,
    matchConfidence: "high",
    priceType: "weekly_ad",
    offerText,
    isBaselineFallback: false,
  };
}

function buildWeeklySeries(
  baseline: number,
  sales: Partial<Record<(typeof WEEKS)[number], number>>,
  offerText?: string,
): WeeklyPrice[] {
  return WEEKS.map((weekStart) => {
    const salePrice = sales[weekStart];
    if (salePrice != null) {
      return saleWeek(weekStart, salePrice, offerText);
    }
    return baselineWeek(weekStart, baseline);
  });
}

function labChartProduct(
  familyId: string,
  displayName: string,
  baselinePrice: number,
  weeklyPrices: WeeklyPrice[],
  extra?: Partial<FeedProductView>,
): FeedProductView {
  return {
    canonicalId: familyId,
    displayName,
    productFamily: displayName,
    costcoComparable: false,
    confidence: "high",
    feedId: "safeway_bay_area",
    feedLabel: "Safeway",
    regionLabel: "Bay Area",
    hasFeedData: true,
    baselinePrice,
    baselineSource: "Mock weekly ad history",
    weeklyPrices,
    trackerType: "deal_family",
    chartMode: "single",
    ...extra,
  };
}

/** Family-level price history keyed by lab family id (lays, ritz, etc.). */
export const MOCK_CHART_PRODUCTS: Record<string, FeedProductView> = {
  lays: labChartProduct(
    "lays",
    "Lay's Chips",
    5.49,
    buildWeeklySeries(5.49, {
      "2026-03-25": 4.99,
      "2026-05-12": 2.99,
      "2026-06-24": 2.99,
      "2026-07-01": 1.99,
    }, "Lay's Potato Chips 7.75–10 oz"),
  ),
  ritz: labChartProduct(
    "ritz",
    "Ritz",
    4.99,
    buildWeeklySeries(4.99, {
      "2026-03-25": 2.5,
      "2026-05-12": 2.5,
      "2026-06-24": 2.5,
      "2026-07-01": 2.5,
    }, "Ritz Crackers 2 for $5"),
  ),
  "ben-jerrys": labChartProduct(
    "ben-jerrys",
    "Ben & Jerry's",
    6.49,
    buildWeeklySeries(6.49, {
      "2026-03-25": 3.49,
      "2026-07-01": 3.49,
    }, "Ben & Jerry's Ice Cream 16 oz"),
  ),
  "coke-12pk": labChartProduct(
    "coke-12pk",
    "Coca-Cola 12-packs",
    9.99,
    buildWeeklySeries(9.99, {
      "2026-05-12": 5.99,
      "2026-06-17": 5.99,
      "2026-07-01": 3.6,
    }, "Buy 2 get 3 free; effective ~$3.60 each when buying 5"),
  ),
};
