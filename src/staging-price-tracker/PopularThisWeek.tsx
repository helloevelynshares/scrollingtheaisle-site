import { useMemo } from "react";
import {
  POPULAR_THIS_WEEK,
  type PopularThisWeekEntry,
  type PopularThisWeekStore,
} from "../data/canonicalTrackerFamilies";
import {
  categorySlug,
  groupByHandpickedCategory,
} from "../data/handpickedCategoryReport";
import {
  leadLineForStore,
  strategyLineForStore,
} from "../data/popularThisWeekCopy";
import { formatComparisonUnit } from "../data/priceComparisonUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import {
  formatPrice,
  getCurrentPrice,
  getDealAdjustedUnitPrice,
} from "../data/priceTrackerUtils";

type Props = {
  feedStore: PopularThisWeekStore;
  products: FeedProductView[];
  onJumpToFamily: (familyIds: string[]) => void;
};

type ReportItem = {
  key: string;
  entry: PopularThisWeekEntry;
  unitPrice: string;
  canJump: boolean;
};

function unitPriceDisplay(product: FeedProductView): string {
  const dealUnit = getDealAdjustedUnitPrice(product);
  if (dealUnit) {
    const unit = formatComparisonUnit(dealUnit.unit);
    return `$${dealUnit.price.toFixed(2)}/${unit}`;
  }

  const comparison = product.priceComparison;
  if (comparison?.groceryUnitPrice != null) {
    const unit = formatComparisonUnit(
      comparison.groceryUnitType ?? comparison.costcoUnitType,
    );
    return `$${comparison.groceryUnitPrice.toFixed(2)}/${unit}`;
  }

  const price = getCurrentPrice(product);
  if (price != null && product.sizeLabel) {
    return `${formatPrice(price)} · ${product.sizeLabel}`;
  }

  return price != null ? formatPrice(price) : "";
}

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

  const reportItems = useMemo((): ReportItem[] => {
    return entries.map((entry) => {
      const primaryId = entry.trackerFamilyIds[0];
      const product = primaryId ? productById.get(primaryId) : undefined;
      return {
        key: primaryId || entry.title,
        entry,
        unitPrice: product ? unitPriceDisplay(product) : "",
        canJump: entry.trackerFamilyIds.length > 0,
      };
    });
  }, [entries, productById]);

  const groups = useMemo(
    () =>
      groupByHandpickedCategory(reportItems, (item) => item.entry.badge),
    [reportItems],
  );

  const leadLine = useMemo(() => leadLineForStore(feedStore), [feedStore]);
  const strategyLine = useMemo(
    () => strategyLineForStore(feedStore),
    [feedStore],
  );

  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="popular-this-week" aria-label="Popular picks this week">
      <header className="popular-this-week__header">
        <p className="popular-this-week__lead">{leadLine}</p>
        {strategyLine ? (
          <p className="popular-this-week__strategy">{strategyLine}</p>
        ) : null}
      </header>

      <div className="hub-picks-report">
        <div className="hub-picks-cat-columns">
          {[...groups.entries()].map(([category, items]) => {
            const slug = categorySlug(category);
            return (
              <section
                key={category}
                className={`hub-picks-cat-section hub-picks-cat-section--${slug}`}
                aria-labelledby={`tracker-picks-cat-${slug}`}
              >
                <header className="hub-picks-cat-header">
                  <h3
                    id={`tracker-picks-cat-${slug}`}
                    className="hub-picks-cat-title"
                  >
                    {category}
                  </h3>
                  <span className="hub-picks-cat-count">{items.length}</span>
                </header>
                <div className="hub-picks-cat-items">
                  {items.map((item) => {
                    const { entry, unitPrice, canJump, key } = item;
                    const note = entry.subtitle || entry.reason;
                    return (
                      <article key={key} className="hub-picks-cat-item">
                        <div className="hub-picks-cat-item-top">
                          <h4 className="hub-picks-cat-item-title">
                            {entry.title}
                          </h4>
                          {entry.price ? (
                            <p className="hub-picks-cat-item-price">
                              <span className="hub-picks-cat-amount">
                                {entry.price}
                              </span>
                              {unitPrice ? (
                                <span className="hub-picks-cat-unit">
                                  {unitPrice}
                                </span>
                              ) : null}
                            </p>
                          ) : null}
                        </div>
                        {note ? (
                          <p className="hub-picks-cat-item-note">{note}</p>
                        ) : null}
                        {canJump ? (
                          <button
                            type="button"
                            className="hub-picks-cat-link"
                            onClick={() =>
                              onJumpToFamily(entry.trackerFamilyIds)
                            }
                          >
                            See price history →
                          </button>
                        ) : null}
                      </article>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </section>
  );
}
