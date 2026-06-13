import type { FeedProductView, WeeklyPrice } from "./priceTrackerTypes";

export type PricePoint = WeeklyPrice & {
  isBaseline?: boolean;
  label?: string;
};

export function getAllPricePoints(product: FeedProductView): PricePoint[] {
  if (!product.hasFeedData || product.baselinePrice == null) {
    return [];
  }

  const baseline: PricePoint = {
    weekStart: "baseline",
    label: "Baseline",
    price: product.baselinePrice,
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
  if (!product.hasFeedData || product.baselinePrice == null) {
    return null;
  }
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );
  return sorted[sorted.length - 1]?.price ?? product.baselinePrice;
}

export function getLowestObservedPrice(product: FeedProductView): number | null {
  if (!product.hasFeedData || product.baselinePrice == null) {
    return null;
  }
  const candidates = product.weeklyPrices.map((week) => week.price);
  return Math.min(product.baselinePrice, ...candidates);
}

export function getDiscountPercent(product: FeedProductView): number | null {
  const baseline = product.baselinePrice;
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
