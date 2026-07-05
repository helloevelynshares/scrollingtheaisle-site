import { computeFeedProductBenchmark } from "../data/priceBenchmarks";
import {
  formatComparisonUnit,
  getComparisonBadgeContent,
} from "../data/priceComparisonUtils";
import { buildSafewayFallbackProducts } from "../data/priceTrackerFallback";
import type { FeedProductView } from "../data/priceTrackerTypes";
import {
  formatPrice,
  getCurrentPrice,
  getDiscountPercent,
  getEffectiveBaseline,
  getFamilyBuyWaitTakeaway,
  hasChartableData,
  isDealFamily,
} from "../data/priceTrackerUtils";
import { WEEKLY_AD_WEEKS } from "../data/weeklyAdPrices.generated";

export type HomepageBadge =
  | "Stock up"
  | "Good small-pack buy"
  | "Costco still wins"
  | "Wait"
  | "Lowest seen recently"
  | "Beats Costco"
  | "About normal";

export type HomepageBuySignal =
  | "Stock up"
  | "Beats Costco"
  | "About normal"
  | "Wait"
  | "Costco wins";

export type StockUpPick = {
  id: string;
  name: string;
  store: string;
  price: string;
  unitPrice: string;
  badge: HomepageBadge;
  explanation: string;
  trackerUrl: string;
  isPlaceholder: boolean;
};

export type TrackerPreviewRow = {
  id: string;
  name: string;
  currentPrice: string;
  store: string;
  unitPrice: string;
  comparisonSignal: string;
  buySignal: HomepageBuySignal;
};

export type TikTokHighlight = {
  title: string;
  finding: string;
  why: string;
  url: string;
  ctaLabel: string;
};

export type HomepagePreview = {
  generatedAt: string;
  weekLabel: string;
  feedLabel: string;
  stockUpPicks: StockUpPick[];
  trackerPreview: TrackerPreviewRow[];
  tiktokHighlights: TikTokHighlight[];
};

const TRACKER_BASE = "staging-price-tracker/";

function latestWeekLabel(): string {
  const latest = WEEKLY_AD_WEEKS[WEEKLY_AD_WEEKS.length - 1];
  if (!latest) {
    return "This week";
  }
  const start = new Date(`${latest.weekStart}T12:00:00`);
  const end = new Date(`${latest.weekEnd}T12:00:00`);
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${fmt(start)}–${fmt(end)}`;
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

function comparisonSignal(product: FeedProductView): string {
  const comparison = product.priceComparison;
  if (!comparison) {
    return "No Costco comparison yet";
  }

  const badge = getComparisonBadgeContent(
    comparison,
    product.feedId,
    product.feedLabel,
  );
  if (!badge) {
    return "Comparison unavailable";
  }

  return badge.detail ? `${badge.title} · ${badge.detail}` : badge.title;
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

function getBuySignal(product: FeedProductView): HomepageBuySignal {
  const badge = getBadge(product);

  if (badge === "Stock up" || badge === "Lowest seen recently") {
    return "Stock up";
  }
  if (badge === "Beats Costco" || badge === "Good small-pack buy") {
    return badge === "Beats Costco" ? "Beats Costco" : "About normal";
  }
  if (badge === "Costco still wins") {
    return "Costco wins";
  }
  if (badge === "About normal") {
    return "About normal";
  }
  return "Wait";
}

function buildExplanation(product: FeedProductView): string {
  if (isDealFamily(product)) {
    const takeaway = getFamilyBuyWaitTakeaway(product);
    if (takeaway.tone === "buy") {
      return `${product.feedLabel} sale this week — mix flavors instead of one big warehouse pack.`;
    }
    if (takeaway.tone === "costco") {
      return "Costco still wins on unit price if you want the classic bulk pack.";
    }
    if (takeaway.tone === "grocery" || takeaway.tone === "close") {
      return `${product.feedLabel} is competitive this week with more variety than Costco.`;
    }
    return "Regular pricing — worth waiting unless you want a specific flavor or size.";
  }

  const benchmark = computeFeedProductBenchmark(product);
  const discount = getDiscountPercent(product);
  const baseline = getEffectiveBaseline(product);
  const current = getCurrentPrice(product);

  if (benchmark.benchmarkBucket === "all-time low") {
    return "At the lowest price we've tracked in weekly ads.";
  }
  if (benchmark.benchmarkBucket === "near all-time low") {
    return "Near the best price we've seen — worth grabbing if you need it.";
  }
  if (discount != null && discount >= 15 && baseline != null && current != null) {
    return `${discount}% below the usual ${formatPrice(baseline)} shelf price.`;
  }
  if (product.priceComparison?.winner === "grocery") {
    return `${product.feedLabel} beats Costco on unit price this week.`;
  }
  if (product.priceComparison?.winner === "costco") {
    return "Warehouse pricing still wins if you can buy in bulk.";
  }
  if (discount != null && discount > 0) {
    return `A modest sale — fine for a small pack, not a pantry fill.`;
  }
  return "Regular pricing this week — safe to skip unless you're out.";
}

function stockUpScore(product: FeedProductView): number {
  if (!hasChartableData(product)) {
    return -100;
  }

  const badge = getBadge(product);
  const discount = getDiscountPercent(product) ?? 0;
  const benchmark = computeFeedProductBenchmark(product);

  let score = discount;

  switch (badge) {
    case "Stock up":
      score += 50;
      break;
    case "Lowest seen recently":
      score += 45;
      break;
    case "Beats Costco":
      score += 35;
      break;
    case "Good small-pack buy":
      score += 25;
      break;
    case "About normal":
      score += 10;
      break;
    case "Costco still wins":
      score -= 5;
      break;
    case "Wait":
      score -= 20;
      break;
    default:
      break;
  }

  if (benchmark.benchmarkBucket === "strong sale") {
    score += 20;
  }

  if (isDealFamily(product) && product.salePriceRange) {
    score += 15;
  }

  return score;
}

function toStockUpPick(product: FeedProductView): StockUpPick {
  const current = getCurrentPrice(product);
  return {
    id: product.canonicalId,
    name: product.displayName,
    store: product.feedLabel,
    price: current != null ? formatPrice(current) : "—",
    unitPrice: unitPriceDisplay(product),
    badge: getBadge(product),
    explanation: buildExplanation(product),
    trackerUrl: TRACKER_BASE,
    isPlaceholder: !hasChartableData(product),
  };
}

function toTrackerRow(product: FeedProductView): TrackerPreviewRow {
  const current = getCurrentPrice(product);
  return {
    id: product.canonicalId,
    name: product.displayName,
    currentPrice: current != null ? formatPrice(current) : "—",
    store: product.feedLabel,
    unitPrice: unitPriceDisplay(product),
    comparisonSignal: comparisonSignal(product),
    buySignal: getBuySignal(product),
  };
}

const PLACEHOLDER_STOCK_UP: StockUpPick[] = [
  {
    id: "placeholder-berries",
    name: "Berries",
    store: "Safeway",
    price: "$3.99",
    unitPrice: "$3.99/lb",
    badge: "Stock up",
    explanation: "Placeholder pick — run generate:homepage-preview after weekly ad data updates.",
    trackerUrl: TRACKER_BASE,
    isPlaceholder: true,
  },
  {
    id: "placeholder-doritos",
    name: "Doritos Nacho Cheese",
    store: "Safeway",
    price: "$3.99",
    unitPrice: "$0.43/oz",
    badge: "Good small-pack buy",
    explanation: "Weekly ad match pending — check the full tracker for live pricing.",
    trackerUrl: TRACKER_BASE,
    isPlaceholder: true,
  },
  {
    id: "placeholder-yogurt",
    name: "Greek Yogurt",
    store: "Safeway",
    price: "$5.99",
    unitPrice: "$0.19/oz",
    badge: "About normal",
    explanation: "Placeholder until the next ad scrape lands.",
    trackerUrl: TRACKER_BASE,
    isPlaceholder: true,
  },
];

const TIKTOK_HIGHLIGHTS: TikTokHighlight[] = [
  {
    title: "Safeway weekly walk",
    finding: "Strawberries dipped under usual Bay Area pricing",
    why: "We matched the ad price against past weeks and Costco per-pound math.",
    url: "https://www.tiktok.com/@evelynshares/video/7535317556773653773",
    ctaLabel: "Watch the breakdown",
  },
  {
    title: "Costco vs grocery chips",
    finding: "When the big bag wins — and when variety packs do",
    why: "Unit-price comparisons for families like Ritz and snack multipacks.",
    url: "https://www.tiktok.com/@evelynshares/video/7539982330568510734",
    ctaLabel: "Watch the aisle walk",
  },
  {
    title: "New finds on the endcap",
    finding: "Seasonal snacks and limited drops worth a second look",
    why: "Not every find is a deal — we flag what's hype vs. actually cheaper.",
    url: "https://www.tiktok.com/@evelynshares/video/7244764793285037358",
    ctaLabel: "See the find",
  },
];

export function buildHomepagePreview(): HomepagePreview {
  const products = buildSafewayFallbackProducts().filter(hasChartableData);
  const ranked = [...products].sort(
    (a, b) => stockUpScore(b) - stockUpScore(a),
  );

  const stockUpPicks =
    ranked.length > 0
      ? ranked.slice(0, 6).map(toStockUpPick)
      : PLACEHOLDER_STOCK_UP;

  const trackerPreview = (
    ranked.length > 0 ? ranked : buildSafewayFallbackProducts()
  )
    .slice(0, 10)
    .map(toTrackerRow);

  const feedLabel =
    products[0]?.feedLabel ?? ranked[0]?.feedLabel ?? "Safeway";

  return {
    generatedAt: new Date().toISOString(),
    weekLabel: latestWeekLabel(),
    feedLabel,
    stockUpPicks,
    trackerPreview,
    tiktokHighlights: TIKTOK_HIGHLIGHTS,
  };
}
