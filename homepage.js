/**
 * Homepage hub — curated popular picks (Safeway / Vons toggle).
 * Price data: data/homepage-preview.generated.json (npm run generate:homepage-preview)
 */

const PREVIEW_JSON = "data/homepage-preview.generated.json";
const TRACKER_URL = "staging-price-tracker/";
const STORE_VOTE_STORAGE_KEY = "sta_store_votes";
const SUPABASE_URL = "https://wurmdtqysegytsjcudve.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_8Wt-it-oIHHIkQOi0D9y_g_qMoH51ZX";
const TRACKER_URLS = {
  safeway: `${TRACKER_URL}?feed=safeway_bay_area`,
  vons: `${TRACKER_URL}?feed=vons_albertsons_socal`,
};

const VIEW_CONFIG = {
  safeway: {
    title: "Scrolling the Aisle's highlights of the week",
    lead: "Hand-picked deals I'm watching at Safeway this week.",
    picksKey: "popularPicksSafeway",
    store: "Safeway",
    trackerUrl: TRACKER_URLS.safeway,
  },
  vons: {
    title: "Scrolling the Aisle's highlights of the week",
    lead: "Hand-picked deals I'm watching at Vons this week.",
    picksKey: "popularPicksVons",
    store: "Vons",
    trackerUrl: TRACKER_URLS.vons,
  },
};

const BADGE_CLASS = {
  "Stock up": "hub-badge--stock-up",
  "Good small-pack buy": "hub-badge--good-buy",
  "Costco still wins": "hub-badge--costco",
  Wait: "hub-badge--wait",
  "Lowest seen recently": "hub-badge--low",
  "Beats Costco": "hub-badge--beats",
  "About normal": "hub-badge--normal",
};

let previewData = null;
let activeView = "safeway";

function escapeHtml(text) {
  if (text == null || text === "") return "";
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

async function loadPreviewData() {
  try {
    const res = await fetch(PREVIEW_JSON, { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    previewData = await res.json();
  } catch (err) {
    console.warn("Homepage preview JSON unavailable", err);
    previewData = null;
  }
}

function badgeHtml(badge) {
  const cls = BADGE_CLASS[badge] || "hub-badge--normal";
  return `<span class="hub-badge ${cls}">${escapeHtml(badge)}</span>`;
}

function picksForView(view) {
  if (!previewData) return [];
  const config = VIEW_CONFIG[view];
  if (!config) return [];
  return previewData[config.picksKey] ?? [];
}

function leadLineForView(view) {
  const config = VIEW_CONFIG[view];
  if (!config) return "";
  const week = previewData?.popularWeekLabel;
  const curated = week
    ? `Curated by Scrolling the Aisle · week of ${week}`
    : "Curated by Scrolling the Aisle";
  return `${config.lead} · ${curated}`;
}

function renderDealCard(pick) {
  const dealBadge =
    pick.onSale && !pick.isPlaceholder
      ? '<span class="hub-badge hub-badge--deal">Deal</span>'
      : "";

  return `
    <article class="hub-deal-card${pick.isPlaceholder ? " hub-deal-card--placeholder" : ""}">
      <div class="hub-deal-card-top">
        <h3 class="hub-deal-card-title">${escapeHtml(pick.name)}</h3>
        ${dealBadge || badgeHtml(pick.badge)}
      </div>
      <p class="hub-deal-card-price">
        <span class="hub-deal-card-amount">${escapeHtml(pick.price)}</span>
        <span class="hub-deal-card-store">${escapeHtml(pick.store)}</span>
      </p>
      <p class="hub-deal-card-unit">${escapeHtml(pick.unitPrice)}</p>
      <p class="hub-deal-card-note">${escapeHtml(pick.explanation)}</p>
      <a href="${escapeHtml(pick.trackerUrl || TRACKER_URL)}" class="hub-deal-card-link">See price history →</a>
    </article>
  `;
}

function renderPicksGrid() {
  const grid = document.getElementById("picks-grid");
  const titleEl = document.getElementById("picks-title");
  const leadEl = document.getElementById("picks-lead");
  if (!grid) return;

  const config = VIEW_CONFIG[activeView] ?? VIEW_CONFIG.safeway;
  const picks = picksForView(activeView);

  if (titleEl) titleEl.textContent = config.title;
  if (leadEl) leadEl.textContent = leadLineForView(activeView);

  if (picks.length === 0) {
    grid.innerHTML = `<p class="hub-empty">Weekly picks loading soon — check the <a href="${TRACKER_URL}">price tracker</a>.</p>`;
    return;
  }

  grid.innerHTML = picks.map(renderDealCard).join("");
}

function setActiveView(view) {
  if (!VIEW_CONFIG[view]) return;
  activeView = view;

  document.querySelectorAll(".hub-picks-toggle-btn").forEach((btn) => {
    const isActive = btn.dataset.view === view;
    btn.classList.toggle("is-active", isActive);
    btn.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  renderPicksGrid();
}

function initPicksToggle() {
  document.querySelectorAll(".hub-picks-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      setActiveView(btn.dataset.view);
    });
  });
}

async function initHomepage() {
  await loadPreviewData();
  initPicksToggle();
  renderPicksGrid();
  initStoreSuggestModule();
}

/* —— Store vote module (homepage hero) —— */

let supabaseClient = null;
/** @type {Map<string, { id: string, voteCount: number }>} */
let storeVoteItems = new Map();
let storeVoteLoading = true;
let storePendingVote = null;
let storePendingSuggest = false;

function getSupabase() {
  if (!supabaseClient && window.supabase) {
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return supabaseClient;
}

function normalizeStoreName(name) {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function readVotedStores() {
  try {
    const raw = localStorage.getItem(STORE_VOTE_STORAGE_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return new Set();
    return new Set(parsed.filter((value) => typeof value === "string"));
  } catch {
    return new Set();
  }
}

function markStoreVoted(normalizedName) {
  const voted = readVotedStores();
  voted.add(normalizedName);
  localStorage.setItem(STORE_VOTE_STORAGE_KEY, JSON.stringify([...voted]));
}

function formatStoreVoteError(error) {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "object" && error && "message" in error
        ? String(error.message)
        : "";

  if (
    message.includes("store_vote_items") ||
    message.includes("vote_on_store") ||
    message.includes("submit_store_suggestion")
  ) {
    return "Store voting isn't set up yet. Apply supabase/migrations/20260707_store_vote_items.sql.";
  }
  return message || "Something went wrong. Please try again.";
}

function showStoreStatus(message, isError = false) {
  const el = document.getElementById("store-suggest-status");
  if (!el) return;
  el.textContent = message;
  el.hidden = false;
  el.classList.toggle("hub-store-status--error", isError);
}

function hideStoreStatus() {
  const el = document.getElementById("store-suggest-status");
  if (!el) return;
  el.hidden = true;
  el.textContent = "";
  el.classList.remove("hub-store-status--error");
}

function updateChipStates(votedStores) {
  document.querySelectorAll(".hub-store-chip").forEach((chip) => {
    const store = chip.dataset.store;
    const normalized = store ? normalizeStoreName(store) : "";
    const voted = Boolean(normalized && votedStores.has(normalized));
    chip.classList.toggle("is-voted", voted);
    chip.setAttribute("aria-pressed", voted ? "true" : "false");
    chip.disabled = voted || Boolean(storePendingVote) || storePendingSuggest;
  });
}

function bumpStoreVoteCount(normalizedName) {
  const entry = storeVoteItems.get(normalizedName);
  if (!entry) return;
  entry.voteCount += 1;
  storeVoteItems.set(normalizedName, entry);
}

function formatStoreVoteLabel(name, voteCount) {
  return voteCount > 0 ? `${name} ▲ ${voteCount}` : name;
}

function renderStoreChips() {
  document.querySelectorAll(".hub-store-chip").forEach((chip) => {
    const store = chip.dataset.store;
    if (!store) return;
    const normalized = normalizeStoreName(store);
    const item = storeVoteItems.get(normalized);
    const count = item?.voteCount ?? 0;
    chip.textContent = formatStoreVoteLabel(store, count);
  });
  updateChipStates(readVotedStores());
}

async function fetchStoreVoteItems() {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("store_vote_items unavailable");
  }

  const { data, error } = await supabase
    .from("store_vote_items")
    .select("id, public_name, raw_text, normalized_name, vote_count")
    .eq("status", "approved")
    .order("vote_count", { ascending: false })
    .order("public_name", { ascending: true })
    .order("raw_text", { ascending: true });

  if (error) {
    throw error;
  }

  const next = new Map();
  for (const row of data ?? []) {
    next.set(row.normalized_name, {
      id: row.id,
      voteCount: row.vote_count ?? 0,
      label: row.public_name?.trim() || row.raw_text,
    });
  }
  storeVoteItems = next;
}

async function voteOnStoreItem(itemId) {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("vote_on_store unavailable");
  }

  const { error } = await supabase.rpc("vote_on_store", {
    p_item_id: itemId,
  });

  if (error) {
    throw error;
  }
}

async function submitStoreSuggestion(storeName, city) {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("submit_store_suggestion unavailable");
  }

  const { data, error } = await supabase.rpc("submit_store_suggestion", {
    p_store_name: storeName,
    p_city: city || null,
  });

  if (error) {
    throw error;
  }

  return data;
}

async function handleStoreChipVote(chip) {
  const store = chip.dataset.store?.trim();
  if (!store || storePendingVote || storePendingSuggest) return;

  const normalized = normalizeStoreName(store);
  const votedStores = readVotedStores();
  if (votedStores.has(normalized)) {
    showStoreStatus("You already voted for this store.");
    return;
  }

  const item = storeVoteItems.get(normalized);

  hideStoreStatus();
  storePendingVote = normalized;
  updateChipStates(votedStores);
  if (item) {
    bumpStoreVoteCount(normalized);
    renderStoreChips();
  }

  try {
    if (item?.id) {
      await voteOnStoreItem(item.id);
    } else {
      const result = await submitStoreSuggestion(store, null);
      if (result?.action === "voted") {
        storeVoteItems.set(normalized, {
          id: result.item_id,
          voteCount: (item?.voteCount ?? 0) + 1,
          label: store,
        });
        renderStoreChips();
      } else {
        if (item) {
          const entry = storeVoteItems.get(normalized);
          if (entry) {
            entry.voteCount = Math.max(0, entry.voteCount - 1);
            storeVoteItems.set(normalized, entry);
            renderStoreChips();
          }
        }
        showStoreStatus("Thanks — we'll review this before adding it to the voting list.");
        return;
      }
    }

    markStoreVoted(normalized);
    showStoreStatus(`Vote counted for ${store}. Thanks!`);
  } catch (error) {
    if (item) {
      const entry = storeVoteItems.get(normalized);
      if (entry) {
        entry.voteCount = Math.max(0, entry.voteCount - 1);
        storeVoteItems.set(normalized, entry);
        renderStoreChips();
      }
    }
    showStoreStatus(formatStoreVoteError(error), true);
  } finally {
    storePendingVote = null;
    updateChipStates(readVotedStores());
  }
}

async function handleStoreFormSubmit(event) {
  event.preventDefault();
  if (storePendingSuggest || storePendingVote) return;

  const form = event.currentTarget;
  const storeInput = form.querySelector('input[name="store"]');
  const cityInput = form.querySelector('input[name="city"]');
  const store = storeInput?.value?.trim() ?? "";
  const city = cityInput?.value?.trim() ?? "";

  if (!store) {
    showStoreStatus("Please enter a store name.", true);
    storeInput?.focus();
    return;
  }

  const normalized = normalizeStoreName(store);
  const votedStores = readVotedStores();

  hideStoreStatus();
  storePendingSuggest = true;
  updateChipStates(votedStores);

  try {
    if (votedStores.has(normalized)) {
      showStoreStatus("You already voted for this store.");
      form.reset();
      return;
    }

    const result = await submitStoreSuggestion(store, city);

    if (result?.action === "voted") {
      markStoreVoted(normalized);
      if (storeVoteItems.has(normalized)) {
        bumpStoreVoteCount(normalized);
      } else {
        storeVoteItems.set(normalized, {
          id: result.item_id,
          voteCount: 1,
          label: store,
        });
      }
      renderStoreChips();
      form.reset();
      showStoreStatus("Vote counted — thanks!");
      return;
    }

    form.reset();
    showStoreStatus("Thanks — we'll review this before adding it to the voting list.");
  } catch (error) {
    showStoreStatus(formatStoreVoteError(error), true);
  } finally {
    storePendingSuggest = false;
    updateChipStates(readVotedStores());
  }
}

function initStoreChipPicker() {
  document.querySelectorAll(".hub-store-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      void handleStoreChipVote(chip);
    });
  });
}

async function initStoreSuggestModule() {
  const module = document.getElementById("store-suggest-module");
  if (!module) return;

  initStoreChipPicker();
  renderStoreChips();

  const form = document.getElementById("store-custom-form");
  form?.addEventListener("submit", handleStoreFormSubmit);

  try {
    await fetchStoreVoteItems();
    renderStoreChips();
  } catch {
    /* Chips can still submit via RPC when migration is applied. */
  } finally {
    storeVoteLoading = false;
    renderStoreChips();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  void initHomepage();
});
