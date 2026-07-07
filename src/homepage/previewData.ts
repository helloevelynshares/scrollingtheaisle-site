import {
  POPULAR_THIS_WEEK,
  POPULAR_THIS_WEEK_WEEK,
  type PopularThisWeekEntry,
  type PopularThisWeekStore,
} from "../data/canonicalTrackerFamilies";
import { computeFeedProductBenchmark } from "../data/priceBenchmarks";
import {
  formatComparisonUnit,
} from "../data/priceComparisonUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import {
  formatPrice,
  getCurrentPrice,
  getDiscountPercent,
  hasChartableData,
  isProductOnSale,
} from "../data/priceTrackerUtils";
import {
  buildSafewayYamlProducts,
  buildVonsYamlProducts,
} from "../data/yamlFamilyProducts";
import { WEEKLY_AD_WEEKS } from "../data/weeklyAdPrices.generated";

export type HomepageBadge =
  | "Stock up"
  | "Good small-pack buy"
  | "Costco still wins"
  | "Wait"
  | "Lowest seen recently"
  | "Beats Costco"
  | "About normal";

export type PopularPick = {
  id: string;
  name: string;
  store: string;
  price: string;
  unitPrice: string;
  badge: HomepageBadge;
  explanation: string;
  trackerUrl: string;
  isPlaceholder: boolean;
  onSale: boolean;
};

export type HomepagePreview = {
  generatedAt: string;
  popularWeekLabel: string;
  popularPicksSafeway: PopularPick[];
  popularPicksVons: PopularPick[];
};

const TRACKER_BASE = "staging-price-tracker/";

function latestWeekLabel(): string {
  const latest = WEEKLY_AD_WEEKS[WEEKLY_AD_WEEKS.length - 1];
  if (!latest) {
    return "This week";
  }
  return formatWeekRange(latest.weekStart, latest.weekEnd);
}

function formatWeekRange(weekStart: string, weekEnd?: string): string {
  const start = new Date(`${weekStart}T12:00:00`);
  if (!weekEnd) {
    return start.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
  const end = new Date(`${weekEnd}T12:00:00`);
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${fmt(start)}–${fmt(end)}`;
}

function popularWeekLabel(): string {
  if (!POPULAR_THIS_WEEK_WEEK) {
    return latestWeekLabel();
  }
  const week = WEEKLY_AD_WEEKS.find(
    (entry) => entry.weekStart === POPULAR_THIS_WEEK_WEEK,
  );
  if (week) {
    return formatWeekRange(week.weekStart, week.weekEnd);
  }
  return formatWeekRange(POPULAR_THIS_WEEK_WEEK);
}

function unitPriceDisplay(product: FeedProductView): string {
  const comparison = product.priceComparison;
  if (comparison?.groceryUnitPrice != null) {
    const unit = formatComparisonUnit(
      comparison.groceryUnitType ?? comparison.costcoUnitType,
    );
    return `$${comparison.groceryUnitPrice.toFixed(2)}/${unit}`;
  }

  const price = getCurrentPrice(product);
  if (price != null && product.sizeLabel) {
    return `${formatPrice(price)} · ${product.sizeLabel}`;
  }

  return price != null ? formatPrice(price) : "—";
}

function getBadge(product: FeedProductView): HomepageBadge {
  const benchmark = computeFeedProductBenchmark(product);
  const discount = getDiscountPercent(product) ?? 0;
  const comparison = product.priceComparison;

  if (
    comparison?.winner === "costco" &&
    comparison.comparisonStatus === "comparable"
  ) {
    return "Costco still wins";
  }

  if (
    benchmark.benchmarkBucket === "all-time low" ||
    benchmark.benchmarkBucket === "near all-time low"
  ) {
    return "Lowest seen recently";
  }

  if (
    benchmark.benchmarkBucket === "strong sale" ||
    discount >= 15
  ) {
    return "Stock up";
  }

  if (
    comparison?.winner === "grocery" &&
    comparison.comparisonStatus === "comparable"
  ) {
    return "Beats Costco";
  }

  if (
    benchmark.benchmarkBucket === "normal sale" ||
    (discount >= 5 && discount < 15)
  ) {
    return "Good small-pack buy";
  }

  if (benchmark.benchmarkBucket === "weak sale" || discount > 0) {
    return "About normal";
  }

  return "Wait";
}

function toPopularPick(
  entry: PopularThisWeekEntry,
  product: FeedProductView | undefined,
  storeLabel: string,
): PopularPick {
  const primaryId = entry.trackerFamilyIds[0] ?? entry.title;
  const onSale = product ? isProductOnSale(product) : false;
  const current = product ? getCurrentPrice(product) : null;

  return {
    id: primaryId,
    name: entry.title,
    store: storeLabel,
    price: current != null ? formatPrice(current) : "—",
    unitPrice: product ? unitPriceDisplay(product) : "—",
    badge: product ? getBadge(product) : onSale ? "Stock up" : "About normal",
    explanation: entry.reason,
    trackerUrl: TRACKER_BASE,
    isPlaceholder: !product || !hasChartableData(product),
    onSale,
  };
}

function buildPopularPicksForStore(
  store: PopularThisWeekStore,
  products: FeedProductView[],
  storeLabel: string,
): PopularPick[] {
  const productById = new Map(
    products.map((product) => [product.canonicalId, product]),
  );
  const entries = [...(POPULAR_THIS_WEEK[store] ?? [])].sort(
    (a, b) => a.displayOrder - b.displayOrder,
  );

  return entries.map((entry) => {
    const primaryId = entry.trackerFamilyIds[0];
    const product = primaryId ? productById.get(primaryId) : undefined;
    return toPopularPick(entry, product, storeLabel);
  });
}

export function buildHomepagePreview(): HomepagePreview {
  const safewayProducts = buildSafewayYamlProducts();
  const vonsProducts = buildVonsYamlProducts();

  return {
    generatedAt: new Date().toISOString(),
    popularWeekLabel: popularWeekLabel(),
    popularPicksSafeway: buildPopularPicksForStore(
      "safeway",
      safewayProducts,
      "Safeway",
    ),
    popularPicksVons: buildPopularPicksForStore(
      "vons",
      vonsProducts,
      "Vons",
    ),
  };
}
