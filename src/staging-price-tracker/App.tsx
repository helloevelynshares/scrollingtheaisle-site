import { trackedProducts } from "../data/priceTrackerV1";
import { ProductCard } from "./ProductCard";
import { TrackVoteModule } from "./TrackVoteModule";

export function App() {
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
          <h1>Safeway Price Tracker</h1>
          <p className="price-tracker-subtitle">
            Track weekly price changes on grocery staples and spot better deals
            before your next Costco or grocery run.
          </p>
        </section>

        <TrackVoteModule />

        <div className="price-tracker-grid">
          {trackedProducts.map((product) => (
            <ProductCard key={product.canonicalId} product={product} />
          ))}
        </div>
      </main>
    </>
  );
}
