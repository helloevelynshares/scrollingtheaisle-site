import { PRICE_FEEDS } from "../data/priceFeeds";

type Props = {
  activeFeedId: string;
  onChange: (feedId: string) => void;
};

/** Compact feed selector; feed_id controls which regional price data is shown. */
export function FeedTabs({ activeFeedId, onChange }: Props) {
  return (
    <div
      className="price-tracker-feed-tabs"
      role="tablist"
      aria-label="Store feed"
    >
      {PRICE_FEEDS.map((feed) => {
        const selected = feed.id === activeFeedId;
        return (
          <button
            key={feed.id}
            type="button"
            role="tab"
            aria-selected={selected}
            className={`price-tracker-feed-tab${
              selected ? " price-tracker-feed-tab--active" : ""
            }`}
            onClick={() => onChange(feed.id)}
          >
            <span className="price-tracker-feed-tab-label">{feed.label}</span>
            <span className="price-tracker-feed-tab-region">{feed.regionLabel}</span>
          </button>
        );
      })}
    </div>
  );
}
