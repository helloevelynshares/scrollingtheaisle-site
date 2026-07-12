import {
  formatCostcoRegionLabel,
  getCostcoRegionForFeed,
} from "./costcoRegions";
import {
  formatCostcoItemLabel,
  formatCostcoPackageSize,
  formatCostcoReferenceLine,
  getProductCostcoComparisonDetails,
  hasMeaningfulCostcoComparison,
} from "./priceComparisonUtils";
import {
  computeFeedProductBenchmark,
  type BenchmarkBucket,
  type PriceBenchmarkResult,
} from "./priceBenchmarks";
import type { FeedProductView, WeeklyPrice } from "./priceTrackerTypes";
import {
  formatPreviewPriceLabel,
  formatPreviewStartLabel,
  isActiveAdWeek,
} from "./weeklyAdPreview";

export type { BenchmarkBucket, PriceBenchmarkResult };
export { computeFeedProductBenchmark };

export type PricePoint = WeeklyPrice & {
  isBaseline?: boolean;
  label?: string;
  priceMax?: number;
  isCostco?: boolean;
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
      priceMax: week.priceMax ?? week.price,
    }))
    .sort((a, b) => a.weekStart.localeCompare(b.weekStart));
}

/** Costco warehouse prices for the feed's paired region — never mixed across locations. */
export function getCostcoChartPricePoints(
  product: FeedProductView,
): PricePoint[] {
  const history = product.costcoPriceHistory ?? [];
  if (
    !product.costcoComparable ||
    history.length === 0 ||
    !hasMeaningfulCostcoComparison(product.priceComparison)
  ) {
    return [];
  }

  // Normalize Costco price to the same unit the grocery graph tracks.
  // For produce tracked per-lb or per-each, use unitPrice (already per-lb/each).
  // For packaged goods (oz, bar, can, etc.) use the raw package price so the
  // y-axis stays in familiar "price per purchase" territory.
  const groceryUnitType = product.priceComparison?.groceryUnitType;
  const useUnitPrice =
    (groceryUnitType === "lb" || groceryUnitType === "each") &&
    history.some((p) => p.unitPrice != null && p.unitPrice < p.price);

  return history.map((point) => ({
    weekStart: point.date,
    label: formatWeekLabel(point.date),
    price:
      useUnitPrice && point.unitPrice != null ? point.unitPrice : point.price,
    adPrice: null,
    matchConfidence: null,
    priceType: "baseline" as const,
    isBaselineFallback: false,
    isCostco: true,
    sourceLabel: point.sourceFile,
  }));
}

export function hasCostcoChartData(product: FeedProductView): boolean {
  return getCostcoChartPricePoints(product).length > 0;
}

export type UnifiedChartRow = {
  weekStart: string;
  label: string;
  groceryPrice: number;
  groceryPriceMax?: number;
  priceType: string;
  isBaselineFallback: boolean;
  costcoPrice: number | null;
  /** e.g. "friday_only" — forwarded from WeeklyPrice for tooltip Option A */
  availabilityType?: string | null;
  /** Promo copy e.g. "3 for $5 Friday July 3rd" — forwarded for tooltip Option A */
  promoNote?: string | null;
};

function addDays(isoDate: string, days: number): string {
  const date = new Date(`${isoDate}T12:00:00`);
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

/** Map a Costco observation date onto the grocery weekly bucket it falls in. */
function findGroceryWeekForCostcoDate(
  costcoDate: string,
  weekStarts: string[],
): string | null {
  const sorted = weekStarts.filter((week) => week !== "baseline").sort();
  if (sorted.length === 0) {
    return null;
  }

  for (let index = 0; index < sorted.length; index += 1) {
    const start = sorted[index];
    const nextStart = sorted[index + 1];
    const endExclusive = nextStart ?? addDays(start, 7);
    if (costcoDate >= start && costcoDate < endExclusive) {
      return start;
    }
  }

  const lastWeek = sorted[sorted.length - 1];
  if (costcoDate >= lastWeek && costcoDate < addDays(lastWeek, 7)) {
    return lastWeek;
  }

  return null;
}

/** Grocery + Costco rows sharing one x-axis so warehouse points align to ad weeks. */
export function buildUnifiedChartRows(product: FeedProductView): UnifiedChartRow[] {
  // Single-mode charts use ReferenceLine for baseline; skip the synthetic
  // "Baseline" x-axis anchor here (range-mode charts still use getAllPricePoints).
  const groceryPoints = getAllPricePoints(product).filter(
    (point) => point.weekStart !== "baseline",
  );
  const costcoPoints = getCostcoChartPricePoints(product);
  const weekStarts = groceryPoints.map((point) => point.weekStart);
  const costcoByWeek = new Map<string, number>();

  for (const point of costcoPoints) {
    const week = findGroceryWeekForCostcoDate(point.weekStart, weekStarts);
    if (week != null) {
      costcoByWeek.set(week, point.price);
    }
  }

  // When Costco data exists but doesn't cover every historical week, fill all
  // weeks with the most-recent known Costco price so the line is continuous
  // ("flat line" from last observed price extended backward and forward).
  let flatCostcoPrice: number | null = null;
  if (costcoPoints.length > 0) {
    const sorted = [...costcoPoints].sort((a, b) =>
      a.weekStart.localeCompare(b.weekStart),
    );
    flatCostcoPrice = sorted[sorted.length - 1].price;
  }

  return groceryPoints.map((point) => ({
    weekStart: point.weekStart,
    label: point.label ?? formatWeekLabel(point.weekStart),
    groceryPrice: point.price,
    groceryPriceMax: point.priceMax ?? point.price,
    priceType: point.priceType,
    isBaselineFallback: point.isBaselineFallback,
    costcoPrice: costcoByWeek.get(point.weekStart) ?? flatCostcoPrice,
    availabilityType: point.availabilityType ?? null,
    promoNote: point.promoNote ?? null,
  }));
}

export function getCostcoChartRegionLabel(product: FeedProductView): string | null {
  const region = getCostcoRegionForFeed(product.feedId);
  return region ? formatCostcoRegionLabel(region) : null;
}

export function getLatestWeeklyPrice(product: FeedProductView): WeeklyPrice | null {
  if (product.weeklyPrices.length === 0) {
    return null;
  }
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );
  return sorted[sorted.length - 1] ?? null;
}

/** Prefer the calendar-active ad week; fall back to latest non-preview, then latest. */
export function getCurrentWeeklyPrice(
  product: FeedProductView,
): WeeklyPrice | null {
  if (product.weeklyPrices.length === 0) {
    return null;
  }
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );
  const active = [...sorted]
    .reverse()
    .find((week) => isActiveAdWeek(week.weekStart, week.weekEnd));
  if (active) {
    return active;
  }
  const latestNonPreview = [...sorted]
    .reverse()
    .find((week) => !week.isPreviewWeek);
  return latestNonPreview ?? sorted[sorted.length - 1] ?? null;
}

export function isProductInPreviewWeek(product: FeedProductView): boolean {
  return getLatestWeeklyPrice(product)?.isPreviewWeek === true;
}

export function getCurrentPrice(product: FeedProductView): number | null {
  const baseline = getEffectiveBaseline(product);
  if (!hasChartableData(product) || baseline == null) {
    return null;
  }
  return getCurrentWeeklyPrice(product)?.price ?? baseline;
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

/** Pack count from labels like "12-pack, 12 fl oz cans". */
export function parsePackUnitCount(
  sizeLabel: string | undefined,
): { count: number; unit: string } | null {
  if (!sizeLabel) {
    return null;
  }
  const packMatch = sizeLabel.match(/(\d+)-pack\b/i);
  if (!packMatch) {
    return null;
  }
  const count = Number(packMatch[1]);
  if (!(count > 1)) {
    return null;
  }
  const lower = sizeLabel.toLowerCase();
  const unit = /\bcan/.test(lower)
    ? "can"
    : /\bbag/.test(lower)
      ? "bag"
      : "item";
  return { count, unit };
}

/** Per-unit price from the current deal-adjusted price (weekly ad), not baseline. */
export function getDealAdjustedUnitPrice(
  product: FeedProductView,
): { price: number; unit: string } | null {
  const current = getCurrentPrice(product);
  const pack = parsePackUnitCount(product.subtitle ?? product.sizeLabel);
  if (current == null || pack == null) {
    return null;
  }
  return { price: current / pack.count, unit: pack.unit };
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

export function formatPriceRange(
  range: { min: number; max: number } | null | undefined,
): string | null {
  if (!range) {
    return null;
  }
  if (Math.abs(range.min - range.max) < 0.01) {
    return formatPrice(range.min);
  }
  return `${formatPrice(range.min)}–${formatPrice(range.max)}`;
}

export function isDealFamily(product: FeedProductView): boolean {
  return product.trackerType === "deal_family" || product.trackerType === "brand_family";
}

export function getFamilyDisplayPrice(product: FeedProductView): string {
  if (product.salePriceRange) {
    const sale = formatPriceRange(product.salePriceRange);
    if (sale) {
      return sale;
    }
  }
  if (product.priceRange) {
    const regular = formatPriceRange(product.priceRange);
    if (regular) {
      return regular;
    }
  }
  return formatPrice(getCurrentPrice(product));
}

export function getFamilyPriceCaption(product: FeedProductView): string {
  if (isProductInPreviewWeek(product)) {
    return "Preview";
  }
  if (product.salePriceRange) {
    return "This week";
  }
  if (product.priceRange) {
    return "Usually";
  }
  return "";
}

export type FamilyValueBadge = {
  label: string;
  tone: "grocery" | "costco" | "neutral" | "muted";
};

export type FamilyBuyWaitTone =
  | "buy"
  | "wait"
  | "costco"
  | "close"
  | "grocery"
  | "neutral";

export type FamilyBuyWaitTakeaway = {
  label: string;
  tone: FamilyBuyWaitTone;
};

const MEANINGFUL_SALE_PCT = 15;
const GOOD_DEAL_SALE_PCT = 5;
const COSTCO_WINS_PCT = 25;

export function isProductOnSale(product: FeedProductView): boolean {
  if (product.salePriceRange) {
    return true;
  }
  const discount = getDiscountPercent(product);
  return discount != null && discount >= GOOD_DEAL_SALE_PCT;
}

function getProductSaleDiscountPercent(product: FeedProductView): number | null {
  const familyDiscount = getFamilySaleDiscountPercent(product);
  if (familyDiscount != null) {
    return familyDiscount;
  }
  return getDiscountPercent(product);
}

function getFamilySaleDiscountPercent(product: FeedProductView): number | null {
  if (!product.salePriceRange) {
    return null;
  }
  const usualMin =
    product.priceRange?.min ?? product.baselinePrice ?? null;
  if (usualMin == null || usualMin <= 0) {
    return null;
  }
  const saleMin = product.salePriceRange.min;
  return Math.round(((usualMin - saleMin) / usualMin) * 100);
}

/**
 * Deal-quality ordering for a section grid. Lower rank = stronger deal, so a
 * plain ascending sort puts the best current deals first (top-left), filling
 * the grid row by row.
 *
 * Priority (best → worst):
 *   1. Currently on sale (deal-adjusted price below baseline) before non-deals.
 *   2. Benchmark bucket: all-time low > near all-time low > strong sale >
 *      normal sale > weak sale > insufficient history.
 *   3. Larger percent discount vs baseline (higher wins).
 *   4. Stable name / id tiebreak so ordering is fully deterministic.
 */
const BENCHMARK_BUCKET_RANK: Record<BenchmarkBucket, number> = {
  "all-time low": 0,
  "near all-time low": 1,
  "strong sale": 2,
  "normal sale": 3,
  "weak sale": 4,
  "insufficient history": 5,
};

export type DealQualityRankKey = {
  onSaleRank: number;
  bucketRank: number;
  discountPercent: number;
  name: string;
  canonicalId: string;
};

/** Ordering key for a product, reusing existing benchmark/deal helpers. */
export function getDealQualityRankKey(
  product: FeedProductView,
): DealQualityRankKey {
  const benchmark = computeFeedProductBenchmark(product);
  const discount =
    getProductSaleDiscountPercent(product) ?? getDiscountPercent(product) ?? 0;
  return {
    onSaleRank: isProductOnSale(product) ? 0 : 1,
    bucketRank: BENCHMARK_BUCKET_RANK[benchmark.benchmarkBucket] ?? 5,
    discountPercent: discount,
    name: product.displayName ?? "",
    canonicalId: product.canonicalId,
  };
}

/** Comparator ranking stronger deals first (ascending = best deal first). */
export function compareByDealQuality(
  a: FeedProductView,
  b: FeedProductView,
): number {
  const ka = getDealQualityRankKey(a);
  const kb = getDealQualityRankKey(b);
  if (ka.onSaleRank !== kb.onSaleRank) {
    return ka.onSaleRank - kb.onSaleRank;
  }
  if (ka.bucketRank !== kb.bucketRank) {
    return ka.bucketRank - kb.bucketRank;
  }
  if (ka.discountPercent !== kb.discountPercent) {
    return kb.discountPercent - ka.discountPercent;
  }
  const nameCmp = ka.name.localeCompare(kb.name);
  if (nameCmp !== 0) {
    return nameCmp;
  }
  return ka.canonicalId.localeCompare(kb.canonicalId);
}

/** Stable copy of `products` ordered best-deal-first for a section grid. */
export function rankProductsByDealQuality(
  products: FeedProductView[],
): FeedProductView[] {
  return [...products].sort(compareByDealQuality);
}

function getGroceryVsCostcoPercent(product: FeedProductView): number | null {
  const comparison = product.priceComparison;
  if (
    comparison?.groceryUnitPrice == null ||
    comparison.costcoUnitPrice == null ||
    comparison.costcoUnitPrice <= 0
  ) {
    return null;
  }
  return (
    ((comparison.groceryUnitPrice - comparison.costcoUnitPrice) /
      comparison.costcoUnitPrice) *
    100
  );
}

function closeEnoughLabel(feedLabel: string): string {
  if (feedLabel === "Safeway") {
    return "Close enough — Safeway has more variety";
  }
  if (feedLabel === "Vons") {
    return "Close enough — Vons has more variety";
  }
  return `Close enough — ${feedLabel} has more variety`;
}

/** Primary buy/wait headline for collapsed family cards. */
export function getFamilyBuyWaitTakeaway(
  product: FeedProductView,
): FamilyBuyWaitTakeaway {
  const preview = isProductInPreviewWeek(product);
  const onSale = isProductOnSale(product);
  const discount = getProductSaleDiscountPercent(product);
  const vsCostco = hasMeaningfulCostcoComparison(product.priceComparison)
    ? getGroceryVsCostcoPercent(product)
    : null;

  if (preview && onSale && discount != null) {
    if (discount >= MEANINGFUL_SALE_PCT) {
      return { label: "Strong preview deal when ad starts", tone: "buy" };
    }
    if (discount >= GOOD_DEAL_SALE_PCT) {
      return { label: "Good preview deal when ad starts", tone: "buy" };
    }
  }

  if (onSale && discount != null) {
    if (discount >= MEANINGFUL_SALE_PCT) {
      return { label: "Great week to buy", tone: "buy" };
    }
    if (discount >= GOOD_DEAL_SALE_PCT) {
      return { label: "Good deal this week", tone: "buy" };
    }
  }

  if (vsCostco != null) {
    if (vsCostco <= 0) {
      return {
        label: preview
          ? `${product.feedLabel} may win when ad starts`
          : `${product.feedLabel} wins this week`,
        tone: "grocery",
      };
    }
    if (vsCostco > COSTCO_WINS_PCT) {
      return { label: "Costco wins on price", tone: "costco" };
    }
    return { label: closeEnoughLabel(product.feedLabel), tone: "close" };
  }

  if (!onSale) {
    return {
      label: preview ? "Wait for ad to start" : "Wait for a sale",
      tone: "wait",
    };
  }

  return {
    label: preview ? "Preview regular price" : "Regular price this week",
    tone: "neutral",
  };
}

/** Price line for collapsed family cards — current sale or usual price. */
export function getFamilyUsuallyLabel(product: FeedProductView): string {
  const preview = isProductInPreviewWeek(product);
  const latestWeek = getLatestWeeklyPrice(product);
  const weekStart = latestWeek?.weekStart ?? "";

  if (product.salePriceRange) {
    const { min, max } = product.salePriceRange;
    if (Math.abs(min - max) < 0.01) {
      const label = `${formatPrice(min)} each`;
      return preview && weekStart
        ? formatPreviewPriceLabel(label, weekStart)
        : `${label} this week`;
    }
    const sale = formatPriceRange(product.salePriceRange);
    const label = sale ? `${sale} each` : formatPrice(min);
    return preview && weekStart
      ? formatPreviewPriceLabel(label, weekStart)
      : `${label} this week`;
  }

  const current = getCurrentPrice(product);
  const discount = getDiscountPercent(product);
  if (current != null && discount != null && discount >= GOOD_DEAL_SALE_PCT) {
    const label = formatPrice(current);
    return preview && weekStart
      ? formatPreviewPriceLabel(label, weekStart)
      : `${label} this week`;
  }

  if (product.priceRange) {
    const regular = formatPriceRange(product.priceRange);
    if (regular) {
      return preview && weekStart
        ? `Preview usual ${regular}`
        : `Usually ${regular}`;
    }
  }

  if (preview && weekStart && current != null) {
    return formatPreviewPriceLabel(formatPrice(current), weekStart);
  }
  return `Usually ${formatPrice(current)}`;
}

/** "Usually $X–$Y" shown below quick take when a family is on sale. */
export function getFamilyUsuallyRangeLabel(
  product: FeedProductView,
): string | null {
  if (product.salePriceRange && product.priceRange) {
    const regular = formatPriceRange(product.priceRange);
    return regular ? `Usually ${regular}` : null;
  }

  if (!product.salePriceRange && isProductOnSale(product)) {
    const baseline = getEffectiveBaseline(product);
    return baseline != null ? `Usually ${formatPrice(baseline)}` : null;
  }

  return null;
}

/** One short reason line under the price on collapsed family cards. */
export function getFamilyBuyWaitReason(product: FeedProductView): string | null {
  const takeaway = getFamilyBuyWaitTakeaway(product);

  if (product.canonicalId === "ben_jerrys_ice_cream") {
    if (takeaway.tone === "buy") {
      return "Mix and match flavors instead of buying one big pack.";
    }
    return "Worth waiting unless you want a specific flavor.";
  }

  if (
    product.canonicalId === "ritz_crackers_snacks" &&
    hasMeaningfulCostcoComparison(product.priceComparison)
  ) {
    if (takeaway.tone === "costco") {
      return `Costco is cheaper for regular Ritz. ${product.feedLabel} has more Ritz styles.`;
    }
    if (takeaway.tone === "close" || takeaway.tone === "grocery") {
      return `Costco is a little cheaper, but ${product.feedLabel} has more Ritz styles and smaller boxes.`;
    }
    if (takeaway.tone === "buy") {
      return `Strong ${product.feedLabel} sale — ${product.feedLabel} still has more Ritz styles than Costco.`;
    }
  }

  return null;
}

/** Short shopper-facing lines on collapsed family cards. */
export function getFamilyShopperNoteLines(product: FeedProductView): string[] {
  const onSale = isProductOnSale(product);

  if (product.canonicalId === "ben_jerrys_ice_cream") {
    if (onSale) {
      return [
        `Great ${product.feedLabel} week.`,
        "Mix and match flavors instead of buying one big pack.",
      ];
    }
    return ["Wait for a sale unless you want a specific flavor."];
  }

  if (
    product.canonicalId === "ritz_crackers_snacks" &&
    hasMeaningfulCostcoComparison(product.priceComparison)
  ) {
    return [
      "Costco is cheaper for regular Ritz.",
      `${product.feedLabel} has more Ritz styles.`,
    ];
  }

  return [];
}

/** @deprecated Use getFamilyBuyWaitReason */
export function getFamilyShopperNote(product: FeedProductView): string | null {
  return getFamilyBuyWaitReason(product);
}

/** "Best value" / "More variety" pills for comparable families (e.g. Ritz). */
export function getFamilyValueBadges(product: FeedProductView): FamilyValueBadge[] {
  if (!hasMeaningfulCostcoComparison(product.priceComparison)) {
    return [];
  }

  return [
    { label: "Best value: Costco", tone: "costco" },
    { label: `More variety: ${product.feedLabel}`, tone: "grocery" },
  ];
}

export function getFamilyExpandedSectionTitle(product: FeedProductView): string {
  if (product.canonicalId === "ritz_crackers_snacks") {
    return "Ritz styles this covers";
  }
  return "What this covers";
}

export function getFamilyToggleLabel(
  product: FeedProductView,
  expanded: boolean,
): string {
  if (expanded) {
    return "Hide details";
  }
  if (product.canonicalId === "ritz_crackers_snacks") {
    return "See Ritz styles";
  }
  return "See what's included";
}

export type FamilyExpandedRow = {
  label: string;
  detail: string;
};

/** Product/style rows for the expanded family details section. */
export function getFamilyExpandedRows(
  product: FeedProductView,
): FamilyExpandedRow[] {
  if (product.canonicalId === "ritz_crackers_snacks") {
    return [
      { label: "Classic boxes", detail: "Closest match to Costco" },
      { label: "Fresh Stacks", detail: "Same cracker, smaller sleeves" },
      {
        label: "Crisp & Thins / Toasted Chips",
        detail: "More chip-like",
      },
      { label: "Bits", detail: "Mini sandwich crackers" },
      { label: "Drizzled Minis", detail: "Sweet snack" },
    ];
  }

  if (product.canonicalId === "ben_jerrys_ice_cream") {
    return [
      { label: "Pints", detail: "16 oz" },
      { label: "Non-dairy pints", detail: "16 oz" },
      { label: "4-count bars", detail: "Usually around 10.1 fl oz" },
    ];
  }

  return (
    product.familyMembers?.map((member) => ({
      label: member.label,
      detail: member.sizeLabel,
    })) ?? []
  );
}

export type FamilyCostcoComparisonDetails = {
  intro: string;
  costcoLabel: string;
  costcoDetail: string;
  groceryLabel: string;
  groceryDetail: string;
  verdict: string;
};

/** Structured Costco comparison for expanded family details. */
export function getFamilyCostcoComparisonDetails(
  product: FeedProductView,
): FamilyCostcoComparisonDetails | null {
  const comparison = product.priceComparison;
  if (!comparison || !hasMeaningfulCostcoComparison(comparison)) {
    return null;
  }

  const costcoReference = formatCostcoReferenceLine(comparison);
  const costcoUnit =
    comparison.costcoUnitPrice != null
      ? `about $${comparison.costcoUnitPrice.toFixed(2)}/oz`
      : null;
  const groceryUnit =
    comparison.groceryUnitPrice != null
      ? `about $${comparison.groceryUnitPrice.toFixed(2)}/oz`
      : null;

  const costcoDetail = [
    formatPrice(comparison.costcoPrice),
    costcoUnit,
  ]
    .filter(Boolean)
    .join(" · ");

  const groceryPrice =
    comparison.groceryPrice != null
      ? formatPrice(comparison.groceryPrice)
      : product.priceRange
        ? formatPriceRange(product.priceRange)
        : null;
  const groceryDetail = [groceryPrice, groceryUnit].filter(Boolean).join(" · ");

  if (product.canonicalId === "ritz_crackers_snacks") {
    const packageDesc =
      formatCostcoPackageSize(comparison) ??
      comparison.comparisonNote?.trim() ??
      "61.6 oz";

    return {
      intro:
        "We compare Costco against the classic Ritz box because that's closest to Costco's big Original Ritz pack.",
      costcoLabel:
        formatCostcoItemLabel(comparison) ??
        `Original Ritz, ${packageDesc}`,
      costcoDetail,
      groceryLabel: "Classic Ritz boxes, 12–13.7 oz",
      groceryDetail,
      verdict: `Costco is much cheaper if you just want regular Ritz. ${product.feedLabel} is better if you want smaller boxes or different Ritz styles.`,
    };
  }

  const details = getProductCostcoComparisonDetails(
    comparison,
    product.feedLabel,
  );
  if (!details || !costcoReference) {
    return null;
  }

  return {
    intro: details.referenceLine,
    costcoLabel: formatCostcoItemLabel(comparison) ?? "Matched Costco item",
    costcoDetail,
    groceryLabel:
      comparison.groceryPackageDescription?.trim() ??
      product.sizeLabel ??
      product.displayName,
    groceryDetail,
    verdict: details.verdictLine ?? "See per-unit pricing above.",
  };
}

/** Footnote below expanded member rows (e.g. Ben & Jerry's format pricing). */
export function getFamilyExpandedFootnote(
  product: FeedProductView,
): string | null {
  if (product.canonicalId === "ben_jerrys_ice_cream") {
    return "These can have different regular prices, even when the sale price is the same.";
  }
  return null;
}

export type FamilyStockUpRating = "Great" | "Good" | "Great if buying full promo quantity";

export type FamilyStatus =
  | "On sale this week"
  | "Promo deal this week"
  | "Preview sale"
  | "Preview promo";

const MULTI_BUY_OFFER_RE =
  /\b\d+\s+for\s+\$|\bwhen you buy\s+\d+|\bbuy\s+\d+.*get/i;

function latestFamilyOfferText(product: FeedProductView): string | null {
  const sorted = [...product.weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );
  for (let i = sorted.length - 1; i >= 0; i -= 1) {
    const text = sorted[i]?.offerText?.trim();
    if (text) {
      return text;
    }
  }
  return null;
}

/** Sale/promo status pill for Family Deal Card headers. */
export function getFamilyStatus(product: FeedProductView): FamilyStatus | null {
  if (!isProductOnSale(product)) {
    return null;
  }

  const preview = isProductInPreviewWeek(product);
  const offerText = latestFamilyOfferText(product);
  if (offerText && MULTI_BUY_OFFER_RE.test(offerText)) {
    return preview ? "Preview promo" : "Promo deal this week";
  }
  return preview ? "Preview sale" : "On sale this week";
}

/** Stock-up rating for Family Deal Card (Option 9 pattern). */
export function getFamilyStockUpRating(
  product: FeedProductView,
): FamilyStockUpRating {
  const offerText = latestFamilyOfferText(product);
  if (offerText && MULTI_BUY_OFFER_RE.test(offerText)) {
    return "Great if buying full promo quantity";
  }

  const discount = getProductSaleDiscountPercent(product);
  const benchmark = computeFeedProductBenchmark(product);

  if (
    (discount != null && discount >= MEANINGFUL_SALE_PCT) ||
    benchmark.benchmarkBucket === "all-time low" ||
    benchmark.benchmarkBucket === "near all-time low" ||
    benchmark.benchmarkBucket === "strong sale"
  ) {
    return "Great";
  }

  if (discount != null && discount >= GOOD_DEAL_SALE_PCT) {
    return "Good";
  }

  const takeaway = getFamilyBuyWaitTakeaway(product);
  if (takeaway.tone === "buy") {
    return "Good";
  }

  return "Good";
}

/** One-line family summary above the price chart. */
export function getFamilySummary(product: FeedProductView): string {
  const onSale = isProductOnSale(product);
  const preview = isProductInPreviewWeek(product);
  const latestWeek = getLatestWeeklyPrice(product);
  const startLabel = latestWeek?.weekStart
    ? formatPreviewStartLabel(latestWeek.weekStart)
    : "soon";
  const name = product.displayName;

  if (preview) {
    if (onSale) {
      return `${name} has a preview sale price starting ${startLabel}.`;
    }
    return `${name} preview pricing starts ${startLabel}.`;
  }

  if (product.canonicalId === "ben_jerrys_ice_cream") {
    return onSale
      ? `${name} is at a strong stock-up price this week.`
      : `${name} is at regular pricing — worth waiting for a sale.`;
  }

  if (product.canonicalId === "ritz_crackers_snacks") {
    return onSale
      ? "Ritz products are included in a solid sale this week."
      : "Ritz products are at regular pricing this week.";
  }

  if (onSale) {
    return `${name} is at a sale price this week.`;
  }

  return `${name} is at regular pricing this week.`;
}

/** Multi-buy effective price line (e.g. "2 for $5 → $2.50 each"). */
export function getFamilyEffectivePriceLabel(
  product: FeedProductView,
): string | null {
  const offerText = latestFamilyOfferText(product);
  if (offerText && MULTI_BUY_OFFER_RE.test(offerText)) {
    if (product.salePriceRange) {
      const { min, max } = product.salePriceRange;
      if (Math.abs(min - max) < 0.01) {
        return `Effective ${formatPrice(min)} each`;
      }

      const range = formatPriceRange(product.salePriceRange);
      return range ? `Effective ${range} each` : null;
    }

    const current = getCurrentPrice(product);
    return current != null ? `Effective ${formatPrice(current)} each` : null;
  }

  return null;
}

/** Short note above the varieties drawer list. */
export function getFamilyVariantNote(product: FeedProductView): string {
  if (product.canonicalId === "ben_jerrys_ice_cream") {
    return "Pints, non-dairy pints, and 4-count bars may share the same weekly promo.";
  }
  if (product.canonicalId === "ritz_crackers_snacks") {
    return "Classic boxes, Fresh Stacks, Crisp & Thins, Bits, and Drizzled Minis may all appear under this family.";
  }
  if (product.subtitle) {
    return product.subtitle;
  }
  return "Participating varieties may share the same weekly promo.";
}

/** Grouping logic footnote in the varieties drawer. */
export function getFamilyPricingBehavior(product: FeedProductView): string {
  if (product.chartMode === "range") {
    return "This week grouped (same sale price). Tracked separately when normal prices differ.";
  }
  return "Tracked as one family when the weekly ad treats them as a single deal.";
}

/** Whether the card should show the varieties drawer hint. */
export function hasFamilyVarieties(product: FeedProductView): boolean {
  return (
    (product.familyMembers?.length ?? 0) > 1 ||
    getFamilyExpandedRows(product).length > 1
  );
}

export { INFERRED_BASELINE_SOURCE };
