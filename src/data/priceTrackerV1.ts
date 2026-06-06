import {
  WEEKLY_AD_PRICES,
  WEEKLY_AD_WEEKS,
  type GeneratedWeeklyAdPrice,
} from "./weeklyAdPrices.generated";

export type MatchConfidence = "high" | "medium" | "low";

export type WeeklyPrice = {
  weekStart: string; // YYYY-MM-DD
  price: number;
  adPrice: number | null;
  matchConfidence: MatchConfidence | null;
  priceType: "baseline" | "weekly_ad";
  sourceUrl?: string;
  sourceLabel?: string;
  offerText?: string;
  isBaselineFallback: boolean;
};

export type AcceptedProduct = {
  retailerProductId: string;
  upc?: string;
  productName: string;
  size?: string;
};

export type TrackedProduct = {
  canonicalId: string;
  displayName: string;
  productFamily: string;
  retailer: "Safeway";
  storeName: string;
  region: "Bay Area";
  confidence: "high" | "medium" | "low";
  costcoComparable: boolean;
  baselinePrice: number;
  baselineSource: string;
  acceptedProduct: AcceptedProduct;
  weeklyPrices: WeeklyPrice[];
};

export type PricePoint = WeeklyPrice & {
  isBaseline?: boolean;
  label?: string;
};

function effectiveWeeklyPrice(
  baselinePrice: number,
  entry: GeneratedWeeklyAdPrice | undefined,
): Pick<
  WeeklyPrice,
  "price" | "adPrice" | "matchConfidence" | "priceType" | "offerText" | "isBaselineFallback"
> {
  const adPrice = entry?.price ?? null;
  const matchConfidence = entry?.confidence ?? null;
  const useAd = matchConfidence === "high" && adPrice != null;

  return {
    price: useAd ? adPrice : baselinePrice,
    adPrice,
    matchConfidence,
    priceType: useAd ? "weekly_ad" : "baseline",
    offerText: entry?.offerText ?? undefined,
    isBaselineFallback: !useAd,
  };
}

function weeklyAdPricesFor(
  canonicalId: string,
  baselinePrice: number,
): WeeklyPrice[] {
  const byWeek = WEEKLY_AD_PRICES[canonicalId] ?? {};

  return WEEKLY_AD_WEEKS.map((week) => {
    const entry = byWeek[week.weekStart];
    const effective = effectiveWeeklyPrice(baselinePrice, entry);

    return {
      weekStart: week.weekStart,
      ...effective,
      sourceLabel: `${week.sourceLabel} · ${week.sourceFile}`,
    };
  });
}

/** Tracked products — baseline/PIDs here; weekly ad prices come from generated data. */
export const trackedProducts: TrackedProduct[] = [
  {
    canonicalId: "strawberries",
    displayName: "Strawberries",
    productFamily: "strawberries",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 4.99,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Strawberries 1 lb",
      size: "1 lb",
    },
    weeklyPrices: weeklyAdPricesFor("strawberries", 4.99),
  },
  {
    canonicalId: "avocados",
    displayName: "Hass Avocados",
    productFamily: "avocados",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 2.0,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Medium Hass Avocado",
      size: "Each",
    },
    weeklyPrices: weeklyAdPricesFor("avocados", 2.0),
  },
  {
    canonicalId: "doritos_nacho_cheese",
    displayName: "Doritos Nacho Cheese",
    productFamily: "doritos_nacho_cheese",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 5.49,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Doritos Nacho Cheese Tortilla Chips",
      size: "9.25 oz",
    },
    weeklyPrices: weeklyAdPricesFor("doritos_nacho_cheese", 5.49),
  },
  {
    canonicalId: "cheetos_crunchy",
    displayName: "Cheetos Crunchy",
    productFamily: "cheetos_crunchy",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 5.49,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Cheetos Cheese Flavored Crunchy Snacks",
      size: "8.5 oz",
    },
    weeklyPrices: weeklyAdPricesFor("cheetos_crunchy", 5.49),
  },
  {
    canonicalId: "coke_zero",
    displayName: "Coke Zero",
    productFamily: "coke_zero",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 12.99,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Coca-Cola Zero Sugar Soda",
      size: "12 pack / 12 fl oz",
    },
    weeklyPrices: weeklyAdPricesFor("coke_zero", 12.99),
  },
  {
    canonicalId: "chobani_greek_yogurt",
    displayName: "Chobani Greek Yogurt",
    productFamily: "chobani_greek_yogurt",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 7.99,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Chobani Non-Fat Plain Greek Yogurt",
      size: "32 oz",
    },
    weeklyPrices: weeklyAdPricesFor("chobani_greek_yogurt", 7.99),
  },
  {
    canonicalId: "cheerios",
    displayName: "Cheerios",
    productFamily: "cheerios",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 6.99,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Cheerios Whole Grain Oat Toasted Cereal",
      size: "8.9 oz",
    },
    weeklyPrices: weeklyAdPricesFor("cheerios", 6.99),
  },
  {
    canonicalId: "tillamook_ice_cream",
    displayName: "Tillamook Ice Cream",
    productFamily: "tillamook_ice_cream",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 6.99,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Tillamook Oregon Strawberry Ice Cream",
      size: "1.75 qt",
    },
    weeklyPrices: weeklyAdPricesFor("tillamook_ice_cream", 6.99),
  },
  {
    canonicalId: "mission_tortilla_chips",
    displayName: "Mission Tortilla Chips",
    productFamily: "mission_tortilla_chips",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 4.49,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Mission Round Yellow Corn Tortilla Chips",
      size: "11 oz",
    },
    weeklyPrices: weeklyAdPricesFor("mission_tortilla_chips", 4.49),
  },
  {
    canonicalId: "nature_valley_bars",
    displayName: "Nature Valley Bars",
    productFamily: "nature_valley_bars",
    retailer: "Safeway",
    storeName: "Safeway Bay Area",
    region: "Bay Area",
    confidence: "high",
    costcoComparable: true,
    baselinePrice: 4.99,
    baselineSource: "Safeway search result CSV",
    acceptedProduct: {
      retailerProductId: "TODO_PID",
      upc: "TODO_UPC",
      productName: "Nature Valley Crunchy Oats 'n Honey Granola Bars",
      size: "12 ct",
    },
    weeklyPrices: weeklyAdPricesFor("nature_valley_bars", 4.99),
  },
];

/** @deprecated Use trackedProducts */
export const TRACKED_PRODUCTS_V1 = trackedProducts;

export function getAllPricePoints(product: TrackedProduct): PricePoint[] {
  const baseline: PricePoint = {
    weekStart: "baseline",
    label: "Baseline",
    price: product.baselinePrice,
    adPrice: null,
    matchConfidence: null,
    priceType: "baseline",
    sourceLabel: product.baselineSource,
    isBaselineFallback: false,
    isBaseline: true,
  };
  const weekly = getChartPricePoints(product);
  return [baseline, ...weekly];
}

/** Chart series: baseline anchor + every weekly ad slot (ad price or baseline fallback). */
export function getChartPricePoints(product: TrackedProduct): PricePoint[] {
  return product.weeklyPrices
    .map((week) => ({
      ...week,
      label: formatWeekLabel(week.weekStart),
    }))
    .sort((a, b) => a.weekStart.localeCompare(b.weekStart));
}

export function getCurrentPrice(product: TrackedProduct): number {
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );
  return sorted[sorted.length - 1]?.price ?? product.baselinePrice;
}

export function getLowestObservedPrice(product: TrackedProduct): number {
  const candidates = product.weeklyPrices.map((week) => week.price);
  return Math.min(product.baselinePrice, ...candidates);
}

export function getDiscountPercent(product: TrackedProduct): number | null {
  const baseline = product.baselinePrice;
  if (!baseline || baseline <= 0) {
    return null;
  }
  const current = getCurrentPrice(product);
  const pct = Math.round(((baseline - current) / baseline) * 100);
  return pct > 0 ? pct : 0;
}

export function formatPrice(price: number | null | undefined): string {
  if (price == null || Number.isNaN(price)) {
    return "—";
  }
  return `$${price.toFixed(2)}`;
}

export function formatDiscount(percent: number | null): string {
  if (percent == null || percent <= 0) {
    return "At baseline";
  }
  return `${percent}% off`;
}

export function formatWeekLabel(weekStart: string): string {
  if (weekStart === "baseline") {
    return "Baseline";
  }
  const date = new Date(`${weekStart}T12:00:00`);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function getLatestWeeklyAd(product: TrackedProduct): WeeklyPrice | null {
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    b.weekStart.localeCompare(a.weekStart),
  );
  return sorted[0] ?? null;
}

export function countWeeklyAdMatches(product: TrackedProduct): number {
  return product.weeklyPrices.filter((week) => !week.isBaselineFallback).length;
}

export { WEEKLY_AD_WEEKS };
