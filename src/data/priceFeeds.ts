/** Regional/store feed metadata. feed_id selects which price observations to display. */
export type PriceFeed = {
  id: string;
  label: string;
  regionLabel: string;
  storeGroup: string;
  stores: string[];
};

/** Fallback feeds when Supabase price_feeds table is empty or unreachable. */
export const PRICE_FEEDS: PriceFeed[] = [
  {
    id: "safeway_bay_area",
    label: "Safeway",
    regionLabel: "Bay Area",
    storeGroup: "safeway",
    stores: ["Safeway"],
  },
  {
    id: "vons_albertsons_socal",
    label: "Vons / Albertsons",
    regionLabel: "SoCal",
    storeGroup: "vons_albertsons",
    stores: ["Vons", "Albertsons"],
  },
];

export const DEFAULT_FEED_ID = PRICE_FEEDS[0].id;

export function getPriceFeed(feedId: string): PriceFeed | undefined {
  return PRICE_FEEDS.find((feed) => feed.id === feedId);
}
