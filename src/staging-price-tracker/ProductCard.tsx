import type { ReactNode } from "react";
import {
  countWeeklyAdMatches,
  formatDiscount,
  formatDiscountVsBaseline,
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
  compact = false,
}: {
  children: ReactNode;
  tone: "accent" | "muted" | "success";
  compact?: boolean;
}) {
  return (
    <span
      className={`price-tracker-badge price-tracker-badge--${tone}${
        compact ? " price-tracker-badge--compact" : ""
      }`}
    >
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
      <div className="price-tracker-card-compact price-tracker-mobile-only">
        <header className="price-tracker-card-compact-header">
          <h2>{product.displayName}</h2>
          <div className="price-tracker-card-compact-badges">
            {product.confidence === "high" ? (
              <Badge tone="success" compact>
                High
              </Badge>
            ) : null}
            {product.costcoComparable ? (
              <Badge tone="accent" compact>
                Costco
              </Badge>
            ) : null}
          </div>
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
        <div className="price-tracker-badges">
          <Badge tone={product.confidence === "high" ? "success" : "muted"}>
            {product.confidence} confidence
          </Badge>
          {product.costcoComparable && (
            <Badge tone="accent">Costco comparable</Badge>
          )}
        </div>
      </header>

      <p className="price-tracker-product-meta price-tracker-desktop-only">
        {product.acceptedProduct.productName}
        {product.acceptedProduct.size ? ` · ${product.acceptedProduct.size}` : ""}
      </p>

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

      <p className="price-tracker-card-compact-footer price-tracker-mobile-only">
        Matched {adMatches}/{product.weeklyPrices.length} weeks
      </p>

      {latestWeek ? (
        <p className="price-tracker-source price-tracker-source--muted price-tracker-desktop-only">
          Latest week: {latestWeek.sourceLabel}
          {latestWeek.isBaselineFallback
            ? " · not in this week's ad (using baseline)"
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
