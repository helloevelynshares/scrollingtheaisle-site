import {
  buildSafewayYamlProducts,
  buildVonsYamlProducts,
} from "../data/yamlFamilyProducts";
import { CANONICAL_TRACKER_FAMILIES } from "../data/canonicalTrackerFamilies";
import { getPriceFeed } from "../data/priceFeeds";
import {
  buildEmptyFeedProducts,
} from "../data/priceTrackerFallback";
import type {
  FeedProductMatch,
  FeedProductView,
  WeeklyPrice,
  WeeklyPriceObservation,
} from "../data/priceTrackerTypes";
import type { PriceComparisonView } from "../data/priceComparisonTypes";
import { getFallbackComparison, getCostcoPriceHistory } from "../data/priceComparisonUtils";
import {
  hasChartableData,
  INFERRED_BASELINE_SOURCE,
  inferBaselineFromWeeklyPrices,
} from "../data/priceTrackerUtils";
import { getSupabase } from "./supabase";

const SAFEWAY_FEED_ID = "safeway_bay_area";
const VONS_FEED_ID = "vons_albertsons_socal";
const COSTCO_FEED_IDS = new Set(["costco_sf", "costco_oc"]);

type DbCanonicalProduct = {
  id: string;
  display_name: string;
  product_family: string;
  size_label: string | null;
  costco_comparable: boolean;
  confidence: string;
  sort_order: number;
};

type DbFeedProductMatch = {
  canonical_product_id: string;
  feed_id: string;
  retailer_product_id: string | null;
  upc: string | null;
  retailer_product_name: string | null;
  size: string | null;
  baseline_price: number;
  baseline_source: string | null;
};

type DbPriceComparison = {
  canonical_product_id: string;
  grocery_feed_id: string;
  grocery_store_label: string;
  grocery_price: number | null;
  grocery_package_description: string | null;
  grocery_unit_type: string | null;
  grocery_unit_count: number | null;
  grocery_unit_price: number | null;
  costco_region_id: string | null;
  costco_store_label: string | null;
  costco_price: number | null;
  costco_package_description: string | null;
  costco_unit_type: string | null;
  costco_unit_count: number | null;
  costco_unit_price: number | null;
  winner: string;
  savings_amount: number | null;
  savings_percent: number | null;
  comparison_status: string;
  comparison_note: string | null;
};

type DbWeeklyObservation = {
  canonical_product_id: string;
  feed_id: string;
  week_start: string;
  week_end: string | null;
  ad_price: number | null;
  effective_price: number;
  match_confidence: string | null;
  price_type: string;
  is_baseline_fallback: boolean;
  source_label: string | null;
  offer_text: string | null;
};

/**
 * Fetch canonical_products (shared across feeds) and weekly_price_observations
 * for the active feed_id, then merge client-side by canonical_product_id.
 *
 * feed_product_matches maps each canonical item to retailer-specific SKUs per feed.
 */
export async function fetchFeedProducts(
  feedId: string,
): Promise<FeedProductView[]> {
  const feed = getPriceFeed(feedId);
  if (!feed) {
    return [];
  }

  // YAML tracker families: static generated prices (Safeway / Vons grocery tabs).
  if (feedId === SAFEWAY_FEED_ID || feedId === VONS_FEED_ID) {
    return fallbackForFeed(feedId);
  }

  try {
    const supabase = getSupabase();

    const [canonicalResult, matchResult, observationResult, comparisonResult] =
      await Promise.all([
      supabase
        .from("canonical_products")
        .select(
          "id, display_name, product_family, size_label, costco_comparable, confidence, sort_order",
        )
        .eq("is_active", true)
        .order("sort_order"),
      supabase
        .from("feed_product_matches")
        .select(
          "canonical_product_id, feed_id, retailer_product_id, upc, retailer_product_name, size, baseline_price, baseline_source",
        )
        .eq("feed_id", feedId),
      supabase
        .from("weekly_price_observations")
        .select(
          "canonical_product_id, feed_id, week_start, week_end, ad_price, effective_price, match_confidence, price_type, is_baseline_fallback, source_label, offer_text",
        )
        .eq("feed_id", feedId)
        .order("week_start"),
      supabase
        .from("price_comparisons")
        .select(
          "canonical_product_id, grocery_feed_id, grocery_store_label, grocery_price, grocery_unit_type, grocery_unit_price, costco_region_id, costco_store_label, costco_price, costco_unit_type, costco_unit_price, winner, savings_amount, savings_percent, comparison_status, comparison_note",
        )
        .eq("grocery_feed_id", feedId),
    ]);

    if (
      canonicalResult.error ||
      matchResult.error ||
      observationResult.error
    ) {
      return fallbackForFeed(feedId);
    }

    const comparisonLoadFailed = Boolean(comparisonResult.error);

    const canonicalRows = canonicalResult.data as DbCanonicalProduct[] | null;
    if (!canonicalRows?.length) {
      return fallbackForFeed(feedId);
    }

    const matches = (matchResult.data ?? []) as DbFeedProductMatch[];
    const observations = (observationResult.data ?? []) as DbWeeklyObservation[];

    const matchByCanonical = new Map(
      matches.map((row) => [row.canonical_product_id, row]),
    );
    const observationsByCanonical = groupObservations(observations);
    const comparisonsByCanonical = groupComparisons(
      (comparisonResult.data ?? []) as DbPriceComparison[],
      comparisonLoadFailed,
      feedId,
    );

    const merged = canonicalRows.map((row) =>
      mergeCanonicalWithFeed(
        row,
        feed,
        matchByCanonical.get(row.id),
        observationsByCanonical.get(row.id) ?? [],
        comparisonsByCanonical.get(row.id) ?? null,
      ),
    );

    if (feedId === SAFEWAY_FEED_ID && merged.every((p) => !p.hasFeedData)) {
      return buildSafewayYamlProducts();
    }

    if (feedId === VONS_FEED_ID && merged.every((p) => !p.hasFeedData)) {
      return buildVonsYamlProducts();
    }

    if (COSTCO_FEED_IDS.has(feedId) && merged.every((p) => !p.hasFeedData)) {
      return buildEmptyFeedProducts(feedId);
    }

    return enrichSparseProductsFromFallback(merged, feedId);
  } catch {
    return fallbackForFeed(feedId);
  }
}

function fallbackForFeed(feedId: string): FeedProductView[] {
  if (feedId === SAFEWAY_FEED_ID) {
    return buildSafewayYamlProducts();
  }
  if (feedId === VONS_FEED_ID) {
    return buildVonsYamlProducts();
  }
  if (COSTCO_FEED_IDS.has(feedId)) {
    return buildEmptyFeedProducts(feedId);
  }
  return buildEmptyFeedProducts(feedId);
}

function enrichSparseProductsFromFallback(
  products: FeedProductView[],
  feedId: string,
): FeedProductView[] {
  if (feedId !== SAFEWAY_FEED_ID && feedId !== VONS_FEED_ID) {
    return products;
  }

  const fallbackById = new Map(
    (feedId === SAFEWAY_FEED_ID
      ? buildSafewayYamlProducts()
      : buildVonsYamlProducts()
    ).map((product) => [product.canonicalId, product]),
  );

  return products.map((product) => {
    if (hasChartableData(product)) {
      return product;
    }
    const fallback = fallbackById.get(product.canonicalId);
    return fallback && hasChartableData(fallback) ? fallback : product;
  });
}

function groupObservations(
  rows: DbWeeklyObservation[],
): Map<string, WeeklyPriceObservation[]> {
  const map = new Map<string, WeeklyPriceObservation[]>();
  for (const row of rows) {
    const list = map.get(row.canonical_product_id) ?? [];
    list.push({
      canonicalProductId: row.canonical_product_id,
      feedId: row.feed_id,
      weekStart: row.week_start,
      weekEnd: row.week_end,
      adPrice: row.ad_price,
      effectivePrice: row.effective_price,
      matchConfidence: row.match_confidence as WeeklyPriceObservation["matchConfidence"],
      priceType: row.price_type as WeeklyPriceObservation["priceType"],
      isBaselineFallback: row.is_baseline_fallback,
      sourceLabel: row.source_label,
      offerText: row.offer_text,
    });
    map.set(row.canonical_product_id, list);
  }
  return map;
}

function groupComparisons(
  rows: DbPriceComparison[],
  loadFailed: boolean,
  feedId: string,
): Map<string, PriceComparisonView | null> {
  const map = new Map<string, PriceComparisonView | null>();
  if (loadFailed) {
    return map;
  }
  for (const row of rows) {
    map.set(row.canonical_product_id, mapComparisonRow(row));
  }
  return map;
}

function mapComparisonRow(row: DbPriceComparison): PriceComparisonView {
  return {
    canonicalProductId: row.canonical_product_id,
    groceryFeedId: row.grocery_feed_id,
    groceryStoreLabel: row.grocery_store_label,
    groceryPrice: row.grocery_price,
    groceryPackageDescription: row.grocery_package_description,
    groceryUnitType: row.grocery_unit_type,
    groceryUnitCount: row.grocery_unit_count,
    groceryUnitPrice: row.grocery_unit_price,
    costcoRegionId: row.costco_region_id,
    costcoStoreLabel: row.costco_store_label,
    costcoPrice: row.costco_price,
    costcoPackageDescription: row.costco_package_description,
    costcoUnitType: row.costco_unit_type,
    costcoUnitCount: row.costco_unit_count,
    costcoUnitPrice: row.costco_unit_price,
    winner: row.winner as PriceComparisonView["winner"],
    savingsAmount: row.savings_amount,
    savingsPercent: row.savings_percent,
    comparisonStatus: row.comparison_status as PriceComparisonView["comparisonStatus"],
    comparisonNote: row.comparison_note,
  };
}

function mergeCanonicalWithFeed(
  canonical: DbCanonicalProduct,
  feed: { id: string; label: string; regionLabel: string },
  match: DbFeedProductMatch | undefined,
  observations: WeeklyPriceObservation[],
  comparison: PriceComparisonView | null | undefined,
): FeedProductView {
  const hasMatch = Boolean(match);
  const weeklyPrices: WeeklyPrice[] = observations.map((obs) => ({
    weekStart: obs.weekStart,
    price: obs.effectivePrice,
    adPrice: obs.adPrice,
    matchConfidence: obs.matchConfidence,
    priceType: obs.priceType,
    isBaselineFallback: obs.isBaselineFallback,
    sourceLabel: obs.sourceLabel ?? undefined,
    offerText: obs.offerText ?? undefined,
  }));

  const hasAdMatches = weeklyPrices.some(
    (week) => week.adPrice != null && week.matchConfidence !== "low",
  );
  const inferredBaseline = inferBaselineFromWeeklyPrices(weeklyPrices);
  const effectiveBaseline = match?.baseline_price ?? inferredBaseline;

  return {
    canonicalId: canonical.id,
    displayName: canonical.display_name,
    productFamily: canonical.product_family,
    sizeLabel: canonical.size_label ?? undefined,
    costcoComparable: canonical.costco_comparable,
    confidence: canonical.confidence as FeedProductView["confidence"],
    feedId: feed.id,
    feedLabel: feed.label,
    regionLabel: feed.regionLabel,
    hasFeedData:
      (hasMatch && match!.baseline_price != null) || hasAdMatches,
    baselinePrice: effectiveBaseline,
    baselineSource:
      match?.baseline_source ??
      (inferredBaseline != null ? INFERRED_BASELINE_SOURCE : null),
    weeklyPrices,
    priceComparison:
      feed.storeGroup !== "costco"
        ? (comparison ?? getFallbackComparison(canonical.id, feed.id))
        : null,
    costcoPriceHistory:
      feed.storeGroup !== "costco"
        ? getCostcoPriceHistory(canonical.id, feed.id)
        : undefined,
  };
}

/** Local tracker family list when Supabase canonical_products is unavailable. */
export function getLocalCanonicalProducts() {
  return CANONICAL_TRACKER_FAMILIES;
}

export type { FeedProductMatch, FeedProductView };
