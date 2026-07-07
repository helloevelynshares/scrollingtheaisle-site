import { useMemo } from "react";
import {
  POPULAR_THIS_WEEK,
  POPULAR_THIS_WEEK_WEEK,
  type PopularThisWeekStore,
} from "../data/canonicalTrackerFamilies";
import { isProductOnSale, isProductInPreviewWeek } from "../data/priceTrackerUtils";
import { getFeedAdPreviewState } from "../data/weeklyAdPreview";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { WEEKLY_AD_WEEKS } from "../data/weeklyAdPrices.generated";
import { VONS_WEEKLY_AD_WEEKS } from "../data/vonsWeeklyAdPrices.generated";

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

  const previewState = getFeedAdPreviewState(
    feedStore === "vons" ? VONS_WEEKLY_AD_WEEKS : WEEKLY_AD_WEEKS,
  );
  const sectionLabel = previewState?.isPreview
    ? "Popular in upcoming ad"
    : "Popular this week";

  return (
    <section className="popular-this-week" aria-label={sectionLabel}>
      <header className="popular-this-week__header">
        <h2 className="popular-this-week__title">{sectionLabel}</h2>
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
                <span
                  className={`popular-this-week__deal-badge${
                    product && isProductInPreviewWeek(product)
                      ? " popular-this-week__deal-badge--preview"
                      : ""
                  }`}
                >
                  {product && isProductInPreviewWeek(product) ? "Preview deal" : "Deal"}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
    </section>
  );
}
