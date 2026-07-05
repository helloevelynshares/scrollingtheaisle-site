import {
  formatCostcoRegionLabel,
  getCostcoComparisonLocationNote,
  getCostcoRegionForFeed,
} from "./costcoRegions";
import {
  computeFeedProductBenchmark,
  type BenchmarkBucket,
  type PriceBenchmarkResult,
} from "./priceBenchmarks";
import type { FeedProductView, WeeklyPrice } from "./priceTrackerTypes";

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

function isCostcoExcludedFromChart(product: FeedProductView): boolean {
  const comparison = product.priceComparison;
  return (
    comparison?.comparisonStatus === "not_sold_at_costco" ||
    comparison?.winner === "grocery_only"
  );
}

/** Costco warehouse prices for the feed's paired region — never mixed across locations. */
export function getCostcoChartPricePoints(
  product: FeedProductView,
): PricePoint[] {
  const history = product.costcoPriceHistory ?? [];
  if (
    !product.costcoComparable ||
    history.length === 0 ||
    isCostcoExcludedFromChart(product)
  ) {
    return [];
  }

  return history.map((point) => ({
    weekStart: point.date,
    label: formatWeekLabel(point.date),
    price: point.price,
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

/** True when the product is Costco-comparable but has no chartable warehouse data. */
export function isCostcoUnavailableOnChart(product: FeedProductView): boolean {
  return product.costcoComparable && !hasCostcoChartData(product);
}

export type UnifiedChartRow = {
  weekStart: string;
  label: string;
  groceryPrice: number;
  groceryPriceMax?: number;
  priceType: string;
  isBaselineFallback: boolean;
  costcoPrice: number | null;
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
  const groceryPoints = getAllPricePoints(product);
  const costcoPoints = getCostcoChartPricePoints(product);
  const weekStarts = groceryPoints.map((point) => point.weekStart);
  const costcoByWeek = new Map<string, number>();

  for (const point of costcoPoints) {
    const week = findGroceryWeekForCostcoDate(point.weekStart, weekStarts);
    if (week != null) {
      costcoByWeek.set(week, point.price);
    }
  }

  return groceryPoints.map((point) => ({
    weekStart: point.weekStart,
    label: point.label ?? formatWeekLabel(point.weekStart),
    groceryPrice: point.price,
    groceryPriceMax: point.priceMax ?? point.price,
    priceType: point.priceType,
    isBaselineFallback: point.isBaselineFallback,
    costcoPrice:
      point.weekStart === "baseline"
        ? null
        : costcoByWeek.get(point.weekStart) ?? null,
  }));
}

export function getCostcoChartRegionLabel(product: FeedProductView): string | null {
  const region = getCostcoRegionForFeed(product.feedId);
  return region ? formatCostcoRegionLabel(region) : null;
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
  const onSale = isProductOnSale(product);
  const discount = getProductSaleDiscountPercent(product);
  const vsCostco = getGroceryVsCostcoPercent(product);

  if (onSale && discount != null) {
    if (discount >= MEANINGFUL_SALE_PCT) {
      return { label: "Great week to buy", tone: "buy" };
    }
    if (discount >= GOOD_DEAL_SALE_PCT) {
      return { label: "Good deal this week", tone: "buy" };
    }
  }

  if (product.costcoComparable && vsCostco != null) {
    if (vsCostco <= 0) {
      return {
        label: `${product.feedLabel} wins this week`,
        tone: "grocery",
      };
    }
    if (vsCostco > COSTCO_WINS_PCT) {
      return { label: "Costco wins on price", tone: "costco" };
    }
    return { label: closeEnoughLabel(product.feedLabel), tone: "close" };
  }

  if (!onSale) {
    return { label: "Wait for a sale", tone: "wait" };
  }

  return { label: "Regular price this week", tone: "neutral" };
}

/** Price line for collapsed family cards — current sale or usual price. */
export function getFamilyUsuallyLabel(product: FeedProductView): string {
  if (product.salePriceRange) {
    const { min, max } = product.salePriceRange;
    if (Math.abs(min - max) < 0.01) {
      return `${formatPrice(min)} each this week`;
    }
    const sale = formatPriceRange(product.salePriceRange);
    return sale ? `${sale} this week` : formatPrice(min);
  }

  const current = getCurrentPrice(product);
  const discount = getDiscountPercent(product);
  if (current != null && discount != null && discount >= GOOD_DEAL_SALE_PCT) {
    return `${formatPrice(current)} this week`;
  }

  if (product.priceRange) {
    const regular = formatPriceRange(product.priceRange);
    if (regular) {
      return `Usually ${regular}`;
    }
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

  if (product.canonicalId === "ritz_crackers_snacks" && product.costcoComparable) {
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

  if (product.canonicalId === "ritz_crackers_snacks" && product.costcoComparable) {
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
  if (!product.costcoComparable || !product.priceComparison) {
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
  locationNote: string | null;
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
  if (!comparison || !product.costcoComparable) {
    return null;
  }

  const costcoUnit =
    comparison.costcoUnitPrice != null
      ? `about $${comparison.costcoUnitPrice.toFixed(2)}/oz`
      : null;
  const groceryUnit =
    comparison.groceryUnitPrice != null
      ? `about $${comparison.groceryUnitPrice.toFixed(2)}/oz`
      : null;
  const packageDesc = comparison.comparisonNote?.trim() ?? "61.6 oz";

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

  return {
    locationNote: getCostcoComparisonLocationNote(product.feedId),
    intro:
      "We compare Costco against the classic Ritz box because that's closest to Costco's big Original Ritz pack.",
    costcoLabel: `Original Ritz, ${packageDesc} (${comparison.costcoStoreLabel ?? "regional warehouse"})`,
    costcoDetail,
    groceryLabel: "Classic Ritz boxes, 12–13.7 oz",
    groceryDetail,
    verdict: `Costco is much cheaper if you just want regular Ritz. ${product.feedLabel} is better if you want smaller boxes or different Ritz styles.`,
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

export type FamilyStatus = "On sale this week" | "Promo deal this week";

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

  const offerText = latestFamilyOfferText(product);
  if (offerText && MULTI_BUY_OFFER_RE.test(offerText)) {
    return "Promo deal this week";
  }
  return "On sale this week";
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
  const name = product.displayName;

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
