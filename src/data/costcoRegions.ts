/** Costco warehouse keys — normalized from CSV filename slugs (san-francisco → san_francisco). */
export type CostcoRegion = "san_francisco" | "tustin" | "seattle";

/** Grocery tracker tabs that compare against a regional Costco warehouse. */
export type GroceryTrackerRegion = "safeway" | "vons-albertsons";

export const COSTCO_REGIONS: readonly CostcoRegion[] = [
  "san_francisco",
  "tustin",
  "seattle",
] as const;

/** Maps an active grocery tracker to its paired Costco warehouse. No cross-warehouse fallback. */
export const groceryTrackerToCostcoRegion: Record<
  GroceryTrackerRegion,
  CostcoRegion
> = {
  safeway: "san_francisco",
  "vons-albertsons": "tustin",
};

/** Maps price-feed ids to grocery tracker regions (Seattle has no grocery tab yet). */
export const feedIdToGroceryTrackerRegion: Partial<
  Record<string, GroceryTrackerRegion>
> = {
  safeway_bay_area: "safeway",
  vons_albertsons_socal: "vons-albertsons",
};

/** Maps Costco price-feed ids to warehouse region keys. */
export const costcoFeedIdToRegion: Record<string, CostcoRegion> = {
  costco_sf: "san_francisco",
  costco_oc: "tustin",
};

export function getCostcoRegionForFeed(feedId: string): CostcoRegion | null {
  const groceryRegion = feedIdToGroceryTrackerRegion[feedId];
  if (groceryRegion) {
    return groceryTrackerToCostcoRegion[groceryRegion];
  }
  return costcoFeedIdToRegion[feedId] ?? null;
}

/** Shopper-facing note shown once per tracker tab (not on every product card). */
export function getCostcoComparisonPageNote(feedId: string): string | null {
  const region = getCostcoRegionForFeed(feedId);
  if (region === "san_francisco") {
    return "All Costco comparisons on this tab use San Francisco warehouse pricing.";
  }
  if (region === "tustin") {
    return "All Costco comparisons on this tab use Tustin warehouse pricing.";
  }
  return null;
}

/** Display label for a Costco warehouse region key. */
export function formatCostcoRegionLabel(region: CostcoRegion): string {
  switch (region) {
    case "san_francisco":
      return "San Francisco";
    case "tustin":
      return "Tustin";
    case "seattle":
      return "Seattle";
  }
}
