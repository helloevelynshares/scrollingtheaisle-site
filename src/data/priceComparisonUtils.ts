import type { PriceComparisonView } from "../data/priceComparisons.generated";
import { PRICE_COMPARISONS_BY_KEY } from "../data/priceComparisons.generated";
import {
  getCostcoComparisonLocationNote,
  getCostcoRegionForFeed,
} from "./costcoRegions";
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

export type ComparisonBadgeContent = {
  title: string;
  detail: string | null;
  locationNote: string | null;
  tone: "grocery" | "costco" | "neutral" | "muted";
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
      title: "Too close to call",
      detail: `Within 3% per ${unit}`,
      locationNote: getCostcoComparisonLocationNote(activeFeedId),
      tone: "neutral",
    };
  }

  if (comparison.winner === "grocery") {
    return {
      title: `Via ${activeGroceryLabel}`,
      detail: buildWinnerDetail(comparison, activeGroceryLabel, "grocery"),
      locationNote: getCostcoComparisonLocationNote(activeFeedId),
      tone: "grocery",
    };
  }

  if (comparison.winner === "costco") {
    return {
      title: "Via Costco",
      detail: buildWinnerDetail(comparison, activeGroceryLabel, "costco"),
      locationNote: getCostcoComparisonLocationNote(activeFeedId),
      tone: "costco",
    };
  }

  return null;
}
