import {
  formatDiscount,
  formatDiscountVsBaseline,
  formatPrice,
  getCurrentPrice,
  getDiscountPercent,
  getEffectiveBaseline,
  getLowestObservedPrice,
  hasChartableData,
} from "../data/priceTrackerUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { ComparisonBadge } from "./ComparisonBadge";
import { PriceTrendChart } from "./PriceTrendChart";

type Props = {
  product: FeedProductView;
};

export function ProductCard({ product }: Props) {
  if (!hasChartableData(product)) {
    return (
      <article className="price-tracker-card price-tracker-card--empty">
        <header className="price-tracker-card-header">
          <h2>{product.displayName}</h2>
          {product.sizeLabel ? (
            <p className="price-tracker-product-meta">{product.sizeLabel}</p>
          ) : null}
        </header>
        <p className="price-tracker-empty-state">
          Tracking soon — no {product.feedLabel} prices for{" "}
          {product.regionLabel} yet.
        </p>
      </article>
    );
  }

  const current = getCurrentPrice(product);
  const lowest = getLowestObservedPrice(product);
  const discount = getDiscountPercent(product);
  const baseline = getEffectiveBaseline(product);

  return (
    <article className="price-tracker-card">
      <div className="price-tracker-card-compact price-tracker-mobile-only">
        <header className="price-tracker-card-compact-header">
          <h2>{product.displayName}</h2>
        </header>

        <div className="price-tracker-card-compact-price">
          <span className="price-tracker-card-compact-current">
            {formatPrice(current)}
          </span>
          <span
            className={`price-tracker-card-compact-vs${
              discount && discount > 0
                ? " price-tracker-card-compact-vs--deal"
                : ""
            }`}
          >
            {formatDiscountVsBaseline(discount)}
          </span>
        </div>
      </div>

      <header className="price-tracker-card-header price-tracker-desktop-only">
        <h2>{product.displayName}</h2>
        {product.sizeLabel ? (
          <p className="price-tracker-product-meta">{product.sizeLabel}</p>
        ) : null}
      </header>

      <dl className="price-tracker-stats price-tracker-desktop-only">
        <div>
          <dt>Current</dt>
          <dd className="price-tracker-stat-current">{formatPrice(current)}</dd>
        </div>
        <div>
          <dt>Baseline</dt>
          <dd>{formatPrice(baseline)}</dd>
        </div>
        <div>
          <dt>Lowest</dt>
          <dd>{formatPrice(lowest)}</dd>
        </div>
        <div>
          <dt>vs baseline</dt>
          <dd>{formatDiscount(discount)}</dd>
        </div>
      </dl>

      <ComparisonBadge
        activeFeedId={product.feedId}
        activeGroceryLabel={product.feedLabel}
        comparison={product.priceComparison}
      />

      <PriceTrendChart product={product} />
    </article>
  );
}
