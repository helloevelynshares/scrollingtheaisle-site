/**
 * Shared grouping for the hand-picked deals "balanced editorial breakout"
 * layout used on the homepage and staging price tracker.
 *
 * Keep in sync with homepage.js: BADGE_TO_CATEGORY / CATEGORY_ORDER /
 * categoryForPick / groupPicksByCategory.
 */

export const HANDPICKED_BADGE_TO_CATEGORY: Record<string, string> = {
  friday: "Friday",
  produce: "Produce",
  meat: "Meat",
  snacks: "Snacks",
  variety: "Variety",
  deal: "Other Deals",
};

export const HANDPICKED_CATEGORY_ORDER = [
  "Friday",
  "Produce",
  "Meat",
  "Snacks",
  "Variety",
  "Other Deals",
] as const;

export type HandpickedCategory = (typeof HANDPICKED_CATEGORY_ORDER)[number];

export function categoryForHandpickedBadge(
  badge: string | null | undefined,
): HandpickedCategory {
  const raw = String(badge || "")
    .trim()
    .toLowerCase();
  return (
    (HANDPICKED_BADGE_TO_CATEGORY[raw] as HandpickedCategory | undefined) ||
    "Other Deals"
  );
}

export function categorySlug(category: string): string {
  return category.toLowerCase().replace(/\s+/g, "-");
}

/** Group picks by editorial badge → category columns; drops empty categories. */
export function groupByHandpickedCategory<T extends { badge?: string | null }>(
  picks: T[],
  badgeOf: (pick: T) => string | null | undefined = (pick) => pick.badge,
): Map<HandpickedCategory, T[]> {
  const groups = new Map<HandpickedCategory, T[]>(
    HANDPICKED_CATEGORY_ORDER.map((name) => [name, [] as T[]]),
  );

  for (const pick of picks) {
    const cat = categoryForHandpickedBadge(badgeOf(pick));
    groups.get(cat)!.push(pick);
  }

  for (const [key, list] of [...groups.entries()]) {
    if (list.length === 0) {
      groups.delete(key);
    }
  }

  return groups;
}
