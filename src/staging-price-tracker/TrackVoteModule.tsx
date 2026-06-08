import { useEffect, useId, useState, type FormEvent } from "react";
import { getSupabase, getVisitorId } from "../lib/supabase";
import {
  defaultTrackItems,
  formatVoteLabel,
  markItemVoted,
  normalizeItemName,
  readVotedItems,
  type TrackItem,
} from "../lib/trackVote";

type StatusTone = "success" | "error" | "idle";

function formatError(error: unknown): string {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "object" && error && "message" in error
        ? String((error as { message: unknown }).message)
        : "";

  if (
    message.includes("product_track_suggestions") ||
    message.includes("product_track_votes") ||
    message.includes("product_track_suggestion_totals")
  ) {
    return "Voting isn’t set up yet. Run supabase/migrations/20260608_product_track_voting.sql.";
  }
  if (message.includes("duplicate key") || message.includes("unique")) {
    return "You already voted for this item.";
  }
  return message || "Something went wrong. Please try again.";
}

async function fetchTrackItems(): Promise<TrackItem[]> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from("product_track_suggestion_totals")
    .select("id, item_name, normalized_item_name, vote_count")
    .order("vote_count", { ascending: false })
    .order("item_name", { ascending: true });

  if (error) {
    throw error;
  }

  return (data ?? []).map((row) => ({
    id: row.id,
    itemName: row.item_name,
    normalizedItemName: row.normalized_item_name,
    voteCount: row.vote_count ?? 0,
  }));
}

async function insertVote(item: TrackItem): Promise<void> {
  if (!item.id) {
    throw new Error("Suggestion is not available yet.");
  }

  const supabase = getSupabase();
  const normalized = item.normalizedItemName;
  const { error } = await supabase.from("product_track_votes").insert({
    suggestion_id: item.id,
    item_name: item.itemName,
    normalized_item_name: normalized,
    vote_source: "tracker_module",
    anonymous_user_key: getVisitorId(),
  });

  if (error) {
    throw error;
  }
}

async function findSuggestionByNormalized(
  normalizedItemName: string,
): Promise<TrackItem | null> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from("product_track_suggestions")
    .select("id, item_name, normalized_item_name")
    .eq("normalized_item_name", normalizedItemName)
    .maybeSingle();

  if (error) {
    throw error;
  }
  if (!data) {
    return null;
  }

  return {
    id: data.id,
    itemName: data.item_name,
    normalizedItemName: data.normalized_item_name,
    voteCount: 0,
  };
}

async function createSuggestion(itemName: string, normalizedItemName: string): Promise<TrackItem> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from("product_track_suggestions")
    .insert({
      item_name: itemName,
      normalized_item_name: normalizedItemName,
      source: "tracker_module",
    })
    .select("id, item_name, normalized_item_name")
    .single();

  if (error) {
    throw error;
  }

  return {
    id: data.id,
    itemName: data.item_name,
    normalizedItemName: data.normalized_item_name,
    voteCount: 0,
  };
}

function sortTrackItems(items: TrackItem[]): TrackItem[] {
  return [...items].sort((a, b) => {
    if (b.voteCount !== a.voteCount) {
      return b.voteCount - a.voteCount;
    }
    return a.itemName.localeCompare(b.itemName);
  });
}

function upsertTrackItem(items: TrackItem[], next: TrackItem): TrackItem[] {
  const existingIndex = items.findIndex(
    (item) => item.normalizedItemName === next.normalizedItemName,
  );
  if (existingIndex === -1) {
    return sortTrackItems([...items, next]);
  }
  const updated = [...items];
  updated[existingIndex] = {
    ...updated[existingIndex],
    ...next,
    voteCount: Math.max(updated[existingIndex].voteCount, next.voteCount),
  };
  return sortTrackItems(updated);
}

export function TrackVoteModule() {
  const inputId = useId();
  const [items, setItems] = useState<TrackItem[]>(defaultTrackItems());
  const [votedItems, setVotedItems] = useState<Set<string>>(() => readVotedItems());
  const [customItem, setCustomItem] = useState("");
  const [loading, setLoading] = useState(true);
  const [pendingVote, setPendingVote] = useState<string | null>(null);
  const [pendingSuggest, setPendingSuggest] = useState(false);
  const [statusTone, setStatusTone] = useState<StatusTone>("idle");
  const [statusMessage, setStatusMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadItems() {
      try {
        const fetched = await fetchTrackItems();
        if (!cancelled && fetched.length > 0) {
          setItems(fetched);
        }
      } catch {
        if (!cancelled) {
          setItems(defaultTrackItems());
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadItems();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleVote(item: TrackItem) {
    if (votedItems.has(item.normalizedItemName) || pendingVote) {
      return;
    }

    const previousItems = items;
    setStatusTone("idle");
    setStatusMessage("");
    setPendingVote(item.normalizedItemName);
    setItems((current) =>
      sortTrackItems(
        current.map((entry) =>
          entry.normalizedItemName === item.normalizedItemName
            ? { ...entry, voteCount: entry.voteCount + 1 }
            : entry,
        ),
      ),
    );

    try {
      await insertVote(item);
      markItemVoted(item.normalizedItemName);
      setVotedItems((current) => new Set([...current, item.normalizedItemName]));
    } catch (error) {
      setItems(previousItems);
      setStatusTone("error");
      setStatusMessage(formatError(error));
    } finally {
      setPendingVote(null);
    }
  }

  async function resolveSuggestion(
    trimmed: string,
    normalized: string,
  ): Promise<TrackItem> {
    const existing =
      items.find((item) => item.normalizedItemName === normalized) ??
      (await findSuggestionByNormalized(normalized));

    if (existing) {
      return existing;
    }

    const displayName = trimmed.replace(/\s+/g, " ");
    try {
      return await createSuggestion(displayName, normalized);
    } catch (error) {
      const message = formatError(error);
      if (message.includes("duplicate") || message.includes("unique")) {
        const fallback = await findSuggestionByNormalized(normalized);
        if (fallback) {
          return fallback;
        }
      }
      throw error;
    }
  }

  async function handleCustomSuggest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = customItem.trim();
    if (!trimmed || pendingSuggest) {
      return;
    }

    const normalized = normalizeItemName(trimmed);
    if (!normalized) {
      return;
    }

    setPendingSuggest(true);
    setStatusTone("idle");
    setStatusMessage("");

    try {
      if (votedItems.has(normalized)) {
        setCustomItem("");
        setStatusTone("success");
        setStatusMessage("Added — thanks!");
        return;
      }

      const previousItems = items;
      const target = await resolveSuggestion(trimmed, normalized);
      const optimisticTarget = {
        ...target,
        voteCount: target.voteCount + 1,
      };

      setItems((current) => upsertTrackItem(current, optimisticTarget));
      try {
        await insertVote(target);
      } catch (error) {
        setItems(previousItems);
        throw error;
      }
      markItemVoted(normalized);
      setVotedItems((current) => new Set([...current, normalized]));
      setCustomItem("");
      setStatusTone("success");
      setStatusMessage("Added — thanks!");
    } catch (error) {
      setStatusTone("error");
      setStatusMessage(formatError(error));
    } finally {
      setPendingSuggest(false);
    }
  }

  return (
    <section
      id="track-vote"
      className="price-tracker-vote"
      aria-labelledby="price-tracker-vote-title"
    >
      <h2 id="price-tracker-vote-title">What should we track next?</h2>
      <p className="price-tracker-vote-lead">
        Vote for an item you want added to the tracker, or suggest your own.
      </p>

      <div className="price-tracker-vote-grid" role="list">
        {items.map((item) => {
          const voted = votedItems.has(item.normalizedItemName);
          const isPending = pendingVote === item.normalizedItemName;
          return (
            <button
              key={item.id ?? item.normalizedItemName}
              type="button"
              role="listitem"
              className={`price-tracker-vote-card${voted ? " price-tracker-vote-card--voted" : ""}`}
              onClick={() => void handleVote(item)}
              disabled={voted || Boolean(pendingVote) || loading || !item.id}
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

      <form className="price-tracker-vote-custom" onSubmit={handleCustomSuggest}>
        <label htmlFor={inputId}>Suggest another item</label>
        <div className="price-tracker-vote-custom-row">
          <input
            id={inputId}
            type="text"
            value={customItem}
            onChange={(event) => setCustomItem(event.target.value)}
            placeholder="e.g. grapes, Ritz crackers, protein bars"
            autoComplete="off"
            disabled={pendingSuggest}
          />
          <button
            type="submit"
            className="btn btn-primary btn-sm"
            disabled={pendingSuggest || !customItem.trim()}
          >
            {pendingSuggest ? "Adding…" : "Suggest item"}
          </button>
        </div>
      </form>

      {statusMessage ? (
        <p
          className={`price-tracker-vote-status price-tracker-vote-status--${statusTone}`}
          role="status"
          aria-live="polite"
        >
          {statusMessage}
        </p>
      ) : null}
    </section>
  );
}
