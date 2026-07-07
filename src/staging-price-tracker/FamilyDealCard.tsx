/**
 * Family Deal Card — production UI for grouped deal families (Family Tracker UI Lab Option 9).
 * Family-level price + chart first; included varieties live in a secondary drawer.
 */
import { useState } from "react";
import {
  computeFeedProductBenchmark,
  formatPrice,
  getFamilyBuyWaitTakeaway,
  getFamilyCostcoComparisonDetails,
  getFamilyEffectivePriceLabel,
  getFamilyExpandedFootnote,
  getFamilyExpandedRows,
  getFamilyExpandedSectionTitle,
  getFamilyPricingBehavior,
  getFamilyStatus,
  getFamilyStockUpRating,
  getFamilySummary,
  getFamilyUsuallyLabel,
  getFamilyUsuallyRangeLabel,
  getFamilyVariantNote,
  hasFamilyVarieties,
  isDealFamily,
  isProductOnSale,
  type FamilyStockUpRating,
  type FamilyStatus,
} from "../data/priceTrackerUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { ComparisonBadge } from "./ComparisonBadge";
import { PriceTrendChart } from "./PriceTrendChart";

type Props = {
  product: FeedProductView;
};

function FamilyStatusBadge({ status }: { status: FamilyStatus }) {
  const tone = status === "Promo deal this week" ? "promo" : "sale";
  return (
    <span className={`family-deal-card__status family-deal-card__status--${tone}`}>
      {status}
    </span>
  );
}

function FamilyStockUpBadge({ rating }: { rating: FamilyStockUpRating }) {
  const tone =
    rating === "Great" || rating === "Great if buying full promo quantity"
      ? "great"
      : "good";
  return (
    <span className={`family-deal-card__stock-up family-deal-card__stock-up--${tone}`}>
      Stock-up: {rating}
    </span>
  );
}

function FamilyVarietiesDrawer({ product }: { product: FeedProductView }) {
  const title = getFamilyExpandedSectionTitle(product);
  const rows = getFamilyExpandedRows(product);
  const footnote = getFamilyExpandedFootnote(product);
  const costco = getFamilyCostcoComparisonDetails(product);
  const variantNote = getFamilyVariantNote(product);
  const pricingBehavior = getFamilyPricingBehavior(product);

  return (
    <div className="family-deal-card__drawer">
      <div className="family-deal-card__variants">
        <p className="family-deal-card__section-label">{title}</p>
        <p className="family-deal-card__variant-note">{variantNote}</p>
        <ul className="family-deal-card__variant-list">
          {rows.map((row) => (
            <li key={row.label} className="family-deal-card__variant-item">
              <span className="family-deal-card__variant-name">{row.label}</span>
              <span className="family-deal-card__variant-meta">{row.detail}</span>
            </li>
          ))}
        </ul>
        {footnote ? (
          <p className="family-deal-card__variant-footnote">{footnote}</p>
        ) : null}
        <p className="family-deal-card__pricing-behavior">
          <span className="family-deal-card__pricing-behavior-label">
            Grouping logic:
          </span>{" "}
          {pricingBehavior}
        </p>
      </div>

      {costco ? (
        <div className="family-deal-card__costco">
          <p className="family-deal-card__section-label">Costco comparison</p>
          {costco.locationNote ? (
            <p className="family-deal-card__costco-location">{costco.locationNote}</p>
          ) : null}
          <p className="family-deal-card__costco-intro">{costco.intro}</p>
          <dl className="family-deal-card__costco-rows">
            <div>
              <dt>Costco</dt>
              <dd>
                <span>{costco.costcoLabel}</span>
                <span className="family-deal-card__costco-math">
                  {costco.costcoDetail}
                </span>
              </dd>
            </div>
            <div>
              <dt>{product.feedLabel}</dt>
              <dd>
                <span>{costco.groceryLabel}</span>
                <span className="family-deal-card__costco-math">
                  {costco.groceryDetail}
                </span>
              </dd>
            </div>
          </dl>
          <p className="family-deal-card__costco-verdict">
            <strong>Verdict:</strong> {costco.verdict}
          </p>
        </div>
      ) : null}
    </div>
  );
}

export function FamilyDealCard({ product }: Props) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const status = getFamilyStatus(product);
  const saleLabel = getFamilyUsuallyLabel(product);
  const effectivePrice = getFamilyEffectivePriceLabel(product);
  const usualRange = getFamilyUsuallyRangeLabel(product);
  const stockUp = getFamilyStockUpRating(product);
  const summary = getFamilySummary(product);
  const takeaway = getFamilyBuyWaitTakeaway(product);
  const showVarietiesHint = hasFamilyVarieties(product);
  const onSale = isProductOnSale(product);
  const productMeta = product.subtitle ?? product.sizeLabel;

  const benchmark = computeFeedProductBenchmark(product);
  const atlPrice = benchmark.allTimeLowUnitPrice;
  const isAtl = benchmark.benchmarkBucket === "all-time low";
  const showAtlHint = atlPrice != null && benchmark.observationCount >= 2;

  return (
    <article className="price-tracker-card price-tracker-card--family family-deal-card">
      <header className="family-deal-card__header">
        <div>
          <h2>{product.displayName}</h2>
          {productMeta && !isDealFamily(product) ? (
            <p className="price-tracker-product-meta">{productMeta}</p>
          ) : null}
        </div>
        {status ? <FamilyStatusBadge status={status} /> : null}
      </header>

      <div className="family-deal-card__price-block">
        <p
          className={`family-deal-card__sale${
            onSale ? " family-deal-card__sale--deal" : ""
          }`}
        >
          {saleLabel}
        </p>
        {usualRange ? (
          <p className="family-deal-card__usual">{usualRange}</p>
        ) : null}
        {showAtlHint ? (
          <p
            className={`family-deal-card__atl-hint${
              isAtl ? " family-deal-card__atl-hint--match" : ""
            }`}
          >
            {isAtl ? "All-time low" : "All-time low:"}{" "}
            <span className="family-deal-card__atl-price">
              {formatPrice(atlPrice)}
            </span>
          </p>
        ) : null}
      </div>

      <div className="family-deal-card__chart">
        <PriceTrendChart product={product} />
      </div>

      {!showVarietiesHint ? (
        <ComparisonBadge
          activeFeedId={product.feedId}
          activeGroceryLabel={product.feedLabel}
          comparison={product.priceComparison}
          familyBadge={product.familyComparisonBadge ?? undefined}
        />
      ) : null}

      <p
        className={`family-deal-card__takeaway family-deal-card__takeaway--${takeaway.tone}`}
      >
        {takeaway.label}
      </p>

      <button
        type="button"
        className={`family-deal-card__details-toggle${
          detailsOpen ? " family-deal-card__details-toggle--open" : ""
        }`}
        aria-expanded={detailsOpen}
        onClick={() => setDetailsOpen((o) => !o)}
      >
        {detailsOpen ? "Less" : "Details"}
      </button>

      {detailsOpen ? (
        <div className="family-deal-card__details-panel">
          <FamilyStockUpBadge rating={stockUp} />
          {effectivePrice ? (
            <p className="family-deal-card__effective">{effectivePrice}</p>
          ) : null}
          <p className="family-deal-card__summary">{summary}</p>
        </div>
      ) : null}

      {showVarietiesHint ? (
        <button
          type="button"
          className="family-deal-card__varieties-hint"
          aria-expanded={drawerOpen}
          onClick={() => setDrawerOpen((open) => !open)}
        >
          Includes multiple flavors / varieties
        </button>
      ) : null}

      {drawerOpen && showVarietiesHint ? (
        <FamilyVarietiesDrawer product={product} />
      ) : null}
    </article>
  );
}
