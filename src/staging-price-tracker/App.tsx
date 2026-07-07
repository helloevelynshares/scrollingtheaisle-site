import { useCallback, useEffect, useMemo, useState } from "react";
import { DEFAULT_FEED_ID, getPriceFeed } from "../data/priceFeeds";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { fetchFeedProducts } from "../lib/priceTrackerApi";
import { FeedTabs } from "./FeedTabs";
import { SectionedTrackerList } from "./SectionedTrackerList";

function feedIdFromUrl(): string {
  const feed = new URLSearchParams(window.location.search).get("feed");
  return feed && getPriceFeed(feed) ? feed : DEFAULT_FEED_ID;
}

export function App() {
  const [activeFeedId, setActiveFeedId] = useState(feedIdFromUrl);
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

  const activeFeed = products[0];
  const feedStore = useMemo<"safeway" | "vons">(
    () =>
      activeFeedId === "vons_albertsons_socal" ? "vons" : "safeway",
    [activeFeedId],
  );

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
            Track weekly prices for grocery staples across local store feeds.
            Switch tabs to see what&apos;s happening near you.
          </p>
        </section>

        <FeedTabs activeFeedId={activeFeedId} onChange={setActiveFeedId} />

        {activeFeed ? (
          <p className="price-tracker-feed-context">
            Showing {activeFeed.feedLabel} · {activeFeed.regionLabel}
          </p>
        ) : null}

        {loading ? (
          <p className="price-tracker-loading">Loading prices…</p>
        ) : (
          <SectionedTrackerList products={products} feedStore={feedStore} />
        )}
      </main>
    </>
  );
}
