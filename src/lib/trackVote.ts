export const TRACK_VOTE_STORAGE_KEY = "sta_track_votes";
export const MAX_SUGGESTION_LENGTH = 60;

export const SEED_TRACK_ITEMS = [
  "Berries",
  "Grapes",
  "Chicken breast",
  "Oreos",
  "Ritz crackers",
  "Kettle chips",
] as const;

export type TrackItem = {
  id: string | null;
  itemName: string;
  normalizedItemName: string;
  voteCount: number;
};

export function normalizeItemName(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function readVotedItems(): Set<string> {
  try {
    const raw = localStorage.getItem(TRACK_VOTE_STORAGE_KEY);
    if (!raw) {
      return new Set();
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return new Set();
    }
    return new Set(parsed.filter((value) => typeof value === "string"));
  } catch {
    return new Set();
  }
}

export function markItemVoted(normalizedItemName: string): void {
  const voted = readVotedItems();
  voted.add(normalizedItemName);
  localStorage.setItem(TRACK_VOTE_STORAGE_KEY, JSON.stringify([...voted]));
}

export function defaultTrackItems(): TrackItem[] {
  return SEED_TRACK_ITEMS.map((itemName) => ({
    id: null,
    itemName,
    normalizedItemName: normalizeItemName(itemName),
    voteCount: 0,
  }));
}

export function formatVoteLabel(itemName: string, voteCount: number): string {
  return `${itemName} ▲ ${voteCount}`;
}
