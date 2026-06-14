import type { PriceComparisonView } from "../data/priceComparisonTypes";
import {
  GROCERY_FEED_IDS,
  getComparisonBadgeContent,
} from "../data/priceComparisonUtils";

type Props = {
  activeFeedId: string;
  activeGroceryLabel: string;
  comparison: PriceComparisonView | null | undefined;
};

export function ComparisonBadge({
  activeFeedId,
  activeGroceryLabel,
  comparison,
}: Props) {
  if (!GROCERY_FEED_IDS.has(activeFeedId) || !comparison) {
    return null;
  }

  if (comparison.groceryFeedId !== activeFeedId) {
    return null;
  }

  const content = getComparisonBadgeContent(
    comparison,
    activeFeedId,
    activeGroceryLabel,
  );
  if (!content) {
    return null;
  }

  return (
    <div
      className={`price-tracker-comparison price-tracker-comparison--${content.tone}`}
      aria-label={`Store comparison: ${content.title}`}
    >
      <span className="price-tracker-comparison-title">{content.title}</span>
      {content.detail ? (
        <span className="price-tracker-comparison-detail">{content.detail}</span>
      ) : null}
    </div>
  );
}
