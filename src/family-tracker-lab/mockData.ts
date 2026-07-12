/** Local mock data for family tracker UI lab; not wired to production. */

export type StockUpRating =
  | "Great"
  | "Good"
  | "Great if buying full promo quantity";

export type FamilyStatus = "On sale this week" | "Promo deal this week";

export type Variant = {
  id: string;
  name: string;
  size: string;
  priceLabel: string;
};

export type GroceryFamily = {
  id: string;
  displayName: string;
  saleLabel: string;
  effectivePriceLabel?: string;
  usualRange: string;
  stockUp: StockUpRating;
  status: FamilyStatus;
  summary: string;
  variantNote: string;
  takeaway: string;
  caveat?: string;
  pricingBehavior: string;
  groupedThisWeek: boolean;
  variants: Variant[];
};

export const MOCK_FAMILIES: GroceryFamily[] = [
  {
    id: "lays",
    displayName: "Lay's Chips",
    saleLabel: "$1.99 each",
    usualRange: "usually $4.99–$5.49",
    stockUp: "Great",
    status: "On sale this week",
    summary: "Lay's chips are at a strong stock-up price this week.",
    variantNote:
      "Most participating Lay's flavors are the same sale price. Some specialty bags may be slightly smaller.",
    takeaway:
      "Good week to buy Lay's, especially if you are flexible on flavor.",
    caveat: "Some specialty bags are slightly smaller than Classic.",
    pricingBehavior:
      "This week grouped (same sale price). Baseline may need separate tracking when normal prices differ.",
    groupedThisWeek: true,
    variants: [
      { id: "lays-classic", name: "Classic / Original", size: "10oz", priceLabel: "$1.99" },
      { id: "lays-bbq", name: "BBQ", size: "7.75oz", priceLabel: "$1.99" },
      { id: "lays-sco", name: "Sour Cream & Onion", size: "7.75oz", priceLabel: "$1.99" },
      { id: "lays-limon", name: "Limón", size: "7.75oz", priceLabel: "$1.99" },
    ],
  },
  {
    id: "ritz",
    displayName: "Ritz",
    saleLabel: "2 for $5",
    usualRange: "usually $4.49–$5.49 each",
    stockUp: "Good",
    status: "On sale this week",
    summary: "Ritz products are included in a solid sale this week.",
    variantNote:
      "Original crackers, Toasted Chips, Crisp & Thins, Ritz Bits may all appear under Ritz family, but some are different sizes/formats.",
    takeaway:
      "Good week to buy Ritz, but original crackers are the cleanest pantry stock-up.",
    caveat: "Snack formats are smaller and different from original crackers.",
    pricingBehavior:
      "This week one family deal. Detail view shows snack formats smaller/different.",
    groupedThisWeek: true,
    variants: [
      { id: "ritz-original", name: "Original Crackers", size: "13.7oz", priceLabel: "$2.50" },
      { id: "ritz-chips", name: "Toasted Chips", size: "8.1oz", priceLabel: "$2.50" },
      { id: "ritz-thins", name: "Crisp & Thins", size: "7.1oz", priceLabel: "$2.50" },
      { id: "ritz-bits", name: "Ritz Bits", size: "8.8oz", priceLabel: "$2.50" },
    ],
  },
  {
    id: "ben-jerrys",
    displayName: "Ben & Jerry's",
    saleLabel: "$3.49 each",
    usualRange: "usually $5.99–$6.99",
    stockUp: "Great",
    status: "On sale this week",
    summary: "Ben & Jerry's pints are at a strong stock-up price.",
    variantNote: "Most flavors same pint size, family stays simple.",
    takeaway: "Great week to buy if you have freezer space.",
    pricingBehavior: "Safe to group; consistent size/price.",
    groupedThisWeek: true,
    variants: [
      { id: "bj-half-baked", name: "Half Baked", size: "16oz", priceLabel: "$3.49" },
      { id: "bj-cherry", name: "Cherry Garcia", size: "16oz", priceLabel: "$3.49" },
      { id: "bj-phish", name: "Phish Food", size: "16oz", priceLabel: "$3.49" },
    ],
  },
  {
    id: "coke-12pk",
    displayName: "Coca-Cola 12-packs",
    saleLabel: "Buy 2 get 3 free",
    effectivePriceLabel: "~$3.60 each when buying 5",
    usualRange: "usually $8.99–$10.99 each",
    stockUp: "Great if buying full promo quantity",
    status: "Promo deal this week",
    summary:
      "Coke 12-packs are a great deal only if you buy the full promo quantity.",
    variantNote: "Coke, Diet Coke, Coke Zero, Sprite mix-and-match.",
    takeaway: "Great stock-up if you are buying five total.",
    caveat: "Must buy 5 packs to unlock the promo price.",
    pricingBehavior:
      "Family display focuses on effective price and promo requirement.",
    groupedThisWeek: true,
    variants: [
      { id: "coke-classic", name: "Coke", size: "12-pack", priceLabel: "mix-and-match" },
      { id: "coke-diet", name: "Diet Coke", size: "12-pack", priceLabel: "mix-and-match" },
      { id: "coke-zero", name: "Coke Zero", size: "12-pack", priceLabel: "mix-and-match" },
      { id: "coke-sprite", name: "Sprite", size: "12-pack", priceLabel: "mix-and-match" },
    ],
  },
];

export const RECOMMENDATION_HEADLINES: Record<string, string> = {
  lays: "Buy Lay's this week",
  ritz: "Stock up on Ritz. Favor original crackers",
  "ben-jerrys": "Stock up on Ben & Jerry's",
  "coke-12pk": "Only buy Coke if you want five 12-packs",
};
