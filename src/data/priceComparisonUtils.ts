import type { PriceComparisonView } from "./priceComparisons.generated";
import { PRICE_COMPARISONS_BY_KEY } from "./priceComparisons.generated";
import { getCostcoRegionForFeed } from "./costcoRegions";
import type { CostcoPricePoint } from "./costcoPriceHistory.generated";
import { COSTCO_PRICE_HISTORY } from "./costcoPriceHistory.generated";

export const GROCERY_FEED_IDS = new Set([
  "safeway_bay_area",
  "vons_albertsons_socal",
]);

export function comparisonKey(canonicalId: string, feedId: string): string {
  return `${canonicalId}:${feedId}`;
}

export function getFallbackComparison(
  canonicalId: string,
  feedId: string,
): PriceComparisonView | null {
  if (!GROCERY_FEED_IDS.has(feedId)) {
    return null;
  }
  return PRICE_COMPARISONS_BY_KEY[comparisonKey(canonicalId, feedId)] ?? null;
}

/** Region-scoped Costco price history for one canonical product on the active feed. */
export function getCostcoPriceHistory(
  canonicalId: string,
  feedId: string,
): CostcoPricePoint[] {
  const region = getCostcoRegionForFeed(feedId);
  if (!region) {
    return [];
  }
  return COSTCO_PRICE_HISTORY[canonicalId]?.[region] ?? [];
}

export function formatComparisonUnit(unit: string | null): string {
  if (!unit) return "unit";
  const labels: Record<string, string> = {
    oz: "oz",
    lb: "lb",
    each: "item",
    bar: "bar",
    bag: "bag",
    can: "can",
    egg: "egg",
    fl_oz: "fl oz",
  };
  return labels[unit] ?? unit;
}

function formatUnitPrice(price: number | null, unit: string): string | null {
  if (price == null) return null;
  return `$${price.toFixed(2)}/${unit}`;
}

function formatMoney(price: number | null): string | null {
  if (price == null) return null;
  return `$${price.toFixed(2)}`;
}

function titleCaseWarehouseSign(sign: string): string {
  return sign
    .split(/\s+/)
    .map((word) => {
      if (/^\d/.test(word)) {
        return word.toLowerCase();
      }
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(" ");
}

/** Human-readable Costco warehouse item label from the matched item sign. */
export function formatCostcoItemLabel(
  comparison: PriceComparisonView,
): string | null {
  const sign = comparison.costcoPackageDescription?.trim();
  if (!sign) {
    return null;
  }
  return titleCaseWarehouseSign(sign);
}

/** Package size for a matched Costco item, e.g. "30 oz" or "6 count". */
export function formatCostcoPackageSize(
  comparison: PriceComparisonView,
): string | null {
  const count = comparison.costcoUnitCount;
  const unit = comparison.costcoUnitType;
  if (count == null || !unit) {
    return null;
  }

  const unitLabel = formatComparisonUnit(unit);
  const rounded = Math.round(count * 100) / 100;
  const countLabel =
    rounded === Math.round(rounded)
      ? String(Math.round(rounded))
      : String(rounded);

  if (unit === "each") {
    return `${countLabel} count`;
  }
  return `${countLabel} ${unitLabel}`;
}

/** One-line Costco reference: item, size, and shelf price. */
export function formatCostcoReferenceLine(
  comparison: PriceComparisonView,
): string | null {
  const label = formatCostcoItemLabel(comparison);
  const size = formatCostcoPackageSize(comparison);
  const price = formatMoney(comparison.costcoPrice);

  if (!label && !size && !price) {
    return null;
  }

  const nameWithSize =
    label ??
    (size ? `Costco item, ${size}` : null);
  if (nameWithSize && price) {
    return `${nameWithSize} · ${price}`;
  }
  return nameWithSize ?? price;
}

export type ComparisonBadgeContent = {
  label: string;
  tone: "grocery" | "costco" | "neutral" | "muted";
};

function compactBadgeLabel(
  headline: string,
  detail: string | null,
): string {
  if (detail) {
    return `${headline} · ${detail}`;
  }
  return headline;
}

export type ProductCostcoComparisonDetails = {
  referenceLine: string;
  unitPriceLine: string | null;
  verdictLine: string | null;
};

/** True when grocery-vs-Costco comparison data is complete enough to show in the UI. */
export function hasMeaningfulCostcoComparison(
  comparison: PriceComparisonView | null | undefined,
): boolean {
  if (!comparison) {
    return false;
  }
  if (comparison.comparisonStatus !== "comparable") {
    return false;
  }
  if (
    comparison.winner === "grocery_only" ||
    comparison.winner === "unknown"
  ) {
    return false;
  }
  if (comparison.costcoUnitPrice == null && comparison.costcoPrice == null) {
    return false;
  }
  return true;
}

function buildWinnerDetail(
  comparison: PriceComparisonView,
  activeGroceryLabel: string,
  winner: "grocery" | "costco",
): string | null {
  const unit = formatComparisonUnit(
    comparison.groceryUnitType ?? comparison.costcoUnitType,
  );
  const pct = comparison.savingsPercent;
  const groceryFmt = formatUnitPrice(comparison.groceryUnitPrice, unit);
  const costcoFmt = formatUnitPrice(comparison.costcoUnitPrice, unit);

  if (winner === "grocery") {
    if (pct != null && pct > 0) {
      return `${Math.round(pct)}% cheaper than Costco per ${unit}`;
    }
    if (groceryFmt && costcoFmt) {
      return `${groceryFmt} vs Costco ${costcoFmt}`;
    }
    return null;
  }

  if (pct != null && pct > 0) {
    return `Costco is ${Math.round(pct)}% cheaper per ${unit}`;
  }
  if (costcoFmt && groceryFmt) {
    return `${costcoFmt} vs ${activeGroceryLabel} ${groceryFmt}`;
  }
  return null;
}

/** Expanded card copy for the specific Costco item used in the comparison. */
export function getProductCostcoComparisonDetails(
  comparison: PriceComparisonView,
  activeGroceryLabel: string,
): ProductCostcoComparisonDetails | null {
  if (!hasMeaningfulCostcoComparison(comparison)) {
    return null;
  }

  const referenceLine = formatCostcoReferenceLine(comparison);
  if (!referenceLine) {
    return null;
  }

  const unit = formatComparisonUnit(
    comparison.groceryUnitType ?? comparison.costcoUnitType,
  );
  const costcoUnitPrice = formatUnitPrice(comparison.costcoUnitPrice, unit);
  const unitPriceLine = costcoUnitPrice
    ? `${costcoUnitPrice} at Costco`
    : null;

  let verdictLine: string | null = null;
  if (comparison.winner === "tie") {
    verdictLine = `Within 3% per ${unit}`;
  } else if (comparison.winner === "grocery") {
    verdictLine = buildWinnerDetail(comparison, activeGroceryLabel, "grocery");
  } else if (comparison.winner === "costco") {
    verdictLine = buildWinnerDetail(comparison, activeGroceryLabel, "costco");
  }

  return {
    referenceLine: `Compared to ${referenceLine}`,
    unitPriceLine,
    verdictLine,
  };
}

/** Shopper-facing badge copy scoped to the active grocery feed vs Costco. */
export function getComparisonBadgeContent(
  comparison: PriceComparisonView,
  activeFeedId: string,
  activeGroceryLabel: string,
): ComparisonBadgeContent | null {
  if (comparison.groceryFeedId !== activeFeedId) {
    return null;
  }

  if (!hasMeaningfulCostcoComparison(comparison)) {
    return null;
  }

  const unit = formatComparisonUnit(
    comparison.groceryUnitType ?? comparison.costcoUnitType,
  );

  if (comparison.winner === "tie") {
    return {
      label: compactBadgeLabel("Too close to call", `within 3% per ${unit}`),
      tone: "neutral",
    };
  }

  if (comparison.winner === "grocery") {
    return {
      label: compactBadgeLabel(
        `${activeGroceryLabel} wins`,
        buildWinnerDetail(comparison, activeGroceryLabel, "grocery"),
      ),
      tone: "grocery",
    };
  }

  if (comparison.winner === "costco") {
    return {
      label: compactBadgeLabel(
        "Costco wins",
        buildWinnerDetail(comparison, activeGroceryLabel, "costco"),
      ),
      tone: "costco",
    };
  }

  return null;
}
