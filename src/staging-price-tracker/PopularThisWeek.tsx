import { useMemo } from "react";
import {
  POPULAR_THIS_WEEK,
  POPULAR_THIS_WEEK_WEEK,
  type PopularThisWeekStore,
} from "../data/canonicalTrackerFamilies";
import { isProductOnSale } from "../data/priceTrackerUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";

type Props = {
  feedStore: PopularThisWeekStore;
  products: FeedProductView[];
  onJumpToFamily: (familyIds: string[]) => void;
};

export function PopularThisWeek({ feedStore, products, onJumpToFamily }: Props) {
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

  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="popular-this-week" aria-label="Popular this week">
      <header className="popular-this-week__header">
        <h2 className="popular-this-week__title">Popular this week</h2>
        {POPULAR_THIS_WEEK_WEEK ? (
          <p className="popular-this-week__week">
            Week of {POPULAR_THIS_WEEK_WEEK}
          </p>
        ) : null}
      </header>
      <div className="popular-this-week__grid">
        {entries.map((entry) => {
          const primaryId = entry.trackerFamilyIds[0];
          const product = primaryId ? productById.get(primaryId) : undefined;
          const onSale = product ? isProductOnSale(product) : false;
          return (
            <button
              key={entry.title}
              type="button"
              className="popular-this-week__card"
              onClick={() => onJumpToFamily(entry.trackerFamilyIds)}
            >
              <span className="popular-this-week__card-title">{entry.title}</span>
              <span className="popular-this-week__card-reason">{entry.reason}</span>
              {onSale ? (
                <span className="popular-this-week__deal-badge">Deal</span>
              ) : null}
            </button>
          );
        })}
      </div>
    </section>
  );
}
