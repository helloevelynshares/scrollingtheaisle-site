import type { HomepageSectionId } from "../data/canonicalTrackerFamilies";
import type { FeedProductView } from "../data/priceTrackerTypes";

/** Product ids hidden behind "Show more" until the section is expanded. */
export const SECTION_COLLAPSED_PRODUCT_IDS: Partial<
  Record<HomepageSectionId, readonly string[]>
> = {
  stock_up_snacks_and_treats: [
    "cheetos_party_size",
    "lays_party_size",
    "simply_snacks",
    "simply_party_size",
    "sun_chips_7oz",
    "nabisco_snack_crackers",
    "ritz_toasted_chips",
    "keebler_sandwich_crackers",
    "breyers_ice_cream",
    "tillamook_ice_cream",
    "haagen_dazs_bars_novelties",
    "dreyers_novelties",
  ],
  fresh_produce: ["nectarines_per_lb", "plums_per_lb", "sweet_corn"],
  dairy_breakfast_bakery: [
    "thomas_bagels_muffins_bread",
    "kings_hawaiian_rolls",
    "pillsbury_refrigerated_dough",
    "quest_bars",
    "clif_bars",
    "general_mills_cereal_family_size",
    "post_cereal_giant_size",
  ],
  drinks: ["simply_refrigerated_juice_lemonade"],
};

/**
 * Staples that must stay visible even when they are not a strong deal this week
 * (otherwise deal-quality ranking buries them behind "Show more").
 */
export const SECTION_ALWAYS_VISIBLE_PRODUCT_IDS: Partial<
  Record<HomepageSectionId, readonly string[]>
> = {
  dairy_breakfast_bakery: ["eggs_dozen_normalized", "butter_16oz"],
};

export function getCollapsedProductIds(
  sectionId: HomepageSectionId,
): readonly string[] {
  return SECTION_COLLAPSED_PRODUCT_IDS[sectionId] ?? [];
}

export function getAlwaysVisibleProductIds(
  sectionId: HomepageSectionId,
): readonly string[] {
  return SECTION_ALWAYS_VISIBLE_PRODUCT_IDS[sectionId] ?? [];
}

/**
 * How many items a section keeps behind "Show more". The curated
 * `SECTION_COLLAPSED_PRODUCT_IDS` list still decides *how many* items are
 * hidden per section, but which specific items are hidden is now driven by
 * deal-quality ranking (the lowest-ranked tail), so `products` MUST already be
 * sorted best-deal-first before calling this.
 */
export function getCollapsedCount(sectionId: HomepageSectionId): number {
  return getCollapsedProductIds(sectionId).length;
}

export function partitionSectionProducts(
  sectionId: HomepageSectionId,
  products: FeedProductView[],
  isExpanded: boolean,
  bypassCollapse: boolean,
): { visible: FeedProductView[]; hiddenCount: number } {
  const collapsedCount = getCollapsedCount(sectionId);
  if (!collapsedCount || isExpanded || bypassCollapse) {
    return { visible: products, hiddenCount: 0 };
  }

  // Hide the lowest-ranked (worst-deal) tail; keep the top deals visible.
  const hiddenCount = Math.min(collapsedCount, products.length);
  let visible = products.slice(0, products.length - hiddenCount);
  let hidden = products.slice(products.length - hiddenCount);

  // Pull staples (e.g. Lucerne eggs) out of the hidden tail if ranking buried them.
  const alwaysVisible = new Set(getAlwaysVisibleProductIds(sectionId));
  if (alwaysVisible.size > 0 && hidden.some((p) => alwaysVisible.has(p.canonicalId))) {
    const rescued: FeedProductView[] = [];
    const stillHidden: FeedProductView[] = [];
    for (const product of hidden) {
      if (alwaysVisible.has(product.canonicalId)) {
        rescued.push(product);
      } else {
        stillHidden.push(product);
      }
    }
    // Keep visible length stable: drop the weakest non-staples from the visible
    // tail for each rescued staple.
    const demoteCount = Math.min(rescued.length, visible.length);
    const demoted = visible.slice(visible.length - demoteCount);
    visible = [...visible.slice(0, visible.length - demoteCount), ...rescued];
    hidden = [...demoted.filter((p) => !alwaysVisible.has(p.canonicalId)), ...stillHidden];
  }

  return { visible, hiddenCount: hidden.length };
}
