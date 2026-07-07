import { formatVoteLabel, type TrackItem } from "../../lib/trackVote";
import { useTrackVote } from "./useTrackVote";

type Props = {
  id?: string;
  className?: string;
  maxVisibleItems?: number;
};

function visibleItems(items: TrackItem[], max: number): TrackItem[] {
  if (max >= items.length) {
    return items;
  }
  return items.slice(0, max);
}

export function TrackVotePanel({
  id = "track-vote",
  className = "",
  maxVisibleItems = 6,
}: Props) {
  const vote = useTrackVote();
  const shownItems = visibleItems(vote.items, maxVisibleItems);
  const headingId = `${id}-title`;

  const rootClass = ["price-tracker-vote", className].filter(Boolean).join(" ");

  return (
    <section
      id={id}
      className={rootClass}
      aria-labelledby={headingId}
    >
      <p id={headingId} className="price-tracker-vote-label">
        Help pick what we track next.
      </p>

      <div className="price-tracker-vote-strip" role="list">
        {shownItems.map((item) => {
          const voted = vote.votedItems.has(item.normalizedItemName);
          const isPending = vote.pendingVote === item.normalizedItemName;
          return (
            <button
              key={item.id ?? item.normalizedItemName}
              type="button"
              role="listitem"
              className={`price-tracker-vote-card${voted ? " price-tracker-vote-card--voted" : ""}`}
              onClick={() => void vote.handleVote(item)}
              disabled={
                voted || Boolean(vote.pendingVote) || vote.loading || !item.id
              }
              aria-pressed={voted}
            >
              <span className="price-tracker-vote-card-label">
                {formatVoteLabel(item.itemName, item.voteCount)}
              </span>
              {voted ? (
                <span className="price-tracker-vote-card-note">Voted</span>
              ) : isPending ? (
                <span className="price-tracker-vote-card-note">Saving…</span>
              ) : null}
            </button>
          );
        })}
      </div>

      <form
        className="price-tracker-vote-custom price-tracker-vote-custom--inline"
        onSubmit={vote.handleCustomSuggest}
      >
        <label htmlFor={vote.inputId} className="visually-hidden">
          Suggest another item
        </label>
        <div className="price-tracker-vote-custom-row">
          <input
            id={vote.inputId}
            type="text"
            value={vote.customItem}
            onChange={(event) => vote.setCustomItem(event.target.value)}
            placeholder="Suggest something else…"
            autoComplete="off"
            maxLength={60}
            disabled={vote.pendingSuggest}
          />
          <button
            type="submit"
            className="btn btn-primary btn-sm price-tracker-vote-submit"
            disabled={vote.pendingSuggest || !vote.customItem.trim()}
          >
            {vote.pendingSuggest ? "Submitting…" : "Suggest"}
          </button>
        </div>
      </form>

      {vote.statusMessage ? (
        <p
          className={`price-tracker-vote-status price-tracker-vote-status--${vote.statusTone}`}
          role="status"
          aria-live="polite"
        >
          {vote.statusMessage}
        </p>
      ) : null}
    </section>
  );
}
