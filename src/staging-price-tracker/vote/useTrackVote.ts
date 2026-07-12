import { useEffect, useId, useState, type FormEvent } from "react";
import { getSupabase } from "../../lib/supabase";
import {
  defaultTrackItems,
  markItemVoted,
  MAX_SUGGESTION_LENGTH,
  normalizeItemName,
  readVotedItems,
  type TrackItem,
} from "../../lib/trackVote";

type StatusTone = "success" | "error" | "idle";

type SubmitSuggestionResult = {
  action: "voted" | "submitted" | "already_pending";
  item_id: string;
  normalized_name: string;
};

const MODERATION_SUCCESS_MESSAGE =
  "Thanks. We'll review this before adding it to the voting list.";

function formatError(error: unknown): string {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "object" && error && "message" in error
        ? String((error as { message: unknown }).message)
        : "";

  if (
    message.includes("tracker_vote_items") ||
    message.includes("vote_on_item") ||
    message.includes("submit_suggestion")
  ) {
    return "Voting isn’t set up yet. Run supabase/migrations/20260614_tracker_vote_items.sql.";
  }
  if (message.includes("60 characters")) {
    return "Suggestions must be 60 characters or fewer.";
  }
  return message || "Something went wrong. Please try again.";
}

function mapRowToTrackItem(row: {
  id: string;
  public_name: string | null;
  raw_text: string;
  normalized_name: string;
  vote_count: number | null;
}): TrackItem {
  return {
    id: row.id,
    itemName: row.public_name?.trim() || row.raw_text,
    normalizedItemName: row.normalized_name,
    voteCount: row.vote_count ?? 0,
  };
}

async function fetchTrackItems(): Promise<TrackItem[]> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from("tracker_vote_items")
    .select("id, public_name, raw_text, normalized_name, vote_count")
    .eq("status", "approved")
    .order("vote_count", { ascending: false })
    .order("public_name", { ascending: true })
    .order("raw_text", { ascending: true });

  if (error) {
    throw error;
  }

  return (data ?? []).map(mapRowToTrackItem);
}

async function voteOnItem(itemId: string): Promise<void> {
  const supabase = getSupabase();
  const { error } = await supabase.rpc("vote_on_item", {
    p_item_id: itemId,
  });

  if (error) {
    throw error;
  }
}

async function submitSuggestion(rawText: string): Promise<SubmitSuggestionResult> {
  const supabase = getSupabase();
  const { data, error } = await supabase.rpc("submit_suggestion", {
    p_raw_text: rawText,
  });

  if (error) {
    throw error;
  }

  return data as SubmitSuggestionResult;
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

export function useTrackVote() {
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
    if (votedItems.has(item.normalizedItemName) || pendingVote || !item.id) {
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
      await voteOnItem(item.id);
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

  async function handleCustomSuggest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = customItem.trim();
    if (!trimmed || pendingSuggest) {
      return;
    }

    if (trimmed.length > MAX_SUGGESTION_LENGTH) {
      setStatusTone("error");
      setStatusMessage("Suggestions must be 60 characters or fewer.");
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
        setStatusMessage("You already voted for this item.");
        return;
      }

      const result = await submitSuggestion(trimmed);

      if (result.action === "voted") {
        const previousItems = items;
        const existing =
          items.find((item) => item.normalizedItemName === normalized) ??
          ({
            id: result.item_id,
            itemName: trimmed.replace(/\s+/g, " "),
            normalizedItemName: normalized,
            voteCount: 0,
          } satisfies TrackItem);

        const optimisticTarget = {
          ...existing,
          voteCount: existing.voteCount + 1,
        };

        setItems((current) => upsertTrackItem(current, optimisticTarget));
        try {
          markItemVoted(normalized);
          setVotedItems((current) => new Set([...current, normalized]));
          setCustomItem("");
          setStatusTone("success");
          setStatusMessage("Vote counted. Thanks!");
        } catch (error) {
          setItems(previousItems);
          throw error;
        }
        return;
      }

      setCustomItem("");
      setStatusTone("success");
      setStatusMessage(MODERATION_SUCCESS_MESSAGE);
    } catch (error) {
      setStatusTone("error");
      setStatusMessage(formatError(error));
    } finally {
      setPendingSuggest(false);
    }
  }

  return {
    inputId,
    items,
    votedItems,
    customItem,
    setCustomItem,
    loading,
    pendingVote,
    pendingSuggest,
    statusTone,
    statusMessage,
    handleVote,
    handleCustomSuggest,
  };
}
