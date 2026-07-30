import {
  CANONICAL_TRACKER_FAMILIES,
  LEGACY_CANONICAL_TO_FAMILY,
} from "./canonicalTrackerFamilies.generated";
import { getPriceFeed } from "./priceFeeds";
import { getFallbackComparison, getCostcoPriceHistory } from "./priceComparisonUtils";
import type { FeedProductView, WeeklyPrice } from "./priceTrackerTypes";
import {
  INFERRED_BASELINE_SOURCE,
  backfillBaselineFallbackWeeks,
  inferBaselineFromWeeklyPrices,
  sanitizeBaselinePrice,
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
        const price = sanitizeBaselinePrice(
          normalizeEggsBaselineToDozen(
            legacyId,
            entry.price,
            entry.retailerProductName,
          ),
        );
        if (price == null) {
          continue;
        }
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
        const price = sanitizeBaselinePrice(
          normalizeEggsBaselineToDozen(
            legacyId,
            entry.baselinePrice,
            entry.retailerProductName,
          ),
        );
        if (price == null) {
          continue;
        }
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
    const entry = SAFEWAY_BASELINES[familyId];
    const price = sanitizeBaselinePrice(entry.price);
    if (price == null) {
      return null;
    }
    return { price, source: entry.source };
  }
  if (feedId === VONS_FEED_ID && VONS_BASELINE_BY_CANONICAL[familyId]) {
    const entry = VONS_BASELINE_BY_CANONICAL[familyId];
    const price = sanitizeBaselinePrice(entry.baselinePrice);
    if (price == null) {
      return null;
    }
    return { price, source: entry.baselineSource };
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
    adPrice != null &&
    matchConfidence != null &&
    matchConfidence !== "low" &&
    sanitizeBaselinePrice(adPrice) != null;
  // Never ship $0 as a chart/UI price; prefer store baseline, else valid ad.
  const fallbackPrice =
    sanitizeBaselinePrice(baselinePrice) ??
    sanitizeBaselinePrice(adPrice) ??
    0;

  return {
    weekStart,
    weekEnd,
    isPreviewWeek: isPreviewWeek(weekStart),
    price: useAd ? adPrice! : fallbackPrice,
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

  const products = CANONICAL_TRACKER_FAMILIES.map((family) => {
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
    const effectiveBaseline = sanitizeBaselinePrice(
      baseline?.price ?? inferredBaseline,
    );
    backfillBaselineFallbackWeeks(weeklyPrices, effectiveBaseline);

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
      hasFeedData: Boolean(baseline) || hasAdMatches || effectiveBaseline != null,
      baselinePrice: effectiveBaseline,
      baselineSource:
        baseline?.source ??
        (inferredBaseline != null && effectiveBaseline != null
          ? INFERRED_BASELINE_SOURCE
          : null),
      weeklyPrices,
      priceComparison: getFallbackComparison(comparisonKey, feed.id),
      costcoPriceHistory: getCostcoPriceHistory(comparisonKey, feed.id),
      trackerType: "brand_family" as const,
      chartMode: "single" as const,
      homepageSection: family.homepageSection,
      displayOrder: family.displayOrder,
      displayCardGroup: family.displayCardGroup || undefined,
    };
  }).sort((a, b) => (a.displayOrder ?? 999) - (b.displayOrder ?? 999));

  return mergeDisplayCardGroups(products);
}

/** Egg carton size used for per-egg deal comparison within a display card group. */
function eggPackCount(canonicalId: string): number | null {
  if (canonicalId === "lucerne_eggs_18") return 18;
  if (canonicalId === "eggs_dozen_normalized") return 12;
  return null;
}

function unitDealPrice(product: FeedProductView, week: WeeklyPrice): number | null {
  const pack = eggPackCount(product.canonicalId);
  if (pack == null || week.price == null || week.price <= 0) {
    return week.price ?? null;
  }
  return week.price / pack;
}

function preferAdWeek(week: WeeklyPrice): boolean {
  return (
    week.adPrice != null &&
    week.matchConfidence != null &&
    week.matchConfidence !== "low"
  );
}

/**
 * Collapse families that share displayCardGroup into one card.
 * For Lucerne eggs, pick the better per-egg price each week (12 vs 18 count)
 * and surface that count in the subtitle / preview.
 */
function mergeDisplayCardGroups(
  products: FeedProductView[],
): FeedProductView[] {
  const byGroup = new Map<string, FeedProductView[]>();
  const ungrouped: FeedProductView[] = [];

  for (const product of products) {
    const group = product.displayCardGroup?.trim();
    if (!group) {
      ungrouped.push(product);
      continue;
    }
    const list = byGroup.get(group) ?? [];
    list.push(product);
    byGroup.set(group, list);
  }

  const merged: FeedProductView[] = [...ungrouped];

  for (const [, members] of byGroup) {
    if (members.length === 1) {
      merged.push(members[0]);
      continue;
    }

    // Prefer the 12-count family as the stable card identity / scroll target.
    const primary =
      members.find((m) => m.canonicalId === "eggs_dozen_normalized") ??
      members[0];

    type OwnedWeek = { member: FeedProductView; week: WeeklyPrice };
    const mergedWeeks: WeeklyPrice[] = primary.weeklyPrices.map((anchor) => {
      const owned: OwnedWeek[] = members
        .map((member) => {
          const week = member.weeklyPrices.find(
            (w) => w.weekStart === anchor.weekStart,
          );
          return week ? { member, week } : null;
        })
        .filter((row): row is OwnedWeek => Boolean(row));

      const adOwned = owned.filter((row) => preferAdWeek(row.week));
      const pool = adOwned.length ? adOwned : owned;

      let best = pool[0];
      for (const row of pool.slice(1)) {
        const bestUnit = unitDealPrice(best.member, best.week);
        const rowUnit = unitDealPrice(row.member, row.week);
        if (rowUnit == null) continue;
        if (bestUnit == null || rowUnit < bestUnit) {
          best = row;
        }
      }

      return {
        ...best.week,
        offerText:
          best.week.offerText ||
          (best.member.canonicalId === "lucerne_eggs_18"
            ? "Lucerne Eggs 18-count"
            : "Lucerne Eggs 12-count"),
      };
    });

    // Subtitle reflects the better current/preview ad deal when present.
    const previewOrCurrent =
      [...mergedWeeks].reverse().find((w) => preferAdWeek(w)) ??
      mergedWeeks[mergedWeeks.length - 1];
    const winnerNow =
      members.find((m) =>
        m.weeklyPrices.some(
          (w) =>
            w.weekStart === previewOrCurrent?.weekStart &&
            w.adPrice != null &&
            w.adPrice === previewOrCurrent?.adPrice,
        ),
      ) ?? primary;
    const countLabel =
      winnerNow.canonicalId === "lucerne_eggs_18" ? "18-count" : "12-count";

    const baselines = members
      .map((m) => m.baselinePrice)
      .filter((p): p is number => p != null && p > 0);
    const baselinePrice =
      baselines.length > 0 ? Math.min(...baselines) : primary.baselinePrice;

    merged.push({
      ...primary,
      displayName: "Lucerne Eggs",
      subtitle: `${countLabel} deal shown when better per egg; tracks 12- and 18-count`,
      sizeLabel: "12- or 18-count Lucerne cartons",
      weeklyPrices: mergedWeeks,
      baselinePrice,
      hasFeedData: members.some((m) => m.hasFeedData),
    });
  }

  return merged.sort(
    (a, b) => (a.displayOrder ?? 999) - (b.displayOrder ?? 999),
  );
}

export function buildSafewayYamlProducts(): FeedProductView[] {
  return buildYamlFamilyFeedProducts(SAFEWAY_FEED_ID);
}

export function buildVonsYamlProducts(): FeedProductView[] {
  return buildYamlFamilyFeedProducts(VONS_FEED_ID);
}
