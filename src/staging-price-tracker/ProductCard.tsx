import { useState } from "react";
import {
  formatDiscount,
  formatDiscountVsBaseline,
  formatPrice,
  getCurrentPrice,
  getDiscountPercent,
  getEffectiveBaseline,
  getFamilyCostcoComparisonDetails,
  getFamilyExpandedFootnote,
  getFamilyExpandedRows,
  getFamilyExpandedSectionTitle,
  getFamilyShopperNoteLines,
  getFamilyToggleLabel,
  getFamilyUsuallyLabel,
  getFamilyUsuallyRangeLabel,
  getFamilyValueBadges,
  getLowestObservedPrice,
  hasChartableData,
  isDealFamily,
} from "../data/priceTrackerUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { ComparisonBadge } from "./ComparisonBadge";
import { PriceTrendChart } from "./PriceTrendChart";

type Props = {
  product: FeedProductView;
};

function FamilyValueBadges({ product }: { product: FeedProductView }) {
  const badges = getFamilyValueBadges(product);
  if (badges.length === 0) {
    return null;
  }

  return (
    <div className="price-tracker-family-badges">
      {badges.map((badge) => (
        <span
          key={badge.label}
          className={`price-tracker-family-badge price-tracker-family-badge--${badge.tone}`}
        >
          {badge.label}
        </span>
      ))}
    </div>
  );
}

function FamilyExpandedDetails({ product }: { product: FeedProductView }) {
  const title = getFamilyExpandedSectionTitle(product);
  const rows = getFamilyExpandedRows(product);
  const footnote = getFamilyExpandedFootnote(product);
  const costco = getFamilyCostcoComparisonDetails(product);

  if (rows.length === 0 && !costco) {
    return null;
  }

  return (
    <>
      {rows.length > 0 ? (
        <div className="price-tracker-family-members">
          <h3 className="price-tracker-family-members-title">{title}</h3>
          <ul className="price-tracker-family-members-list">
            {rows.map((row) => (
              <li key={row.label} className="price-tracker-family-member">
                <span className="price-tracker-family-member-label">
                  {row.label}
                </span>
                <span className="price-tracker-family-member-detail">
                  {row.detail}
                </span>
              </li>
            ))}
          </ul>
          {footnote ? (
            <p className="price-tracker-family-members-footnote">{footnote}</p>
          ) : null}
        </div>
      ) : null}

      {costco ? (
        <div className="price-tracker-family-costco-comparison">
          <h3 className="price-tracker-family-members-title">
            Costco comparison
          </h3>
          <p className="price-tracker-family-costco-intro">{costco.intro}</p>
          <dl className="price-tracker-family-costco-rows">
            <div>
              <dt>Costco</dt>
              <dd>
                <span>{costco.costcoLabel}</span>
                <span className="price-tracker-family-costco-math">
                  {costco.costcoDetail}
                </span>
              </dd>
            </div>
            <div>
              <dt>{product.feedLabel}</dt>
              <dd>
                <span>{costco.groceryLabel}</span>
                <span className="price-tracker-family-costco-math">
                  {costco.groceryDetail}
                </span>
              </dd>
            </div>
          </dl>
          <p className="price-tracker-family-costco-verdict">
            <strong>Verdict:</strong> {costco.verdict}
          </p>
        </div>
      ) : null}
    </>
  );
}

function FamilyDealCard({ product }: { product: FeedProductView }) {
  const [expanded, setExpanded] = useState(false);
  const priceLabel = getFamilyUsuallyLabel(product);
  const usualRange = getFamilyUsuallyRangeLabel(product);
  const shopperLines = getFamilyShopperNoteLines(product);
  const onSale = product.salePriceRange != null;
  const hasDetails =
    getFamilyExpandedRows(product).length > 0 ||
    getFamilyCostcoComparisonDetails(product) != null;

  return (
    <article
      className={`price-tracker-card price-tracker-card--family${
        expanded ? " price-tracker-card--expanded" : ""
      }`}
    >
      <header className="price-tracker-family-header">
        <h2>{product.displayName}</h2>
        {product.subtitle ? (
          <p className="price-tracker-product-meta">{product.subtitle}</p>
        ) : null}
      </header>

      <p
        className={`price-tracker-family-usually${
          onSale ? " price-tracker-family-usually--deal" : ""
        }`}
      >
        {priceLabel}
      </p>

      {shopperLines.length > 0 ? (
        <div className="price-tracker-family-shopper-note">
          {shopperLines.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
      ) : null}

      {usualRange ? (
        <p className="price-tracker-family-usual-range">{usualRange}</p>
      ) : null}

      <FamilyValueBadges product={product} />

      <PriceTrendChart product={product} variant="sparkline" />

      {hasDetails ? (
        <button
          type="button"
          className="price-tracker-family-toggle"
          aria-expanded={expanded}
          onClick={() => setExpanded((value) => !value)}
        >
          {getFamilyToggleLabel(product, expanded)}
        </button>
      ) : null}

      {expanded ? (
        <div className="price-tracker-family-expanded">
          <FamilyExpandedDetails product={product} />
        </div>
      ) : null}
    </article>
  );
}

export function ProductCard({ product }: Props) {
  const familyCard = isDealFamily(product);

  if (!hasChartableData(product)) {
    return (
      <article className="price-tracker-card price-tracker-card--empty">
        <header className="price-tracker-card-header">
          <h2>{product.displayName}</h2>
          {product.subtitle || product.sizeLabel ? (
            <p className="price-tracker-product-meta">
              {product.subtitle ?? product.sizeLabel}
            </p>
          ) : null}
        </header>
        <p className="price-tracker-empty-state">
          Tracking soon — no {product.feedLabel} prices for{" "}
          {product.regionLabel} yet.
        </p>
      </article>
    );
  }

  if (familyCard) {
    return <FamilyDealCard product={product} />;
  }

  const current = formatPrice(getCurrentPrice(product));
  const lowest = getLowestObservedPrice(product);
  const discount = getDiscountPercent(product);
  const baseline = getEffectiveBaseline(product);

  return (
    <article className="price-tracker-card">
      <div className="price-tracker-card-compact price-tracker-mobile-only">
        <header className="price-tracker-card-compact-header">
          <h2>{product.displayName}</h2>
          {product.subtitle ? (
            <p className="price-tracker-product-meta">{product.subtitle}</p>
          ) : null}
        </header>

        <div className="price-tracker-card-compact-price">
          <span className="price-tracker-card-compact-current">{current}</span>
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
        {(product.subtitle || product.sizeLabel) ? (
          <p className="price-tracker-product-meta">{product.sizeLabel}</p>
        ) : null}
      </header>

      <dl className="price-tracker-stats price-tracker-desktop-only">
        <div>
          <dt>Current</dt>
          <dd className="price-tracker-stat-current">{current}</dd>
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
