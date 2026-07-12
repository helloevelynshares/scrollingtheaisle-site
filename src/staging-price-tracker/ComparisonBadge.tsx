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

function compactFamilyLabel(
  title: string,
  detail: string | null,
): string {
  if (detail) {
    return `${title} · ${detail}`;
  }
  return title;
}

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
    const label = compactFamilyLabel(familyBadge.title, familyBadge.detail);
    return (
      <p
        className={`price-tracker-comparison price-tracker-comparison--${familyBadge.tone}`}
        aria-label={`Store comparison: ${label}`}
      >
        {label}
      </p>
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
    <p
      className={`price-tracker-comparison price-tracker-comparison--${content.tone}`}
      aria-label={`Store comparison: ${content.label}`}
    >
      {content.label}
    </p>
  );
}
