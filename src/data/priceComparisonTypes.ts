import type { PriceComparisonView } from "./priceComparisons.generated";

export type {
  PriceComparisonView,
  PriceComparisonWinner,
  PriceComparisonStatus,
} from "./priceComparisons.generated";

/** Merged onto FeedProductView when a grocery-vs-Costco comparison exists. */
export type ProductPriceComparison = PriceComparisonView;
