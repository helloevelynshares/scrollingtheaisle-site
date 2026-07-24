import {
  POPULAR_THIS_WEEK,
  type PopularThisWeekEntry,
  type PopularThisWeekStore,
} from "../data/canonicalTrackerFamilies";
import { getPopularWeekLabel } from "../data/popularThisWeekCopy";
import { computeFeedProductBenchmark } from "../data/priceBenchmarks";
import {
  formatComparisonUnit,
} from "../data/priceComparisonUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import {
  formatPrice,
  getCurrentPrice,
  getDealAdjustedUnitPrice,
  getDiscountPercent,
  hasChartableData,
  isProductOnSale,
} from "../data/priceTrackerUtils";
import {
  buildSafewayYamlProducts,
  buildVonsYamlProducts,
} from "../data/yamlFamilyProducts";
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
  /** Optional curated editorial badge label (e.g. FRIDAY, DEAL) that overrides `badge` for display. */
  customBadge?: string;
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

const TRACKER_BASE = "grocery-price-tracker/";

function unitPriceDisplay(product: FeedProductView): string {
  const dealUnit = getDealAdjustedUnitPrice(product);
  if (dealUnit) {
    const unit = formatComparisonUnit(dealUnit.unit);
    return `$${dealUnit.price.toFixed(2)}/${unit}`;
  }

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

  return price != null ? formatPrice(price) : "n/a";
}

function getBadge(product: FeedProductView): HomepageBadge {
  const benchmark = computeFeedProductBenchmark(product);
  const discount = getDiscountPercent(product) ?? 0;

  // Hand-picked summaries stay Safeway/Vons-deal focused — never surface Costco
  // win/loss wording on these editorial cards (Costco stays on product charts).
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
  // Curated editorial cards carry a manual price string (effective_price/ad_price).
  // Prefer it so handpicked deals never render a blank "n/a".
  const editorialPrice = (entry.price ?? "").trim();

  return {
    id: primaryId,
    name: entry.title,
    store: storeLabel,
    price: editorialPrice || (current != null ? formatPrice(current) : "n/a"),
    unitPrice: product ? unitPriceDisplay(product) : "",
    badge: product ? getBadge(product) : onSale ? "Stock up" : "About normal",
    customBadge: entry.badge || undefined,
    explanation: entry.subtitle || entry.reason,
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
    popularWeekLabel: getPopularWeekLabel(),
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
