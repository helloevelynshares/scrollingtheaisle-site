/**
 * canonical_products are shared across all regional feeds.
 * Display names, search aliases, and sort order live here, not duplicated per retailer.
 */
export type CanonicalProduct = {
  id: string;
  displayName: string;
  productFamily: string;
  sizeLabel?: string;
  costcoComparable: boolean;
  confidence: "high" | "medium" | "low";
  sortOrder: number;
  /** Retailer search terms / aliases for baseline matching (Safeway, Vons, Costco). */
  searchAliases: string[];
};

/** Original tracker items (sort_order 1–10). New cross-store items start at 11. */
export const ORIGINAL_TRACKER_SORT_MAX = 10;

export const CANONICAL_PRODUCTS: CanonicalProduct[] = [
  {
    id: "strawberries",
    displayName: "Strawberries",
    productFamily: "strawberries",
    sizeLabel: "1 lb",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 1,
    searchAliases: [
      "strawberries",
      "fresh strawberries",
      "organic strawberries",
      "strawberry",
      "1 lb strawberries",
      "2 lb strawberries",
    ],
  },
  {
    id: "avocados",
    displayName: "Hass Avocados",
    productFamily: "avocados",
    sizeLabel: "Each",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 2,
    searchAliases: ["hass avocado", "avocado"],
  },
  {
    id: "doritos_nacho_cheese",
    displayName: "Doritos Nacho Cheese",
    productFamily: "doritos_nacho_cheese",
    sizeLabel: "9.25 oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 3,
    searchAliases: ["doritos nacho cheese", "doritos"],
  },
  {
    id: "cheetos_crunchy",
    displayName: "Cheetos Crunchy",
    productFamily: "cheetos_crunchy",
    sizeLabel: "8.5 oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 4,
    searchAliases: ["cheetos crunchy", "cheetos"],
  },
  {
    id: "coke_zero",
    displayName: "Coke Zero",
    productFamily: "coke_zero",
    sizeLabel: "12 pack / 12 fl oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 5,
    searchAliases: ["coke zero", "coca-cola zero"],
  },
  {
    id: "chobani_greek_yogurt",
    displayName: "Chobani Greek Yogurt",
    productFamily: "chobani_greek_yogurt",
    sizeLabel: "32 oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 6,
    searchAliases: ["chobani greek yogurt", "chobani greek"],
  },
  {
    id: "cheerios",
    displayName: "Cheerios",
    productFamily: "cheerios",
    sizeLabel: "8.9 oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 7,
    searchAliases: ["cheerios", "cheerios cereal"],
  },
  {
    id: "tillamook_ice_cream",
    displayName: "Tillamook Ice Cream",
    productFamily: "tillamook_ice_cream",
    sizeLabel: "1.75 qt",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 8,
    searchAliases: ["tillamook ice cream"],
  },
  {
    id: "mission_tortilla_chips",
    displayName: "Mission Tortilla Chips",
    productFamily: "mission_tortilla_chips",
    sizeLabel: "11 oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 9,
    searchAliases: ["mission tortilla chips"],
  },
  {
    id: "nature_valley_bars",
    displayName: "Nature Valley Bars",
    productFamily: "nature_valley_bars",
    sizeLabel: "12 ct",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 10,
    searchAliases: [
      "Nature Valley",
      "Nature Valley protein bars",
      "Nature Valley crunchy bars",
      "Nature Valley biscuits",
      "Nature Valley oatmeal squares",
      "Nature Valley bars",
      "nature valley granola bars",
    ],
  },
  {
    id: "fage_greek_yogurt",
    displayName: "Fage Greek Yogurt",
    productFamily: "fage_greek_yogurt",
    sizeLabel: "32 oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 11,
    searchAliases: [
      "Fage",
      "Fage Greek yogurt",
      "Fage Total",
      "Fage 0%",
      "Fage 2%",
      "Greek yogurt Fage",
      "plain Greek yogurt",
    ],
  },
  {
    id: "frito_lay_multipack_chips",
    displayName: "Frito-Lay Multipack Chips",
    productFamily: "frito_lay_multipack_chips",
    sizeLabel: "Multipack",
    costcoComparable: true,
    confidence: "medium",
    sortOrder: 12,
    searchAliases: [
      "Frito Lay variety pack",
      "Frito-Lay",
      "Frito Lay",
      "chip multipack",
      "variety pack chips",
      "42 count chips",
      "30 count chips",
      "party size chips",
      "snack pack chips",
    ],
  },
  {
    id: "haagen_dazs_ice_cream",
    displayName: "Häagen-Dazs Ice Cream",
    productFamily: "haagen_dazs_ice_cream",
    sizeLabel: "14 oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 13,
    searchAliases: [
      "Haagen Dazs",
      "Häagen-Dazs",
      "Haagen Dazs bars",
      "Häagen-Dazs bars",
      "Haagen Dazs ice cream",
      "Häagen-Dazs ice cream",
      "coffee ice cream",
      "ice cream bars",
    ],
  },
  {
    id: "grapes",
    displayName: "Grapes",
    productFamily: "grapes",
    sizeLabel: "per lb",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 14,
    searchAliases: [
      "grapes",
      "green grapes",
      "red grapes",
      "seedless grapes",
      "black grapes",
    ],
  },
  {
    id: "eggs_18_count",
    displayName: "Eggs, 18-count",
    productFamily: "eggs_18_count",
    sizeLabel: "18 ct",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 15,
    searchAliases: [
      "eggs",
      "18 count eggs",
      "18-count eggs",
      "large eggs",
      "cage free eggs",
      "brown eggs",
      "white eggs",
    ],
  },
  {
    id: "oreos_sandwich_cookies",
    displayName: "Oreos / Sandwich Cookies",
    productFamily: "oreos_sandwich_cookies",
    sizeLabel: "Family size",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 16,
    searchAliases: [
      "Oreo",
      "Oreos",
      "sandwich cookies",
      "limited edition Oreo",
      "family size Oreo",
      "Oreo family size",
      "Oreo cookies",
    ],
  },
  {
    id: "protein_bars",
    displayName: "Protein Bars",
    productFamily: "protein_bars",
    sizeLabel: "Varies",
    costcoComparable: true,
    confidence: "medium",
    sortOrder: 17,
    searchAliases: [
      "protein bars",
      "RXBAR",
      "RX bars",
      "Kai's protein bars",
      "Kize protein bars",
      "protein snack bars",
      "snack bars",
    ],
  },
  {
    id: "kettle_brand_chips",
    displayName: "Kettle Brand Chips",
    productFamily: "kettle_brand_chips",
    sizeLabel: "8 oz",
    costcoComparable: true,
    confidence: "high",
    sortOrder: 18,
    searchAliases: [
      "Kettle Brand",
      "Kettle chips",
      "Kettle Brand potato chips",
      "Kettle Brand sea salt",
      "Kettle Brand jalapeno",
      "Kettle Brand backyard barbecue",
      "Kettle Brand salt and vinegar",
      "potato chips",
    ],
  },
];

export function getCanonicalSortOrder(canonicalId: string): number {
  return (
    CANONICAL_PRODUCTS.find((product) => product.id === canonicalId)?.sortOrder ??
    999
  );
}

export function isRecurringCrossStoreProduct(canonicalId: string): boolean {
  return getCanonicalSortOrder(canonicalId) > ORIGINAL_TRACKER_SORT_MAX;
}
