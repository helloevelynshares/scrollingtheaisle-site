import {
  hasChartableData,
  toSentenceCase,
} from "../data/priceTrackerUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { FamilyDealCard } from "./FamilyDealCard";

type Props = {
  product: FeedProductView;
};

export function ProductCard({ product }: Props) {
  if (!hasChartableData(product)) {
    return (
      <article className="price-tracker-card price-tracker-card--empty">
        <header className="price-tracker-card-header">
          <h2>{product.displayName}</h2>
          {product.subtitle || product.sizeLabel ? (
            <p className="price-tracker-product-meta">
              {toSentenceCase(product.subtitle ?? product.sizeLabel ?? "")}
            </p>
          ) : null}
        </header>
        <p className="price-tracker-empty-state">
          Tracking soon. No {product.feedLabel} prices for{" "}
          {product.regionLabel} yet.
        </p>
      </article>
    );
  }

  return <FamilyDealCard product={product} />;
}
