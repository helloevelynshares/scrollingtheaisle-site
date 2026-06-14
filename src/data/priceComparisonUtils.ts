import type { PriceComparisonView } from "../data/priceComparisons.generated";
import { PRICE_COMPARISONS_BY_KEY } from "../data/priceComparisons.generated";

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

export type ComparisonBadgeContent = {
  title: string;
  detail: string | null;
  tone: "grocery" | "costco" | "neutral" | "muted";
};

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

/** Shopper-facing badge copy scoped to the active grocery feed vs Costco. */
export function getComparisonBadgeContent(
  comparison: PriceComparisonView,
  activeFeedId: string,
  activeGroceryLabel: string,
): ComparisonBadgeContent | null {
  if (comparison.groceryFeedId !== activeFeedId) {
    return null;
  }

  const unit = formatComparisonUnit(
    comparison.groceryUnitType ?? comparison.costcoUnitType,
  );

  if (comparison.winner === "unknown") {
    return null;
  }

  if (
    comparison.comparisonStatus === "missing_grocery_price" ||
    comparison.comparisonStatus === "missing_costco_price" ||
    comparison.comparisonStatus === "unit_mismatch" ||
    comparison.comparisonStatus === "needs_review"
  ) {
    return {
      title: "Comparison unavailable",
      detail: null,
      tone: "muted",
    };
  }

  if (
    comparison.comparisonStatus === "not_sold_at_costco" ||
    comparison.winner === "grocery_only"
  ) {
    return {
      title: "Not found at Costco",
      detail: `Best tracked price is via ${activeGroceryLabel}`,
      tone: "grocery",
    };
  }

  if (comparison.winner === "tie") {
    return {
      title: "Too close to call",
      detail: `Within 3% per ${unit}`,
      tone: "neutral",
    };
  }

  if (comparison.winner === "grocery") {
    return {
      title: `Via ${activeGroceryLabel}`,
      detail: buildWinnerDetail(comparison, activeGroceryLabel, "grocery"),
      tone: "grocery",
    };
  }

  if (comparison.winner === "costco") {
    return {
      title: "Via Costco",
      detail: buildWinnerDetail(comparison, activeGroceryLabel, "costco"),
      tone: "costco",
    };
  }

  return null;
}
