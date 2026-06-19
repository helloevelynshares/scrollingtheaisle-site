import type { FeedProductView, WeeklyPrice } from "./priceTrackerTypes";

export type PricePoint = WeeklyPrice & {
  isBaseline?: boolean;
  label?: string;
};

const INFERRED_BASELINE_SOURCE = "Inferred from weekly ad matches";

/** Highest non-low-confidence weekly ad price — anchor when no store baseline exists. */
export function inferBaselineFromWeeklyPrices(
  weeklyPrices: WeeklyPrice[],
): number | null {
  const adPrices = weeklyPrices
    .filter(
      (week) =>
        week.adPrice != null &&
        week.matchConfidence != null &&
        week.matchConfidence !== "low",
    )
    .map((week) => week.adPrice as number);

  return adPrices.length > 0 ? Math.max(...adPrices) : null;
}

export function getEffectiveBaseline(product: FeedProductView): number | null {
  return product.baselinePrice ?? inferBaselineFromWeeklyPrices(product.weeklyPrices);
}

export function hasChartableData(product: FeedProductView): boolean {
  if (!product.hasFeedData) {
    return false;
  }
  return getEffectiveBaseline(product) != null;
}

export function getAllPricePoints(product: FeedProductView): PricePoint[] {
  const baselinePrice = getEffectiveBaseline(product);
  if (!hasChartableData(product) || baselinePrice == null) {
    return [];
  }

  const baseline: PricePoint = {
    weekStart: "baseline",
    label: "Baseline",
    price: baselinePrice,
    adPrice: null,
    matchConfidence: null,
    priceType: "baseline",
    sourceLabel: product.baselineSource ?? undefined,
    isBaselineFallback: false,
    isBaseline: true,
  };
  const weekly = getChartPricePoints(product);
  return [baseline, ...weekly];
}

export function getChartPricePoints(product: FeedProductView): PricePoint[] {
  return product.weeklyPrices
    .map((week) => ({
      ...week,
      label: formatWeekLabel(week.weekStart),
    }))
    .sort((a, b) => a.weekStart.localeCompare(b.weekStart));
}

export function getCurrentPrice(product: FeedProductView): number | null {
  const baseline = getEffectiveBaseline(product);
  if (!hasChartableData(product) || baseline == null) {
    return null;
  }
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );
  return sorted[sorted.length - 1]?.price ?? baseline;
}

export function getLowestObservedPrice(product: FeedProductView): number | null {
  const baseline = getEffectiveBaseline(product);
  if (!hasChartableData(product) || baseline == null) {
    return null;
  }
  const candidates = product.weeklyPrices.map((week) => week.price);
  return Math.min(baseline, ...candidates);
}

export function getDiscountPercent(product: FeedProductView): number | null {
  const baseline = getEffectiveBaseline(product);
  if (!baseline || baseline <= 0) {
    return null;
  }
  const current = getCurrentPrice(product);
  if (current == null) {
    return null;
  }
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

export function formatDiscountVsBaseline(percent: number | null): string {
  if (percent == null || percent <= 0) {
    return "At baseline";
  }
  return `${percent}% off baseline`;
}

export function formatWeekLabel(weekStart: string): string {
  if (weekStart === "baseline") {
    return "Baseline";
  }
  const date = new Date(`${weekStart}T12:00:00`);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function countWeeklyAdMatches(product: FeedProductView): number {
  return product.weeklyPrices.filter((week) => !week.isBaselineFallback).length;
}

export { INFERRED_BASELINE_SOURCE };
