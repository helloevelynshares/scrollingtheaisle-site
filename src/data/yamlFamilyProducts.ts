import {
  CANONICAL_TRACKER_FAMILIES,
  LEGACY_CANONICAL_TO_FAMILY,
} from "./canonicalTrackerFamilies.generated";
import { getPriceFeed } from "./priceFeeds";
import { getFallbackComparison, getCostcoPriceHistory } from "./priceComparisonUtils";
import type { FeedProductView, WeeklyPrice } from "./priceTrackerTypes";
import {
  INFERRED_BASELINE_SOURCE,
  inferBaselineFromWeeklyPrices,
} from "./priceTrackerUtils";
import { SAFEWAY_BASELINES } from "./priceTrackerFallback";
import { VONS_BASELINE_BY_CANONICAL } from "./vonsBaseline.generated";
import { isPreviewWeek } from "./weeklyAdPreview";
import {
  WEEKLY_AD_PRICES,
  WEEKLY_AD_WEEKS,
  type GeneratedWeeklyAdPrice,
} from "./weeklyAdPrices.generated";
import {
  VONS_WEEKLY_AD_PRICES,
  VONS_WEEKLY_AD_WEEKS,
} from "./vonsWeeklyAdPrices.generated";

const SAFEWAY_FEED_ID = "safeway_bay_area";
const VONS_FEED_ID = "vons_albertsons_socal";

/**
 * Legacy eggs_18_count baselines are package totals (e.g. Nellie's 18-count
 * $10.99). When still 18-count and ≥ $5, scale to $/dozen. Lucerne 12-count
 * shelf (~$3.99) is already per dozen and left unchanged.
 */
export function normalizeEggsBaselineToDozen(
  legacyId: string,
  price: number,
  productName?: string,
): number {
  if (legacyId !== "eggs_18_count") {
    return price;
  }
  const name = (productName || "").toLowerCase();
  const looksLike18Pack =
    /\b18\b/.test(name) || name.includes("18 count") || name.includes("18-count");
  if (looksLike18Pack && price >= 5) {
    return Math.round(price * (12 / 18) * 100) / 100;
  }
  return price;
}

function baselineForFamily(
  familyId: string,
  feedId: string,
): { price: number; source: string } | null {
  const legacyIds = Object.entries(LEGACY_CANONICAL_TO_FAMILY)
    .filter(([, target]) => target === familyId)
    .map(([legacy]) => legacy);

  for (const legacyId of legacyIds) {
    if (feedId === SAFEWAY_FEED_ID) {
      const entry = SAFEWAY_BASELINES[legacyId];
      if (entry) {
        const price = normalizeEggsBaselineToDozen(
          legacyId,
          entry.price,
          entry.retailerProductName,
        );
        return {
          price,
          source:
            price !== entry.price
              ? `${entry.source} (scaled to dozen from 18-count)`
              : entry.source,
        };
      }
    }
    if (feedId === VONS_FEED_ID) {
      const entry = VONS_BASELINE_BY_CANONICAL[legacyId];
      if (entry) {
        const price = normalizeEggsBaselineToDozen(
          legacyId,
          entry.baselinePrice,
          entry.retailerProductName,
        );
        return {
          price,
          source:
            price !== entry.baselinePrice
              ? `${entry.baselineSource} (scaled to dozen from 18-count)`
              : entry.baselineSource,
        };
      }
    }
  }

  if (feedId === SAFEWAY_FEED_ID && SAFEWAY_BASELINES[familyId]) {
    return SAFEWAY_BASELINES[familyId];
  }
  if (feedId === VONS_FEED_ID && VONS_BASELINE_BY_CANONICAL[familyId]) {
    const entry = VONS_BASELINE_BY_CANONICAL[familyId];
    return { price: entry.baselinePrice, source: entry.baselineSource };
  }

  return null;
}

function effectiveWeeklyPrice(
  baselinePrice: number | null,
  entry: GeneratedWeeklyAdPrice | undefined,
  sourceLabel: string,
  weekStart: string,
  weekEnd: string,
): WeeklyPrice {
  const adPrice = entry?.price ?? null;
  const matchConfidence = entry?.confidence ?? null;
  const useAd =
    adPrice != null && matchConfidence != null && matchConfidence !== "low";
  const fallbackPrice = baselinePrice ?? adPrice ?? 0;

  return {
    weekStart,
    weekEnd,
    isPreviewWeek: isPreviewWeek(weekStart),
    price: useAd ? adPrice : fallbackPrice,
    adPrice,
    matchConfidence,
    priceType: useAd ? "weekly_ad" : "baseline",
    offerText: entry?.offerText ?? undefined,
    isBaselineFallback: !useAd,
    sourceLabel,
    availabilityType: entry?.availabilityType ?? undefined,
    promoNote: entry?.promoNote ?? undefined,
  };
}

function comparisonIdForFamily(familyId: string): string {
  const legacy = CANONICAL_TRACKER_FAMILIES.find((family) =>
    family.legacyCanonicalIds.length > 0 && family.id === familyId,
  );
  if (legacy?.legacyCanonicalIds[0]) {
    return legacy.legacyCanonicalIds[0];
  }
  return familyId;
}

export function buildYamlFamilyFeedProducts(feedId: string): FeedProductView[] {
  const feed = getPriceFeed(feedId);
  if (!feed) {
    return [];
  }

  const weeks =
    feedId === VONS_FEED_ID ? VONS_WEEKLY_AD_WEEKS : WEEKLY_AD_WEEKS;
  const pricesByFamily =
    feedId === VONS_FEED_ID ? VONS_WEEKLY_AD_PRICES : WEEKLY_AD_PRICES;

  return CANONICAL_TRACKER_FAMILIES.map((family) => {
    const baseline = baselineForFamily(family.id, feedId);
    const byWeek = pricesByFamily[family.id] ?? {};

    const weeklyPrices: WeeklyPrice[] = weeks.map((week) =>
      effectiveWeeklyPrice(
        baseline?.price ?? null,
        byWeek[week.weekStart],
        `${week.sourceLabel} · ${week.sourceFile}`,
        week.weekStart,
        week.weekEnd,
      ),
    );

    const hasAdMatches = weeklyPrices.some(
      (week) => week.adPrice != null && week.matchConfidence !== "low",
    );
    const inferredBaseline = inferBaselineFromWeeklyPrices(weeklyPrices);
    const effectiveBaseline = baseline?.price ?? inferredBaseline;

    const comparisonKey = comparisonIdForFamily(family.id);

    return {
      canonicalId: family.id,
      displayName: family.displayName,
      productFamily: family.id,
      sizeLabel: family.subtitle,
      subtitle: family.subtitle,
      category: family.category,
      costcoComparable: family.costcoComparable,
      confidence:
        family.confidence === "working"
          ? "medium"
          : (family.confidence as FeedProductView["confidence"]),
      feedId: feed.id,
      feedLabel: feed.label,
      regionLabel: feed.regionLabel,
      hasFeedData: Boolean(baseline) || hasAdMatches || inferredBaseline != null,
      baselinePrice: effectiveBaseline,
      baselineSource:
        baseline?.source ??
        (inferredBaseline != null ? INFERRED_BASELINE_SOURCE : null),
      weeklyPrices,
      priceComparison: getFallbackComparison(comparisonKey, feed.id),
      costcoPriceHistory: getCostcoPriceHistory(comparisonKey, feed.id),
      trackerType: "brand_family",
      chartMode: "single",
      homepageSection: family.homepageSection,
      displayOrder: family.displayOrder,
    };
  }).sort((a, b) => (a.displayOrder ?? 999) - (b.displayOrder ?? 999));
}

export function buildSafewayYamlProducts(): FeedProductView[] {
  return buildYamlFamilyFeedProducts(SAFEWAY_FEED_ID);
}

export function buildVonsYamlProducts(): FeedProductView[] {
  return buildYamlFamilyFeedProducts(VONS_FEED_ID);
}
