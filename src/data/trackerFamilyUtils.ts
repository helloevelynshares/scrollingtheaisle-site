import type { PriceComparisonView } from "./priceComparisonTypes";
import { getPriceFeed } from "./priceFeeds";
import type {
  FamilyMemberPriceView,
  FeedProductView,
  WeeklyPrice,
} from "./priceTrackerTypes";
import {
  INFERRED_BASELINE_SOURCE,
  inferBaselineFromWeeklyPrices,
} from "./priceTrackerUtils";
import {
  TRACKER_FAMILIES,
  type FamilyMemberDefinition,
  type TrackerFamilyDefinition,
} from "./trackerFamilies";
import {
  FAMILY_MEMBER_WEEKLY_AD_PRICES,
  FAMILY_WEEKLY_AD_PRICES,
  FAMILY_WEEKLY_AD_WEEKS,
  VONS_FAMILY_MEMBER_WEEKLY_AD_PRICES,
  VONS_FAMILY_WEEKLY_AD_PRICES,
  VONS_FAMILY_WEEKLY_AD_WEEKS,
  type GeneratedWeeklyAdPrice,
} from "./familyWeeklyAdPrices.generated";
import { isActiveAdWeek } from "./weeklyAdPreview";

const SAFEWAY_FEED_ID = "safeway_bay_area";
const VONS_FEED_ID = "vons_albertsons_socal";

type WeekMeta = {
  weekStart: string;
  sourceLabel: string;
  sourceFile: string;
};

function weeksForFeed(feedId: string): WeekMeta[] {
  if (feedId === VONS_FEED_ID) {
    return VONS_FAMILY_WEEKLY_AD_WEEKS.map((week) => ({
      weekStart: week.weekStart,
      sourceLabel: week.sourceLabel,
      sourceFile: week.sourceFile,
    }));
  }
  return FAMILY_WEEKLY_AD_WEEKS.map((week) => ({
    weekStart: week.weekStart,
    sourceLabel: week.sourceLabel,
    sourceFile: week.sourceFile,
  }));
}

function memberPricesForFeed(
  feedId: string,
  familyId: string,
): Record<string, Record<string, GeneratedWeeklyAdPrice>> {
  if (feedId === VONS_FEED_ID) {
    return VONS_FAMILY_MEMBER_WEEKLY_AD_PRICES[familyId] ?? {};
  }
  return FAMILY_MEMBER_WEEKLY_AD_PRICES[familyId] ?? {};
}

function familyPricesForFeed(
  feedId: string,
  familyId: string,
): Record<string, GeneratedWeeklyAdPrice> {
  if (feedId === VONS_FEED_ID) {
    return VONS_FAMILY_WEEKLY_AD_PRICES[familyId] ?? {};
  }
  return FAMILY_WEEKLY_AD_PRICES[familyId] ?? {};
}

function effectiveMemberWeeklyPrice(
  baseline: number | null,
  entry: GeneratedWeeklyAdPrice | undefined,
  sourceLabel: string,
  weekStart: string,
): WeeklyPrice {
  const adPrice = entry?.price ?? null;
  const matchConfidence = entry?.confidence ?? null;
  const useAd =
    adPrice != null && matchConfidence != null && matchConfidence !== "low";
  const fallbackPrice = baseline ?? adPrice ?? 0;

  return {
    weekStart,
    price: useAd ? adPrice : fallbackPrice,
    adPrice,
    matchConfidence,
    priceType: useAd ? "weekly_ad" : "baseline",
    offerText: entry?.offerText ?? undefined,
    isBaselineFallback: !useAd,
    sourceLabel,
  };
}

function buildMemberView(
  member: FamilyMemberDefinition,
  feedId: string,
  weeks: WeekMeta[],
  byWeek: Record<string, GeneratedWeeklyAdPrice>,
): FamilyMemberPriceView {
  const baseline = member.baselineByFeed[feedId] ?? null;

  const weeklyPrices: WeeklyPrice[] = weeks.map((week) =>
    effectiveMemberWeeklyPrice(
      baseline,
      byWeek[week.weekStart],
      `${week.sourceLabel} · ${week.sourceFile}`,
      week.weekStart,
    ),
  );

  const inferredBaseline = inferBaselineFromWeeklyPrices(weeklyPrices);
  const effectiveBaseline = baseline ?? inferredBaseline;
  const sorted = [...weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );
  const currentPrice = sorted[sorted.length - 1]?.price ?? effectiveBaseline;

  return {
    memberId: member.id,
    label: member.label,
    sizeLabel: member.sizeLabel,
    baselinePrice: effectiveBaseline ?? 0,
    currentPrice,
    weeklyPrices,
  };
}

function aggregateWeeklyRange(
  members: FamilyMemberPriceView[],
  weeks: WeekMeta[],
): WeeklyPrice[] {
  return weeks.map((week) => {
    const memberWeeks = members
      .map((member) =>
        member.weeklyPrices.find((slot) => slot.weekStart === week.weekStart),
      )
      .filter((slot): slot is WeeklyPrice => slot != null);

    const adPrices = memberWeeks
      .filter(
        (slot) =>
          slot.adPrice != null &&
          slot.matchConfidence != null &&
          slot.matchConfidence !== "low",
      )
      .map((slot) => slot.adPrice as number);

    const prices = memberWeeks.map((slot) => slot.price);
    const useAd = adPrices.length > 0;
    const price = useAd ? Math.min(...adPrices) : Math.min(...prices);
    const adPrice = useAd ? Math.min(...adPrices) : null;
    const maxAd = useAd ? Math.max(...adPrices) : null;

    return {
      weekStart: week.weekStart,
      price,
      adPrice,
      priceMax: maxAd,
      matchConfidence: useAd ? ("medium" as const) : null,
      priceType: useAd ? ("weekly_ad" as const) : ("baseline" as const),
      offerText: memberWeeks.find((slot) => slot.offerText)?.offerText,
      isBaselineFallback: !useAd,
      sourceLabel: memberWeeks[0]?.sourceLabel,
    };
  });
}

function priceRangeFromMembers(
  members: FamilyMemberPriceView[],
  pick: "baseline" | "current",
): { min: number; max: number } | null {
  const values = members
    .map((member) =>
      pick === "baseline" ? member.baselinePrice : member.currentPrice,
    )
    .filter((value): value is number => value != null && value > 0);

  if (values.length === 0) {
    return null;
  }

  return { min: Math.min(...values), max: Math.max(...values) };
}

function hasRealAdWeek(week: WeeklyPrice): boolean {
  return (
    !week.isBaselineFallback &&
    week.priceType === "weekly_ad" &&
    week.adPrice != null
  );
}

/**
 * "This week" sale range from the calendar-active ad week (or latest
 * non-preview ad match). Never use an upcoming preview week here — preview
 * callouts are handled separately when the upcoming price beats this week.
 */
function saleRangeFromWeekly(
  weeklyPrices: WeeklyPrice[],
): { min: number; max: number } | null {
  const sorted = [...weeklyPrices].sort((a, b) =>
    a.weekStart.localeCompare(b.weekStart),
  );

  const active = [...sorted]
    .reverse()
    .find(
      (week) =>
        isActiveAdWeek(week.weekStart, week.weekEnd ?? week.weekStart) &&
        hasRealAdWeek(week),
    );
  const target =
    active ??
    [...sorted]
      .reverse()
      .find((week) => !week.isPreviewWeek && hasRealAdWeek(week));

  if (!target || target.adPrice == null) {
    return null;
  }

  const weekSlots = weeklyPrices.filter(
    (slot) => slot.weekStart === target.weekStart,
  );
  const adValues = weekSlots
    .map((slot) => slot.adPrice)
    .filter((value): value is number => value != null);

  if (adValues.length === 0) {
    return { min: target.adPrice, max: target.priceMax ?? target.adPrice };
  }

  return { min: Math.min(...adValues), max: Math.max(...adValues) };
}

/** Midpoint oz for Ritz classic box (12–13.7 oz). */
const RITZ_CLASSIC_OZ = 12.85;

export function groceryUnitPriceForRitz(
  groceryPrice: number,
  oz: number = RITZ_CLASSIC_OZ,
): number {
  return groceryPrice / oz;
}

export type FamilyComparisonBadge = {
  title: string;
  detail: string | null;
  tone: "grocery" | "costco" | "neutral" | "muted";
};

export function getFamilyComparisonBadge(
  family: TrackerFamilyDefinition,
  feedId: string,
  feedLabel: string,
  groceryShelfPrice: number | null,
  grocerySalePrice: number | null,
): FamilyComparisonBadge | null {
  const costco = family.costcoComparison;
  if (!costco || !family.costcoComparable) {
    return null;
  }

  const groceryPrice = grocerySalePrice ?? groceryShelfPrice;
  if (groceryPrice == null) {
    return null;
  }

  const groceryUnit = groceryUnitPriceForRitz(groceryPrice);
  const costcoUnit = costco.unitPrice;
  const pctAboveCostco = ((groceryUnit - costcoUnit) / costcoUnit) * 100;

  if (pctAboveCostco <= 25) {
    return {
      title: `More variety: ${feedLabel}`,
      detail: null,
      tone: "grocery",
    };
  }

  return {
    title: "Best value: Costco",
    detail: null,
    tone: "costco",
  };
}

export function buildFamilyFeedProduct(
  family: TrackerFamilyDefinition,
  feedId: string,
): FeedProductView | null {
  const feed = getPriceFeed(feedId);
  if (!feed) {
    return null;
  }

  const weeks = weeksForFeed(feedId);
  if (weeks.length === 0) {
    return null;
  }

  const memberAdByWeek = memberPricesForFeed(feedId, family.id);
  const members = family.members.map((member) =>
    buildMemberView(member, feedId, weeks, memberAdByWeek[member.id] ?? {}),
  );

  const familyAdByWeek = familyPricesForFeed(feedId, family.id);
  const hasFamilyAd = Object.values(familyAdByWeek).some(
    (entry) => entry?.price != null && entry.confidence !== "low",
  );
  const hasMemberAd = members.some((member) =>
    member.weeklyPrices.some(
      (week) => week.adPrice != null && week.matchConfidence !== "low",
    ),
  );

  const weeklyPrices =
    members.length > 1
      ? aggregateWeeklyRange(members, weeks)
      : weeks.map((week) => {
          const memberWeek = members[0]?.weeklyPrices.find(
            (slot) => slot.weekStart === week.weekStart,
          );
          if (memberWeek) {
            return memberWeek;
          }
          const entry = familyAdByWeek[week.weekStart];
          const baseline = members[0]?.baselinePrice ?? null;
          return effectiveMemberWeeklyPrice(
            baseline,
            entry,
            `${week.sourceLabel} · ${week.sourceFile}`,
            week.weekStart,
          );
        });

  const inferredBaseline = inferBaselineFromWeeklyPrices(weeklyPrices);
  const memberBaselines = members
    .map((member) => member.baselinePrice)
    .filter((value) => value > 0);
  const baselinePrice =
    memberBaselines.length > 0
      ? Math.max(...memberBaselines)
      : inferredBaseline;

  const hasFeedData =
    hasFamilyAd ||
    hasMemberAd ||
    memberBaselines.length > 0 ||
    inferredBaseline != null;

  const priceRange = priceRangeFromMembers(members, "baseline");
  const salePriceRange = saleRangeFromWeekly(weeklyPrices);
  const primaryMember = members[0];

  const grocerySale =
    salePriceRange?.min ??
    [...weeklyPrices]
      .sort((a, b) => a.weekStart.localeCompare(b.weekStart))
      .filter((week) => !week.isPreviewWeek && week.adPrice != null)
      .at(-1)?.adPrice ??
    null;

  const familyComparison = getFamilyComparisonBadge(
    family,
    feedId,
    feed.label,
    primaryMember?.baselinePrice ?? baselinePrice,
    grocerySale,
  );

  const priceComparison: PriceComparisonView | null = family.costcoComparison
    ? {
        canonicalProductId: family.id,
        groceryFeedId: feedId,
        groceryStoreLabel: feed.label,
        groceryPrice: grocerySale ?? primaryMember?.baselinePrice ?? null,
        groceryPackageDescription: "Classic Ritz boxes, 12–13.7 oz",
        groceryUnitType: "oz",
        groceryUnitCount: 12.85,
        groceryUnitPrice:
          grocerySale != null
            ? groceryUnitPriceForRitz(grocerySale)
            : primaryMember?.baselinePrice != null
              ? groceryUnitPriceForRitz(primaryMember.baselinePrice)
              : null,
        costcoRegionId:
          feedId === SAFEWAY_FEED_ID ? "costco_sf" : "costco_oc",
        costcoStoreLabel:
          feedId === SAFEWAY_FEED_ID
            ? "Costco San Francisco"
            : "Costco Tustin",
        costcoPrice: family.costcoComparison.price,
        costcoPackageDescription: `${family.costcoComparison.productLabel} ${family.costcoComparison.packageDescription}`,
        costcoUnitType: "oz",
        costcoUnitCount: 61.6,
        costcoUnitPrice: family.costcoComparison.unitPrice,
        winner: "unknown",
        savingsAmount: null,
        savingsPercent: null,
        comparisonStatus: "comparable",
        comparisonNote: family.costcoComparison.packageDescription,
      }
    : null;

  return {
    canonicalId: family.id,
    displayName: family.displayName,
    productFamily: family.id,
    sizeLabel: family.subtitle,
    costcoComparable: family.costcoComparable,
    confidence: "medium",
    feedId: feed.id,
    feedLabel: feed.label,
    regionLabel: feed.regionLabel,
    hasFeedData,
    baselinePrice,
    baselineSource:
      memberBaselines.length > 0 ? "Typical shelf price" : INFERRED_BASELINE_SOURCE,
    weeklyPrices,
    priceComparison,
    trackerType: family.trackerType,
    subtitle: family.subtitle,
    category: family.category,
    familyMembers: members,
    priceRange,
    salePriceRange,
    chartMode: members.length > 1 ? "range" : "single",
    familyComparisonBadge: familyComparison,
  };
}

export function buildAllFamilyFeedProducts(feedId: string): FeedProductView[] {
  return TRACKER_FAMILIES.map((family) => buildFamilyFeedProduct(family, feedId))
    .filter((product): product is FeedProductView => product != null)
    .sort((a, b) => {
      const orderA =
        TRACKER_FAMILIES.find((family) => family.id === a.canonicalId)
          ?.sortOrder ?? 999;
      const orderB =
        TRACKER_FAMILIES.find((family) => family.id === b.canonicalId)
          ?.sortOrder ?? 999;
      return orderA - orderB;
    });
}

export function appendFamiliesToFeedProducts(
  products: FeedProductView[],
  feedId: string,
): FeedProductView[] {
  const existingIds = new Set(products.map((product) => product.canonicalId));
  const families = buildAllFamilyFeedProducts(feedId).filter(
    (family) => !existingIds.has(family.canonicalId),
  );
  return [...products, ...families];
}
