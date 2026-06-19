import type { PriceComparisonView } from "../data/priceComparisonTypes";
import {
  GROCERY_FEED_IDS,
  getComparisonBadgeContent,
} from "../data/priceComparisonUtils";

type Props = {
  activeFeedId: string;
  activeGroceryLabel: string;
  comparison: PriceComparisonView | null | undefined;
  familyBadge?: {
    title: string;
    detail: string | null;
    tone: "grocery" | "costco" | "neutral" | "muted";
  } | null;
};

export function ComparisonBadge({
  activeFeedId,
  activeGroceryLabel,
  comparison,
  familyBadge,
}: Props) {
  if (!GROCERY_FEED_IDS.has(activeFeedId)) {
    return null;
  }

  if (familyBadge) {
    return (
      <div
        className={`price-tracker-comparison price-tracker-comparison--${familyBadge.tone}`}
        aria-label={`Store comparison: ${familyBadge.title}`}
      >
        <span className="price-tracker-comparison-title">{familyBadge.title}</span>
        {familyBadge.detail ? (
          <span className="price-tracker-comparison-detail">
            {familyBadge.detail}
          </span>
        ) : null}
      </div>
    );
  }

  if (!comparison) {
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
      {content.locationNote ? (
        <span className="price-tracker-comparison-location">
          {content.locationNote}
        </span>
      ) : null}
    </div>
  );
}
