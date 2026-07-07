import type { MatchConfidence } from "./weeklyAdPrices.generated";
import type { CanonicalProduct } from "./canonicalProducts";
import type { PriceComparisonView } from "./priceComparisonTypes";
import type { CostcoPricePoint } from "./costcoPriceHistory.generated";
import type { TrackerType } from "./trackerFamilies";
import type { FamilyComparisonBadge } from "./trackerFamilyUtils";

export type { MatchConfidence, CanonicalProduct, TrackerType };

/** Weekly slot for a single feed + canonical product. */
export type WeeklyPrice = {
  weekStart: string;
  price: number;
  adPrice: number | null;
  /** Upper bound when a deal family spans multiple formats in one week. */
  priceMax?: number | null;
  matchConfidence: MatchConfidence | null;
  priceType: "baseline" | "weekly_ad";
  sourceLabel?: string;
  offerText?: string;
  isBaselineFallback: boolean;
  /** e.g. "friday_only", "short_term_dip" — from split_offer_items availability_type_guess */
  availabilityType?: string | null;
  /** Promotional copy from split_offer_items promo_text, e.g. "3 for $5 Friday July 3rd" */
  promoNote?: string | null;
};

export type FamilyMemberPriceView = {
  memberId: string;
  label: string;
  sizeLabel: string;
  baselinePrice: number;
  currentPrice: number | null;
  weeklyPrices: WeeklyPrice[];
};

/**
 * View model for one canonical product under an active feed.
 * feed_id determines which regional/store price data is shown.
 */
export type FeedProductView = {
  canonicalId: string;
  displayName: string;
  productFamily: string;
  sizeLabel?: string;
  costcoComparable: boolean;
  confidence: "high" | "medium" | "low";
  feedId: string;
  feedLabel: string;
  regionLabel: string;
  /** False when this feed has no baseline/match yet (e.g. Vons coming soon). */
  hasFeedData: boolean;
  baselinePrice: number | null;
  baselineSource: string | null;
  weeklyPrices: WeeklyPrice[];
  /** Grocery vs Costco per-unit comparison for this feed, when available. */
  priceComparison?: PriceComparisonView | null;
  /** Regional Costco warehouse price history for chart overlays (never mixed across regions). */
  costcoPriceHistory?: CostcoPricePoint[];
  /** Defaults to single_sku for the original 18 canonical products. */
  trackerType?: TrackerType;
  subtitle?: string;
  category?: string;
  familyMembers?: FamilyMemberPriceView[];
  priceRange?: { min: number; max: number } | null;
  salePriceRange?: { min: number; max: number } | null;
  chartMode?: "single" | "range";
  /** Curated family comparison copy (e.g. Ritz vs Costco). */
  familyComparisonBadge?: FamilyComparisonBadge | null;
  /** YAML homepage section (migration). */
  homepageSection?: string;
  /** YAML display order within section. */
  displayOrder?: number;
};

/** feed_product_matches row — maps canonical item to a retailer SKU for price fetching. */
export type FeedProductMatch = {
  canonicalProductId: string;
  feedId: string;
  retailerProductId: string | null;
  upc: string | null;
  retailerProductName: string | null;
  size: string | null;
  baselinePrice: number;
  baselineSource: string | null;
};

/** weekly_price_observations row — one week of prices for canonical + feed. */
export type WeeklyPriceObservation = {
  canonicalProductId: string;
  feedId: string;
  weekStart: string;
  weekEnd: string | null;
  adPrice: number | null;
  effectivePrice: number;
  matchConfidence: MatchConfidence | null;
  priceType: "baseline" | "weekly_ad";
  isBaselineFallback: boolean;
  sourceLabel: string | null;
  offerText: string | null;
};
