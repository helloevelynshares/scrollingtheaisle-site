/**
 * Curated tracker families; additive to the 18 single-SKU canonical products.
 * Historical single-SKU rows (e.g. haagen_dazs_ice_cream) are never removed.
 */
export type TrackerType = "single_sku" | "brand_family" | "deal_family";

export type FamilyMemberDefinition = {
  id: string;
  label: string;
  sizeLabel: string;
  /** Typical shelf price when no weekly ad match (per feed). */
  baselineByFeed: Partial<Record<string, number>>;
};

export type FamilyCostcoComparison = {
  productLabel: string;
  packageDescription: string;
  price: number;
  unitType: "oz";
  unitPrice: number;
};

export type TrackerFamilyDefinition = {
  id: string;
  trackerType: TrackerType;
  displayName: string;
  subtitle: string;
  category: string;
  sortOrder: number;
  costcoComparable: boolean;
  members: FamilyMemberDefinition[];
  /** Static Costco warehouse reference for family-level comparison (Ritz). */
  costcoComparison?: FamilyCostcoComparison;
  /**
   * Canonical product IDs whose historical weekly rows can seed member charts
   * without deleting those products.
   */
  mappedCanonicalIds?: string[];
};

export const TRACKER_FAMILIES: TrackerFamilyDefinition[] = [
  {
    id: "ben_jerrys_ice_cream",
    trackerType: "deal_family",
    displayName: "Ben & Jerry's Ice Cream",
    subtitle: "Pints, non-dairy pints, and 4-count bars",
    category: "frozen",
    sortOrder: 19,
    costcoComparable: false,
    mappedCanonicalIds: [],
    members: [
      {
        id: "pint",
        label: "Ice cream pint",
        sizeLabel: "16 oz",
        baselineByFeed: {
          safeway_bay_area: 6.99,
          vons_albertsons_socal: 6.99,
        },
      },
      {
        id: "non_dairy_pint",
        label: "Non-dairy pint",
        sizeLabel: "16 oz",
        baselineByFeed: {
          safeway_bay_area: 6.99,
          vons_albertsons_socal: 6.99,
        },
      },
      {
        id: "bars_4ct",
        label: "4-count bars",
        sizeLabel: "4 ct",
        baselineByFeed: {
          safeway_bay_area: 7.99,
          vons_albertsons_socal: 7.99,
        },
      },
    ],
  },
  {
    id: "ritz_crackers_snacks",
    trackerType: "deal_family",
    displayName: "Ritz Crackers & Snacks",
    subtitle:
      "Classic boxes, Fresh Stacks, Crisp & Thins, Bits, and Drizzled Minis",
    category: "snacks",
    sortOrder: 20,
    costcoComparable: true,
    costcoComparison: {
      productLabel: "Nabisco Ritz Original",
      packageDescription: "61.6 oz",
      price: 10.79,
      unitType: "oz",
      unitPrice: 0.18,
    },
    members: [
      {
        id: "classic_box",
        label: "Classic box",
        sizeLabel: "12–13.7 oz",
        baselineByFeed: {
          safeway_bay_area: 5.49,
          vons_albertsons_socal: 5.49,
        },
      },
    ],
  },
];

export function getTrackerFamily(id: string): TrackerFamilyDefinition | undefined {
  return TRACKER_FAMILIES.find((family) => family.id === id);
}

export function isTrackerFamilyId(id: string): boolean {
  return TRACKER_FAMILIES.some((family) => family.id === id);
}
