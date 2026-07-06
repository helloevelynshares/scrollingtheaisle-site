import type { FeedProductView } from "../data/priceTrackerTypes";
import { PriceTrendChart } from "../staging-price-tracker/PriceTrendChart";
import type { GroceryFamily, StockUpRating } from "./mockData";

export function StockUpBadge({ rating }: { rating: StockUpRating }) {
  const tone =
    rating === "Great" || rating === "Great if buying full promo quantity"
      ? "great"
      : "good";
  return (
    <span className={`ftl-badge ftl-badge--stock ftl-badge--${tone}`}>
      Stock-up: {rating}
    </span>
  );
}

export function StatusBadge({ status }: { status: GroceryFamily["status"] }) {
  const tone = status === "Promo deal this week" ? "promo" : "sale";
  return (
    <span className={`ftl-badge ftl-badge--status ftl-badge--${tone}`}>
      {status}
    </span>
  );
}

export function GroupedBadge({ grouped }: { grouped: boolean }) {
  return (
    <span
      className={`ftl-badge ftl-badge--grouped${grouped ? "" : " ftl-badge--ungrouped"}`}
    >
      {grouped ? "Grouped this week" : "Tracked separately"}
    </span>
  );
}

export function FamilyCardHeader({ family }: { family: GroceryFamily }) {
  return (
    <header className="ftl-card-header">
      <h3>{family.displayName}</h3>
      <StatusBadge status={family.status} />
    </header>
  );
}

export function FamilyPriceBlock({ family }: { family: GroceryFamily }) {
  return (
    <div className="ftl-price-block">
      <p className="ftl-sale">{family.saleLabel}</p>
      {family.effectivePriceLabel ? (
        <p className="ftl-effective">{family.effectivePriceLabel}</p>
      ) : null}
      <p className="ftl-usual">{family.usualRange}</p>
    </div>
  );
}

export function FamilySummary({ family }: { family: GroceryFamily }) {
  return <p className="ftl-summary">{family.summary}</p>;
}

export function FamilyTakeaway({ family }: { family: GroceryFamily }) {
  return <p className="ftl-takeaway">{family.takeaway}</p>;
}

export function CaveatNote({ text }: { text?: string }) {
  if (!text) return null;
  return (
    <p className="ftl-caveat">
      <span className="ftl-caveat-label">Caveat:</span> {text}
    </p>
  );
}

export function VariantNote({ text }: { text: string }) {
  return <p className="ftl-variant-note">{text}</p>;
}

export function PricingBehaviorNote({ text }: { text: string }) {
  return (
    <p className="ftl-pricing-behavior">
      <span className="ftl-pricing-behavior-label">Grouping logic:</span> {text}
    </p>
  );
}

export function DetailsToggle({
  expanded,
  onToggle,
  label = "Details",
  expandedLabel = "Hide details",
}: {
  expanded: boolean;
  onToggle: () => void;
  label?: string;
  expandedLabel?: string;
}) {
  return (
    <button
      type="button"
      className="ftl-details-btn"
      aria-expanded={expanded}
      onClick={onToggle}
    >
      {expanded ? expandedLabel : label}
    </button>
  );
}

export function IncludedVarietiesHint({ onClick }: { onClick?: () => void }) {
  if (onClick) {
    return (
      <button type="button" className="ftl-included-hint" onClick={onClick}>
        Includes multiple flavors / varieties
      </button>
    );
  }
  return (
    <p className="ftl-included-hint ftl-included-hint--static">
      Includes multiple flavors / varieties
    </p>
  );
}

export function VariantList({ family }: { family: GroceryFamily }) {
  return (
    <div className="ftl-variants-panel">
      <p className="ftl-section-label">Included varieties</p>
      <VariantNote text={family.variantNote} />
      <ul className="ftl-variant-list">
        {family.variants.map((v) => (
          <li key={v.id} className="ftl-variant-item">
            <span className="ftl-variant-name">{v.name}</span>
            <span className="ftl-variant-meta">
              {v.size}
              {v.priceLabel !== "mix-and-match" ? ` · ${v.priceLabel}` : ""}
            </span>
          </li>
        ))}
      </ul>
      <PricingBehaviorNote text={family.pricingBehavior} />
    </div>
  );
}

export function GroupingTrustPanel({ family }: { family: GroceryFamily }) {
  return (
    <div className="ftl-grouping-panel">
      <GroupedBadge grouped={family.groupedThisWeek} />
      {family.groupedThisWeek ? (
        <p className="ftl-grouping-copy">Same sale across varieties this week.</p>
      ) : null}
      <p className="ftl-grouping-footnote">
        Tracked separately when prices differ.
      </p>
      <PricingBehaviorNote text={family.pricingBehavior} />
    </div>
  );
}

export function FamilyPriceChart({ product }: { product: FeedProductView }) {
  return (
    <div className="ftl-chart-section">
      <p className="ftl-section-label">Price history</p>
      <PriceTrendChart product={product} />
    </div>
  );
}

export function CompactFamilyCard({
  family,
  onSelect,
}: {
  family: GroceryFamily;
  onSelect?: () => void;
}) {
  const Tag = onSelect ? "button" : "article";
  return (
    <Tag
      type={onSelect ? "button" : undefined}
      className={`ftl-compact-card${onSelect ? " ftl-compact-card--clickable" : ""}`}
      onClick={onSelect}
    >
      <span className="ftl-compact-name">{family.displayName}</span>
      <span className="ftl-compact-deal">{family.saleLabel}</span>
      <StockUpBadge rating={family.stockUp} />
      <span className="ftl-compact-summary">{family.summary}</span>
    </Tag>
  );
}
