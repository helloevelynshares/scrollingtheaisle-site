import { Fragment, useState } from "react";
import type { GroceryFamily } from "./mockData";
import { RECOMMENDATION_HEADLINES } from "./mockData";
import { MOCK_CHART_PRODUCTS } from "./mockChartData";
import {
  CaveatNote,
  CompactFamilyCard,
  DetailsToggle,
  FamilyCardHeader,
  FamilyPriceBlock,
  FamilyPriceChart,
  FamilySummary,
  FamilyTakeaway,
  GroupedBadge,
  GroupingTrustPanel,
  IncludedVarietiesHint,
  StatusBadge,
  StockUpBadge,
  VariantList,
} from "./ui";

/** Option 1: Minimal family tracker cards */
export function Option1({ families }: { families: GroceryFamily[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <div className="ftl-option ftl-option-1">
      {families.map((family) => {
        const isOpen = expanded[family.id] ?? false;
        return (
          <article key={family.id} className="ftl-card ftl-card--minimal">
            <FamilyCardHeader family={family} />
            <FamilyPriceBlock family={family} />
            <StockUpBadge rating={family.stockUp} />
            <FamilySummary family={family} />
            <DetailsToggle
              expanded={isOpen}
              onToggle={() =>
                setExpanded((prev) => ({ ...prev, [family.id]: !isOpen }))
              }
            />
            {isOpen ? <VariantList family={family} /> : null}
          </article>
        );
      })}
    </div>
  );
}

/** Option 2: Family card with subtle included-varieties drawer */
export function Option2({ families }: { families: GroceryFamily[] }) {
  const [drawerId, setDrawerId] = useState<string | null>(null);

  return (
    <div className="ftl-option ftl-option-2">
      {families.map((family) => {
        const isOpen = drawerId === family.id;
        return (
          <article key={family.id} className="ftl-card">
            <FamilyCardHeader family={family} />
            <FamilyPriceBlock family={family} />
            <StockUpBadge rating={family.stockUp} />
            <FamilySummary family={family} />
            <FamilyTakeaway family={family} />
            <IncludedVarietiesHint
              onClick={() => setDrawerId(isOpen ? null : family.id)}
            />
            {isOpen ? (
              <div className="ftl-drawer">
                <VariantList family={family} />
              </div>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

/** Option 3: "Grouped this week" visual */
export function Option3({ families }: { families: GroceryFamily[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <div className="ftl-option ftl-option-3">
      {families.map((family) => {
        const isOpen = expanded[family.id] ?? false;
        return (
          <article key={family.id} className="ftl-card">
            <div className="ftl-card-top-row">
              <FamilyCardHeader family={family} />
              <GroupedBadge grouped={family.groupedThisWeek} />
            </div>
            <FamilyPriceBlock family={family} />
            <StockUpBadge rating={family.stockUp} />
            <FamilySummary family={family} />
            <DetailsToggle
              expanded={isOpen}
              label="Why grouped?"
              expandedLabel="Hide grouping info"
              onToggle={() =>
                setExpanded((prev) => ({ ...prev, [family.id]: !isOpen }))
              }
            />
            {isOpen ? <GroupingTrustPanel family={family} /> : null}
            {isOpen ? <VariantList family={family} /> : null}
          </article>
        );
      })}
    </div>
  );
}

/** Option 4: Homepage-style compact feed */
export function Option4({ families }: { families: GroceryFamily[] }) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const active = families.find((f) => f.id === activeId);

  return (
    <div className="ftl-option ftl-option-4">
      <div className="ftl-feed">
        {families.map((family) => (
          <CompactFamilyCard
            key={family.id}
            family={family}
            onSelect={() =>
              setActiveId((prev) => (prev === family.id ? null : family.id))
            }
          />
        ))}
      </div>
      {active ? (
        <article className="ftl-card ftl-feed-detail">
          <FamilyCardHeader family={active} />
          <FamilyPriceBlock family={active} />
          <StockUpBadge rating={active.stockUp} />
          <FamilyTakeaway family={active} />
          <CaveatNote text={active.caveat} />
          <VariantList family={active} />
        </article>
      ) : (
        <p className="ftl-hint">Tap a card to see included varieties.</p>
      )}
    </div>
  );
}

/** Option 5: Family-first detail page */
export function Option5({ families }: { families: GroceryFamily[] }) {
  const [detailId, setDetailId] = useState<string | null>(null);
  const [variantsOpen, setVariantsOpen] = useState(false);
  const family = families.find((f) => f.id === detailId);

  return (
    <div className="ftl-option ftl-option-5">
      <div className="ftl-family-grid">
        {families.map((f) => (
          <button
            key={f.id}
            type="button"
            className={`ftl-family-pick${detailId === f.id ? " ftl-family-pick--active" : ""}`}
            onClick={() => {
              setDetailId(f.id);
              setVariantsOpen(false);
            }}
          >
            <strong>{f.displayName}</strong>
            <span>{f.saleLabel}</span>
            <StockUpBadge rating={f.stockUp} />
          </button>
        ))}
      </div>

      {family ? (
        <div className="ftl-detail-page" role="dialog" aria-label={`${family.displayName} details`}>
          <button
            type="button"
            className="ftl-detail-close"
            onClick={() => setDetailId(null)}
          >
            Close
          </button>
          <h3 className="ftl-detail-heading">{family.displayName}</h3>
          <StatusBadge status={family.status} />
          <FamilyPriceBlock family={family} />
          <StockUpBadge rating={family.stockUp} />
          <FamilySummary family={family} />
          <FamilyTakeaway family={family} />
          <CaveatNote text={family.caveat} />
          <DetailsToggle
            expanded={variantsOpen}
            label="Included varieties"
            expandedLabel="Hide varieties"
            onToggle={() => setVariantsOpen((v) => !v)}
          />
          {variantsOpen ? <VariantList family={family} /> : null}
        </div>
      ) : (
        <p className="ftl-hint">Select a family to open its detail view.</p>
      )}
    </div>
  );
}

/** Option 6: Caveat-first but still simple */
export function Option6({ families }: { families: GroceryFamily[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <div className="ftl-option ftl-option-6">
      {families.map((family) => {
        const isOpen = expanded[family.id] ?? false;
        return (
          <article key={family.id} className="ftl-card ftl-card--caveat">
            <FamilyCardHeader family={family} />
            <FamilyPriceBlock family={family} />
            <StockUpBadge rating={family.stockUp} />
            <CaveatNote text={family.caveat} />
            <FamilySummary family={family} />
            <FamilyTakeaway family={family} />
            <DetailsToggle
              expanded={isOpen}
              label="See included varieties"
              expandedLabel="Hide varieties"
              onToggle={() =>
                setExpanded((prev) => ({ ...prev, [family.id]: !isOpen }))
              }
            />
            {isOpen ? <VariantList family={family} /> : null}
          </article>
        );
      })}
    </div>
  );
}

/** Option 7: Collapsed family rows */
export function Option7({ families }: { families: GroceryFamily[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <div className="ftl-option ftl-option-7">
      <div className="ftl-table-wrap">
        <table className="ftl-family-table">
          <thead>
            <tr>
              <th scope="col">Family</th>
              <th scope="col">Deal</th>
              <th scope="col">Stock-up</th>
              <th scope="col">Status</th>
              <th scope="col" aria-label="Expand" />
            </tr>
          </thead>
          <tbody>
            {families.map((family) => {
              const isOpen = expanded[family.id] ?? false;
              return (
                <Fragment key={family.id}>
                  <tr className="ftl-family-row">
                    <td className="ftl-family-row-name">{family.displayName}</td>
                    <td>{family.saleLabel}</td>
                    <td>{family.stockUp}</td>
                    <td>
                      <StatusBadge status={family.status} />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="ftl-expand-btn"
                        aria-expanded={isOpen}
                        aria-label={`${isOpen ? "Collapse" : "Expand"} ${family.displayName}`}
                        onClick={() =>
                          setExpanded((prev) => ({
                            ...prev,
                            [family.id]: !isOpen,
                          }))
                        }
                      >
                        {isOpen ? "▾" : "▸"}
                      </button>
                    </td>
                  </tr>
                  {isOpen ? (
                    <tr className="ftl-family-row-detail">
                      <td colSpan={5}>
                        <FamilySummary family={family} />
                        <FamilyTakeaway family={family} />
                        <CaveatNote text={family.caveat} />
                        <VariantList family={family} />
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/** Option 9: Option 2 + family-level price graph (combined prototype) */
export function Option9({ families }: { families: GroceryFamily[] }) {
  const [drawerId, setDrawerId] = useState<string | null>(null);

  return (
    <div className="ftl-option ftl-option-9">
      {families.map((family) => {
        const isOpen = drawerId === family.id;
        const chartProduct = MOCK_CHART_PRODUCTS[family.id];
        return (
          <article key={family.id} className="ftl-card ftl-card--with-chart">
            <FamilyCardHeader family={family} />
            <FamilyPriceBlock family={family} />
            <StockUpBadge rating={family.stockUp} />
            <FamilySummary family={family} />
            {chartProduct ? <FamilyPriceChart product={chartProduct} /> : null}
            <FamilyTakeaway family={family} />
            <IncludedVarietiesHint
              onClick={() => setDrawerId(isOpen ? null : family.id)}
            />
            {isOpen ? (
              <div className="ftl-drawer">
                <VariantList family={family} />
              </div>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

/** Option 8: "What to buy this week" recommendation cards */
export function Option8({ families }: { families: GroceryFamily[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <div className="ftl-option ftl-option-8">
      {families.map((family) => {
        const isOpen = expanded[family.id] ?? false;
        const headline = RECOMMENDATION_HEADLINES[family.id] ?? family.displayName;
        return (
          <article key={family.id} className="ftl-card ftl-rec-card">
            <p className="ftl-rec-kicker">This week</p>
            <h3 className="ftl-rec-headline">{headline}</h3>
            <p className="ftl-rec-family">{family.displayName}</p>
            <FamilyPriceBlock family={family} />
            <StockUpBadge rating={family.stockUp} />
            <FamilyTakeaway family={family} />
            <DetailsToggle
              expanded={isOpen}
              label="Why this recommendation"
              expandedLabel="Hide details"
              onToggle={() =>
                setExpanded((prev) => ({ ...prev, [family.id]: !isOpen }))
              }
            />
            {isOpen ? (
              <div className="ftl-rec-detail">
                <FamilySummary family={family} />
                <CaveatNote text={family.caveat} />
                <VariantList family={family} />
              </div>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}
