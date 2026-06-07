import { trackedProducts } from "../data/priceTrackerV1";
import { ProductCard } from "./ProductCard";

export function App() {
  return (
    <>
      <header className="page-header">
        <a href="/" className="brand">
          SCROLLING THE AISLE
        </a>
      </header>

      <main className="page-main price-tracker-main">
        <section className="price-tracker-hero">
          <h1>Safeway Price Tracker</h1>
          <p className="price-tracker-subtitle">
            Week-by-week prices for Costco-comparable grocery staples in the Bay
            Area.
          </p>
          <p className="price-tracker-explainer">
            Each product starts from a Safeway shelf-price baseline. When we
            find it in that week&apos;s Safeway ad, we plot the ad price; if
            it&apos;s not in the ad, the chart stays at baseline for that week.
          </p>
          <p className="price-tracker-cta">
            Want a product tracked?{" "}
            <a
              href="https://www.tiktok.com/@scrollingtheaisle"
              target="_blank"
              rel="noopener noreferrer"
            >
              DM us @scrollingtheaisle
            </a>
            .
          </p>
        </section>

        <div className="price-tracker-grid">
          {trackedProducts.map((product) => (
            <ProductCard key={product.canonicalId} product={product} />
          ))}
        </div>
      </main>

      <footer className="price-tracker-footer">
        <p>
          Prices from Safeway weekly ads · Updated when new flyers are processed
        </p>
      </footer>
    </>
  );
}
