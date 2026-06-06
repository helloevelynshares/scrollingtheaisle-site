import type { ReactNode } from "react";
import {
  countWeeklyAdMatches,
  formatDiscount,
  formatPrice,
  getCurrentPrice,
  getDiscountPercent,
  getLatestWeeklyAd,
  getLowestObservedPrice,
  type TrackedProduct,
} from "../data/priceTrackerV1";
import { PriceTrendChart } from "./PriceTrendChart";

type Props = {
  product: TrackedProduct;
};

function Badge({
  children,
  tone,
}: {
  children: ReactNode;
  tone: "accent" | "muted" | "success";
}) {
  return (
    <span className={`price-tracker-badge price-tracker-badge--${tone}`}>
      {children}
    </span>
  );
}

export function ProductCard({ product }: Props) {
  const current = getCurrentPrice(product);
  const lowest = getLowestObservedPrice(product);
  const discount = getDiscountPercent(product);
  const latestWeek = getLatestWeeklyAd(product);
  const adMatches = countWeeklyAdMatches(product);

  return (
    <article className="price-tracker-card">
      <header className="price-tracker-card-header">
        <h2>{product.displayName}</h2>
        <div className="price-tracker-badges">
          <Badge tone={product.confidence === "high" ? "success" : "muted"}>
            {product.confidence} confidence
          </Badge>
          {product.costcoComparable && (
            <Badge tone="accent">Costco comparable</Badge>
          )}
        </div>
      </header>

      <p className="price-tracker-product-meta">
        {product.acceptedProduct.productName}
        {product.acceptedProduct.size ? ` · ${product.acceptedProduct.size}` : ""}
      </p>

      <dl className="price-tracker-stats">
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

      {latestWeek ? (
        <p className="price-tracker-source price-tracker-source--muted">
          Latest week: {latestWeek.sourceLabel}
          {latestWeek.isBaselineFallback
            ? " · no high-confidence ad match (using baseline)"
            : latestWeek.offerText
              ? ` · ${latestWeek.offerText}`
              : ""}
          {" · "}
          {adMatches} of {product.weeklyPrices.length} weeks matched in ads
        </p>
      ) : null}
    </article>
  );
}
