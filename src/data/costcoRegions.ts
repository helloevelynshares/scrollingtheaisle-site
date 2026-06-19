/** Costco warehouse region slugs derived from CSV filenames. */
export type CostcoRegion = "san-francisco" | "tustin" | "seattle";

/** Grocery tracker tabs that compare against a regional Costco warehouse. */
export type GroceryTrackerRegion = "safeway" | "vons-albertsons";

export const COSTCO_REGIONS: readonly CostcoRegion[] = [
  "san-francisco",
  "tustin",
  "seattle",
] as const;

/** Maps an active grocery tracker to its paired Costco warehouse region. */
export const groceryTrackerToCostcoRegion: Record<
  GroceryTrackerRegion,
  CostcoRegion
> = {
  safeway: "san-francisco",
  "vons-albertsons": "tustin",
};

/** Maps price-feed ids to grocery tracker regions (Seattle has no grocery tab yet). */
export const feedIdToGroceryTrackerRegion: Partial<
  Record<string, GroceryTrackerRegion>
> = {
  safeway_bay_area: "safeway",
  vons_albertsons_socal: "vons-albertsons",
};

/** Maps Costco price-feed ids to warehouse region slugs. */
export const costcoFeedIdToRegion: Record<string, CostcoRegion> = {
  costco_sf: "san-francisco",
  costco_oc: "tustin",
};

export function getCostcoRegionForFeed(feedId: string): CostcoRegion | null {
  const groceryRegion = feedIdToGroceryTrackerRegion[feedId];
  if (groceryRegion) {
    return groceryTrackerToCostcoRegion[groceryRegion];
  }
  return costcoFeedIdToRegion[feedId] ?? null;
}

/** Shopper-facing note for comparison badges and expanded details. */
export function getCostcoComparisonLocationNote(feedId: string): string | null {
  const region = getCostcoRegionForFeed(feedId);
  if (region === "san-francisco") {
    return "Costco comparison uses San Francisco Costco pricing.";
  }
  if (region === "tustin") {
    return "Costco comparison uses Tustin Costco pricing.";
  }
  return null;
}

/** Display label for a Costco warehouse region slug. */
export function formatCostcoRegionLabel(region: CostcoRegion): string {
  switch (region) {
    case "san-francisco":
      return "San Francisco";
    case "tustin":
      return "Tustin";
    case "seattle":
      return "Seattle";
  }
}
