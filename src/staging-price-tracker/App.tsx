import { useCallback, useEffect, useMemo, useState } from "react";
import {
  isRecurringCrossStoreProduct,
} from "../data/canonicalProducts";
import { isTrackerFamilyId } from "../data/trackerFamilies";
import { DEFAULT_FEED_ID } from "../data/priceFeeds";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { fetchFeedProducts } from "../lib/priceTrackerApi";
import { FeedTabs } from "./FeedTabs";
import { ProductCard } from "./ProductCard";
import { TrackVoteModule } from "./TrackVoteModule";

function splitProducts(products: FeedProductView[]) {
  const original: FeedProductView[] = [];
  const recurring: FeedProductView[] = [];
  const families: FeedProductView[] = [];

  for (const product of products) {
    if (isTrackerFamilyId(product.canonicalId)) {
      families.push(product);
    } else if (isRecurringCrossStoreProduct(product.canonicalId)) {
      recurring.push(product);
    } else {
      original.push(product);
    }
  }

  return { original, recurring, families };
}

type ProductGridProps = {
  products: FeedProductView[];
};

function ProductGrid({ products }: ProductGridProps) {
  return (
    <div className="price-tracker-grid">
      {products.map((product) => (
        <ProductCard key={product.canonicalId} product={product} />
      ))}
    </div>
  );
}

export function App() {
  const [activeFeedId, setActiveFeedId] = useState(DEFAULT_FEED_ID);
  const [products, setProducts] = useState<FeedProductView[]>([]);
  const [loading, setLoading] = useState(true);

  const loadFeed = useCallback(async (feedId: string) => {
    setLoading(true);
    const rows = await fetchFeedProducts(feedId);
    setProducts(rows);
    setLoading(false);
  }, []);

  useEffect(() => {
    void loadFeed(activeFeedId);
  }, [activeFeedId, loadFeed]);

  const { original, recurring, families } = useMemo(
    () => splitProducts(products),
    [products],
  );

  const activeFeed = products[0];

  return (
    <>
      <header className="page-header">
        <a href="/" className="brand">
          SCROLLING THE AISLE
        </a>
        <nav className="site-nav" aria-label="Main">
          <a href="/about.html" className="site-nav-link">
            About
          </a>
          <a href="/finds.html" className="site-nav-link">
            Finds
          </a>
          <a
            href="/staging-price-tracker/"
            className="site-nav-link site-nav-link--active"
            aria-current="page"
          >
            Price tracker
          </a>
        </nav>
      </header>

      <main className="page-main price-tracker-main">
        <section className="price-tracker-hero">
          <h1>Price Tracker</h1>
          <p className="price-tracker-subtitle">
            Track weekly prices for the same grocery staples across local store
            feeds. Switch tabs to see what&apos;s happening near you.
          </p>
        </section>

        <FeedTabs activeFeedId={activeFeedId} onChange={setActiveFeedId} />

        {activeFeed ? (
          <p className="price-tracker-feed-context">
            Showing {activeFeed.feedLabel} · {activeFeed.regionLabel}
          </p>
        ) : null}

        <TrackVoteModule />

        {loading ? (
          <p className="price-tracker-loading">Loading prices…</p>
        ) : (
          <>
            {original.length > 0 ? (
              <section
                className="price-tracker-section"
                aria-label="Tracked grocery staples"
              >
                <ProductGrid products={original} />
              </section>
            ) : null}

            {recurring.length > 0 ? (
              <section
                className="price-tracker-section price-tracker-section--recurring"
                aria-label="Recurring cross-store items"
              >
                <header className="price-tracker-section-header">
                  <h2 className="price-tracker-section-title">
                    Recurring items we keep seeing across stores
                  </h2>
                  <p className="price-tracker-section-subtitle">
                    These are the staples and snack deals that keep popping up
                    week after week across Costco, Safeway, Vons, and
                    Albertsons.
                  </p>
                </header>
                <ProductGrid products={recurring} />
              </section>
            ) : null}
            {families.length > 0 ? (
              <section
                className="price-tracker-section price-tracker-section--families"
                aria-label="Curated deal families"
              >
                <header className="price-tracker-section-header">
                  <h2 className="price-tracker-section-title">
                    Deals grouped the way shoppers think
                  </h2>
                  <p className="price-tracker-section-subtitle">
                    When a sale covers a bunch of flavors or sizes, I group them
                    together and call out where the better deal is.
                  </p>
                </header>
                <ProductGrid products={families} />
              </section>
            ) : null}
          </>
        )}
      </main>
    </>
  );
}
