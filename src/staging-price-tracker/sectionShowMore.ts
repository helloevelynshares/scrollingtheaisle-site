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

export function getCollapsedProductIds(
  sectionId: HomepageSectionId,
): readonly string[] {
  return SECTION_COLLAPSED_PRODUCT_IDS[sectionId] ?? [];
}

export function partitionSectionProducts(
  sectionId: HomepageSectionId,
  products: FeedProductView[],
  isExpanded: boolean,
  bypassCollapse: boolean,
): { visible: FeedProductView[]; hiddenCount: number } {
  const collapsedIds = getCollapsedProductIds(sectionId);
  if (!collapsedIds.length || isExpanded || bypassCollapse) {
    return { visible: products, hiddenCount: 0 };
  }

  const hidden = new Set(collapsedIds);
  const visible = products.filter((product) => !hidden.has(product.canonicalId));
  return { visible, hiddenCount: products.length - visible.length };
}
