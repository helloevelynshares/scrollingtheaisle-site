import { useMemo, useState } from "react";
import {
  POPULAR_THIS_WEEK,
  type PopularThisWeekEntry,
  type PopularThisWeekStore,
} from "../data/canonicalTrackerFamilies";
import {
  isPopularWeekPreview,
  leadLineForStore,
  strategyLineForStore,
} from "../data/popularThisWeekCopy";
import { isProductOnSale } from "../data/priceTrackerUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";

type Props = {
  feedStore: PopularThisWeekStore;
  products: FeedProductView[];
  onJumpToFamily: (familyIds: string[]) => void;
};

const DEFAULT_VISIBLE = 8;

function badgeClassName(badge: string): string {
  return `popular-this-week__tag popular-this-week__tag--${badge.toLowerCase()}`;
}

export function PopularThisWeek({ feedStore, products, onJumpToFamily }: Props) {
  const [expanded, setExpanded] = useState(false);

  const entries = useMemo(
    () =>
      [...(POPULAR_THIS_WEEK[feedStore] ?? [])].sort(
        (a, b) => a.displayOrder - b.displayOrder,
      ),
    [feedStore],
  );

  const productById = useMemo(
    () => new Map(products.map((product) => [product.canonicalId, product])),
    [products],
  );

  const leadLine = useMemo(() => leadLineForStore(feedStore), [feedStore]);
  const strategyLine = useMemo(
    () => strategyLineForStore(feedStore),
    [feedStore],
  );
  const curatedWeekIsPreview = isPopularWeekPreview();

  if (entries.length === 0) {
    return null;
  }

  const hiddenCount = Math.max(entries.length - DEFAULT_VISIBLE, 0);
  const visibleEntries =
    expanded || hiddenCount === 0
      ? entries
      : entries.slice(0, DEFAULT_VISIBLE);

  const renderCard = (entry: PopularThisWeekEntry) => {
    const primaryId = entry.trackerFamilyIds[0];
    const product = primaryId ? productById.get(primaryId) : undefined;
    const onSale = product ? isProductOnSale(product) : false;
    const text = entry.subtitle || entry.reason;
    return (
      <button
        key={entry.title}
        type="button"
        className="popular-this-week__card"
        onClick={() => onJumpToFamily(entry.trackerFamilyIds)}
      >
        <span className="popular-this-week__card-title">{entry.title}</span>
        {entry.price ? (
          <span className="popular-this-week__card-price">{entry.price}</span>
        ) : null}
        <span className="popular-this-week__card-reason">{text}</span>
        {entry.badge ? (
          <span className={badgeClassName(entry.badge)}>{entry.badge}</span>
        ) : onSale ? (
          <span
            className={`popular-this-week__deal-badge${
              curatedWeekIsPreview
                ? " popular-this-week__deal-badge--preview"
                : ""
            }`}
          >
            {curatedWeekIsPreview ? "Preview deal" : "Deal"}
          </span>
        ) : null}
      </button>
    );
  };

  return (
    <section className="popular-this-week" aria-label="Popular picks this week">
      <header className="popular-this-week__header">
        <p className="popular-this-week__lead">{leadLine}</p>
        {strategyLine ? (
          <p className="popular-this-week__strategy">{strategyLine}</p>
        ) : null}
      </header>
      <div className="popular-this-week__grid">
        {visibleEntries.map(renderCard)}
      </div>
      {hiddenCount > 0 ? (
        <button
          type="button"
          className="popular-this-week__more"
          aria-expanded={expanded}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Show fewer deals" : `More handpicked deals (${hiddenCount})`}
        </button>
      ) : null}
    </section>
  );
}
