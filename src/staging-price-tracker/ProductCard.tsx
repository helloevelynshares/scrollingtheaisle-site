import {
  formatDiscount,
  formatDiscountVsBaseline,
  formatPrice,
  getCurrentPrice,
  getDiscountPercent,
  getLowestObservedPrice,
  type TrackedProduct,
} from "../data/priceTrackerV1";
import { PriceTrendChart } from "./PriceTrendChart";

type Props = {
  product: TrackedProduct;
};

export function ProductCard({ product }: Props) {
  const current = getCurrentPrice(product);
  const lowest = getLowestObservedPrice(product);
  const discount = getDiscountPercent(product);

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
      </header>

      <dl className="price-tracker-stats price-tracker-desktop-only">
        <div>
          <dt>Current</dt>
          <dd className="price-tracker-stat-current">{formatPrice(current)}</dd>
        </div>
        <div>
          <dt>Baseline</dt>
          <dd>{formatPrice(product.baselinePrice)}</dd>
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

      <PriceTrendChart product={product} />
    </article>
  );
}
