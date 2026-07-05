import type { FeedProductView, WeeklyPrice } from "./priceTrackerTypes";

export type BenchmarkBucket =
  | "all-time low"
  | "near all-time low"
  | "strong sale"
  | "normal sale"
  | "weak sale"
  | "insufficient history";

export type PriceBenchmarkResult = {
  allTimeLowUnitPrice: number | null;
  ninetyDayLowUnitPrice: number | null;
  medianUnitPrice: number | null;
  latestSeenUnitPrice: number | null;
  percentAboveAllTimeLow: number | null;
  percentBelowMedian: number | null;
  benchmarkBucket: BenchmarkBucket;
  observationCount: number;
};

/** Keep in sync with config/price_benchmark_thresholds.json */
export const BENCHMARK_THRESHOLDS = {
  minObservations: 2,
  allTimeLowTolerance: 1.001,
  nearAllTimeLowMultiplier: 1.05,
  strongSaleVsNinetyDayLow: 0.999,
  strongSaleVsMedian: 0.97,
  normalSaleVsMedian: 1.03,
  ninetyDayWeekFallback: 13,
} as const;

type BenchmarkSeriesPoint = {
  weekStart: string;
  price: number;
};

function median(values: number[]): number | null {
  if (values.length === 0) {
    return null;
  }
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2) {
    return sorted[mid];
  }
  return round4((sorted[mid - 1] + sorted[mid]) / 2);
}

function round4(value: number): number {
  return Math.round(value * 10_000) / 10_000;
}

function roundPct(value: number): number {
  return Math.round(value * 100) / 100;
}

export function percentAboveAllTimeLow(
  price: number | null,
  allTimeLow: number | null,
): number | null {
  if (price == null || allTimeLow == null || allTimeLow <= 0) {
    return null;
  }
  return roundPct(((price - allTimeLow) / allTimeLow) * 100);
}

export function percentBelowMedian(
  price: number | null,
  medianPrice: number | null,
): number | null {
  if (price == null || medianPrice == null || medianPrice <= 0) {
    return null;
  }
  return roundPct(((medianPrice - price) / medianPrice) * 100);
}

export function benchmarkBucketForPrice(
  price: number | null,
  stats: {
    allTimeLow: number | null;
    ninetyDayLow: number | null;
    median: number | null;
    observationCount: number;
  },
  thresholds: typeof BENCHMARK_THRESHOLDS = BENCHMARK_THRESHOLDS,
): BenchmarkBucket {
  if (price == null || stats.observationCount < thresholds.minObservations) {
    return "insufficient history";
  }

  const { allTimeLow, ninetyDayLow, median: medianPrice } = stats;
  const nearLowThreshold =
    allTimeLow != null ? allTimeLow * thresholds.nearAllTimeLowMultiplier : null;

  if (allTimeLow != null && price <= allTimeLow * thresholds.allTimeLowTolerance) {
    return "all-time low";
  }
  if (nearLowThreshold != null && price <= nearLowThreshold) {
    return "near all-time low";
  }
  if (
    ninetyDayLow != null &&
    price < ninetyDayLow * thresholds.strongSaleVsNinetyDayLow
  ) {
    return "strong sale";
  }
  if (medianPrice != null && price < medianPrice * thresholds.strongSaleVsMedian) {
    return "strong sale";
  }
  if (medianPrice != null && price <= medianPrice * thresholds.normalSaleVsMedian) {
    return "normal sale";
  }
  return "weak sale";
}

function chartableWeeklyPrices(weeklyPrices: WeeklyPrice[]): BenchmarkSeriesPoint[] {
  return weeklyPrices
    .filter(
      (week) =>
        week.matchConfidence != null &&
        week.matchConfidence !== "low" &&
        Number.isFinite(week.price),
    )
    .map((week) => ({
      weekStart: week.weekStart,
      price: week.price,
    }))
    .sort((a, b) => a.weekStart.localeCompare(b.weekStart));
}

export function computePriceBenchmarkFromSeries(
  series: BenchmarkSeriesPoint[],
  currentUnitPrice: number | null,
  options?: {
    beforeWeek?: string;
    ninetyDayCutoff?: string;
    thresholds?: typeof BENCHMARK_THRESHOLDS;
  },
): PriceBenchmarkResult {
  const thresholds = options?.thresholds ?? BENCHMARK_THRESHOLDS;
  const filtered = options?.beforeWeek
    ? series.filter((point) => point.weekStart < options.beforeWeek!)
    : series;
  const values = filtered.map((point) => point.price);

  let ninetyValues = values;
  if (options?.ninetyDayCutoff) {
    ninetyValues = filtered
      .filter((point) => point.weekStart >= options.ninetyDayCutoff!)
      .map((point) => point.price);
  } else if (values.length > thresholds.ninetyDayWeekFallback) {
    ninetyValues = values.slice(-thresholds.ninetyDayWeekFallback);
  }

  const allTimeLow = values.length > 0 ? Math.min(...values) : null;
  const ninetyDayLow = ninetyValues.length > 0 ? Math.min(...ninetyValues) : null;
  const medianPrice = median(values);
  const latestSeen = values.length > 0 ? values[values.length - 1] : null;

  const benchmarkBucket = benchmarkBucketForPrice(currentUnitPrice, {
    allTimeLow,
    ninetyDayLow,
    median: medianPrice,
    observationCount: values.length,
  }, thresholds);

  return {
    allTimeLowUnitPrice: allTimeLow,
    ninetyDayLowUnitPrice: ninetyDayLow,
    medianUnitPrice: medianPrice,
    latestSeenUnitPrice: latestSeen,
    percentAboveAllTimeLow: percentAboveAllTimeLow(currentUnitPrice, allTimeLow),
    percentBelowMedian: percentBelowMedian(currentUnitPrice, medianPrice),
    benchmarkBucket,
    observationCount: values.length,
  };
}

export function computePriceBenchmarkFromWeeklyPrices(
  weeklyPrices: WeeklyPrice[],
  currentUnitPrice: number | null,
  options?: {
    beforeWeek?: string;
    ninetyDayCutoff?: string;
  },
): PriceBenchmarkResult {
  const series = chartableWeeklyPrices(weeklyPrices);
  return computePriceBenchmarkFromSeries(series, currentUnitPrice, {
    beforeWeek: options?.beforeWeek,
    ninetyDayCutoff: options?.ninetyDayCutoff,
  });
}

/** Benchmark for a feed product card using its weekly ad price history. */
export function computeFeedProductBenchmark(
  product: FeedProductView,
  currentUnitPrice?: number | null,
): PriceBenchmarkResult {
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );
  const current =
    currentUnitPrice ??
    sorted[sorted.length - 1]?.price ??
    null;

  return computePriceBenchmarkFromWeeklyPrices(product.weeklyPrices, current);
}
