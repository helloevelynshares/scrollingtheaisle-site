import { useCallback, useMemo, useState } from "react";
import { HOMEPAGE_SECTIONS } from "../data/canonicalTrackerFamilies";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { ProductCard } from "./ProductCard";
import { PopularThisWeek } from "./PopularThisWeek";
import { partitionSectionProducts } from "./sectionShowMore";
import { TrackVotePanel } from "./vote/TrackVotePanel";

type Props = {
  products: FeedProductView[];
  feedStore: "safeway" | "vons";
};

export function SectionedTrackerList({ products, feedStore }: Props) {
  const [search, setSearch] = useState("");
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    () => new Set(),
  );
  const [highlightIds, setHighlightIds] = useState<Set<string>>(new Set());

  const normalizedSearch = search.trim().toLowerCase();
  const bypassCollapse = normalizedSearch.length > 0;

  const filteredProducts = useMemo(() => {
    let list = products;
    if (normalizedSearch) {
      list = list.filter((product) => {
        const haystack = [
          product.displayName,
          product.subtitle,
          product.sizeLabel,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return haystack.includes(normalizedSearch);
      });
    }
    if (activeSection) {
      list = list.filter((product) => product.homepageSection === activeSection);
    }
    return list;
  }, [products, normalizedSearch, activeSection]);

  const productsBySection = useMemo(() => {
    const map = new Map<string, FeedProductView[]>();
    for (const section of HOMEPAGE_SECTIONS) {
      const sectionProducts = filteredProducts
        .filter((product) => product.homepageSection === section.id)
        .sort((a, b) => (a.displayOrder ?? 999) - (b.displayOrder ?? 999));
      map.set(section.id, sectionProducts);
    }
    return map;
  }, [filteredProducts]);

  const handleJumpToFamily = useCallback((familyIds: string[]) => {
    const firstId = familyIds[0];
    if (!firstId) {
      return;
    }
    const target = document.getElementById(`tracker-${firstId}`);
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
    setHighlightIds(new Set(familyIds));
    window.setTimeout(() => setHighlightIds(new Set()), 2400);
  }, []);

  const expandSection = useCallback((sectionId: string) => {
    setExpandedSections((current) => {
      const next = new Set(current);
      next.add(sectionId);
      return next;
    });
  }, []);

  const controls = (
    <div className="sectioned-tracker__controls">
      <label className="sectioned-tracker__search-label">
        <span className="visually-hidden">Search trackers</span>
        <input
          type="search"
          className="sectioned-tracker__search"
          placeholder="Search items…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </label>
      <div className="sectioned-tracker__chips" role="toolbar" aria-label="Section filters">
        <button
          type="button"
          className={`sectioned-tracker__chip${activeSection === null ? " sectioned-tracker__chip--active" : ""}`}
          onClick={() => setActiveSection(null)}
        >
          All
        </button>
        {HOMEPAGE_SECTIONS.map((section) => (
          <button
            key={section.id}
            type="button"
            className={`sectioned-tracker__chip${activeSection === section.id ? " sectioned-tracker__chip--active" : ""}`}
            onClick={() =>
              setActiveSection((current) =>
                current === section.id ? null : section.id,
              )
            }
          >
            {section.label}
          </button>
        ))}
      </div>
    </div>
  );

  const sections = HOMEPAGE_SECTIONS.map((section) => {
    const sectionProducts = productsBySection.get(section.id) ?? [];
    if (activeSection && activeSection !== section.id) {
      return null;
    }
    if (sectionProducts.length === 0 && !normalizedSearch) {
      return (
        <section
          key={section.id}
          className="price-tracker-section price-tracker-section--grouped price-tracker-section--empty"
          aria-label={section.label}
        >
          <header className="price-tracker-section-header">
            <h2 className="price-tracker-section-title">{section.label}</h2>
          </header>
          <p className="price-tracker-empty-state">
            No items in this section match your filters yet.
          </p>
        </section>
      );
    }
    if (sectionProducts.length === 0) {
      return null;
    }

    const isExpanded = expandedSections.has(section.id);
    const { visible: visibleProducts, hiddenCount } = partitionSectionProducts(
      section.id,
      sectionProducts,
      isExpanded,
      bypassCollapse,
    );

    return (
      <section
        key={section.id}
        className="price-tracker-section price-tracker-section--grouped"
        aria-label={section.label}
      >
        <header className="price-tracker-section-header">
          <h2 className="price-tracker-section-title">{section.label}</h2>
        </header>
        <div className="price-tracker-grid">
          {visibleProducts.map((product) => (
            <div
              key={product.canonicalId}
              id={`tracker-${product.canonicalId}`}
              className={
                highlightIds.has(product.canonicalId)
                  ? "tracker-card-wrap tracker-card-wrap--highlight"
                  : "tracker-card-wrap"
              }
            >
              <ProductCard product={product} />
            </div>
          ))}
        </div>
        {!isExpanded && hiddenCount > 0 ? (
          <button
            type="button"
            className="sectioned-tracker__show-more"
            onClick={() => expandSection(section.id)}
          >
            Show more ({hiddenCount})
          </button>
        ) : null}
      </section>
    );
  });

  return (
    <div className="sectioned-tracker">
      {controls}
      <PopularThisWeek
        feedStore={feedStore}
        products={products}
        onJumpToFamily={handleJumpToFamily}
      />
      <TrackVotePanel id="track-vote" />
      {sections}
    </div>
  );
}
