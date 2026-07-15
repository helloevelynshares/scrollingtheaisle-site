/**
 * Homepage hub: curated popular picks (Safeway / Vons toggle).
 * Price data: data/homepage-preview.generated.json (npm run generate:homepage-preview)
 */

const PREVIEW_JSON = "/data/homepage-preview.generated.json";
const TRACKER_URL = "grocery-price-tracker/";
const STORE_VOTE_STORAGE_KEY = "sta_store_votes";
const COUPON_CHECK_STORAGE_KEY = "sta_coupon_check_votes";
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

const BADGE_TO_CATEGORY = {
  friday: "Friday",
  produce: "Produce",
  meat: "Meat",
  snacks: "Snacks",
  variety: "Variety",
  deal: "Other Deals",
};

const CATEGORY_ORDER = [
  "Friday",
  "Produce",
  "Meat",
  "Snacks",
  "Variety",
  "Other Deals",
];

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

function categoryForPick(pick) {
  const raw = String(pick.customBadge || "")
    .trim()
    .toLowerCase();
  return BADGE_TO_CATEGORY[raw] || "Other Deals";
}

function groupPicksByCategory(picks) {
  const groups = new Map(CATEGORY_ORDER.map((name) => [name, []]));
  for (const pick of picks) {
    const cat = categoryForPick(pick);
    if (!groups.has(cat)) groups.set(cat, []);
    groups.get(cat).push(pick);
  }
  for (const [key, list] of [...groups.entries()]) {
    if (list.length === 0) groups.delete(key);
  }
  return groups;
}

function renderCategoryPick(pick) {
  const placeholder = pick.isPlaceholder ? " is-placeholder" : "";
  const trackerLink = pick.isPlaceholder
    ? ""
    : `<a href="${escapeHtml(pick.trackerUrl || TRACKER_URL)}" class="hub-picks-cat-link">See price history →</a>`;
  return `
    <article class="hub-picks-cat-item${placeholder}">
      <div class="hub-picks-cat-item-top">
        <h4 class="hub-picks-cat-item-title">${escapeHtml(pick.name)}</h4>
        <p class="hub-picks-cat-item-price">
          <span class="hub-picks-cat-amount">${escapeHtml(pick.price)}</span>
          ${
            pick.unitPrice
              ? `<span class="hub-picks-cat-unit">${escapeHtml(pick.unitPrice)}</span>`
              : ""
          }
        </p>
      </div>
      <p class="hub-picks-cat-item-note">${escapeHtml(pick.explanation)}</p>
      ${trackerLink}
    </article>
  `;
}

function renderPicksReport(picks) {
  if (picks.length === 0) {
    return `<p class="hub-empty">Weekly picks loading soon. Check the <a href="${TRACKER_URL}">price tracker</a>.</p>`;
  }

  const groups = groupPicksByCategory(picks);
  const sections = [];

  for (const [category, items] of groups) {
    const slug = category.toLowerCase().replace(/\s+/g, "-");
    sections.push(`
      <section class="hub-picks-cat-section hub-picks-cat-section--${slug}" aria-labelledby="picks-cat-${slug}">
        <header class="hub-picks-cat-header">
          <h3 id="picks-cat-${slug}" class="hub-picks-cat-title">${escapeHtml(category)}</h3>
          <span class="hub-picks-cat-count">${items.length}</span>
        </header>
        <div class="hub-picks-cat-items">${items.map(renderCategoryPick).join("")}</div>
      </section>
    `);
  }

  return `<div class="hub-picks-cat-columns">${sections.join("")}</div>`;
}

function renderPicksGrid() {
  const grid = document.getElementById("picks-grid");
  const titleEl = document.getElementById("picks-title");
  const leadEl = document.getElementById("picks-lead");
  const strategyEl = document.getElementById("picks-strategy");
  if (!grid) return;

  const config = VIEW_CONFIG[activeView] ?? VIEW_CONFIG.safeway;
  const picks = picksForView(activeView);

  if (titleEl) titleEl.textContent = config.title;
  if (leadEl) leadEl.textContent = leadLineForView(activeView);
  if (strategyEl) {
    const strategy = config.strategy ?? "";
    strategyEl.textContent = strategy;
    strategyEl.hidden = !strategy;
  }

  grid.className = "hub-picks-report";
  grid.innerHTML = renderPicksReport(picks);
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
  initCouponCheckModule();
}

/* Coupon personalization check (homepage signup row) */

/** @type {Map<string, { id: string, label: string, voteCount: number }>} */
let couponCheckOptionsById = new Map();
let couponCheckPending = false;

function readCouponCheckVotes() {
  try {
    const raw = localStorage.getItem(COUPON_CHECK_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    return parsed;
  } catch {
    return {};
  }
}

function markCouponCheckVoted(pollId, optionId) {
  const votes = readCouponCheckVotes();
  votes[pollId] = optionId;
  localStorage.setItem(COUPON_CHECK_STORAGE_KEY, JSON.stringify(votes));
}

function showCouponCheckStatus(message, isError = false) {
  const el = document.getElementById("coupon-check-status");
  if (!el) return;
  el.textContent = message;
  el.hidden = false;
  el.classList.remove("hub-coupon-check-status--success", "hub-coupon-check-status--error");
  el.classList.add(isError ? "hub-coupon-check-status--error" : "hub-coupon-check-status--success");
}

function hideCouponCheckStatus() {
  const el = document.getElementById("coupon-check-status");
  if (!el) return;
  el.hidden = true;
  el.textContent = "";
  el.classList.remove("hub-coupon-check-status--success", "hub-coupon-check-status--error");
}

function formatCouponCheckError(error) {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "object" && error && "message" in error
        ? String(error.message)
        : "";

  if (
    message.includes("coupon_check_options") ||
    message.includes("vote_coupon_check") ||
    message.includes("coupon_check_polls")
  ) {
    return "Coupon check isn't set up yet. Apply supabase/migrations/20260715_coupon_check_poll.sql.";
  }
  return message || "Something went wrong. Please try again.";
}

function renderCouponCheckTally() {
  const el = document.getElementById("coupon-check-tally");
  if (!el) return;

  const options = [...couponCheckOptionsById.values()];
  const total = options.reduce((sum, option) => sum + (option.voteCount || 0), 0);
  if (total === 0) {
    el.hidden = true;
    el.textContent = "";
    return;
  }

  const parts = options.map((option) => `${option.label} ${option.voteCount}`);
  el.textContent = `${parts.join(" · ")} (${total} so far)`;
  el.hidden = false;
}

function updateCouponCheckButtons(pollId) {
  const module = document.getElementById("coupon-check-module");
  if (!module) return;

  const votedOptionId = readCouponCheckVotes()[pollId] || null;
  module.querySelectorAll(".hub-coupon-check-btn").forEach((button) => {
    const optionId = button.dataset.optionId;
    const isSelected = Boolean(votedOptionId && optionId === votedOptionId);
    const option = optionId ? couponCheckOptionsById.get(optionId) : null;
    const baseLabel = option?.label || button.dataset.answer || "Vote";
    const count = option?.voteCount ?? 0;
    button.textContent = votedOptionId && count > 0 ? `${baseLabel} (${count})` : baseLabel;
    button.classList.toggle("is-selected", isSelected);
    button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    button.disabled = Boolean(votedOptionId) || couponCheckPending;
  });
}

async function fetchCouponCheckOptions(pollId) {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("coupon_check_options unavailable");
  }

  const { data, error } = await supabase
    .from("coupon_check_options")
    .select("id, label, vote_count, sort_order")
    .eq("poll_id", pollId)
    .order("sort_order", { ascending: true });

  if (error) throw error;

  const byId = new Map();
  for (const row of data ?? []) {
    if (!row?.id) continue;
    byId.set(row.id, {
      id: row.id,
      label: row.label || "Vote",
      voteCount: row.vote_count ?? 0,
    });
  }
  couponCheckOptionsById = byId;
}

async function voteCouponCheckOption(optionId) {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("vote_coupon_check unavailable");
  }

  const { error } = await supabase.rpc("vote_coupon_check", {
    p_option_id: optionId,
  });

  if (error) throw error;
}

async function handleCouponCheckVote(button) {
  const module = document.getElementById("coupon-check-module");
  const pollId = module?.dataset.pollId?.trim();
  const optionId = button.dataset.optionId?.trim();
  if (!module || !pollId || !optionId || couponCheckPending) return;

  const priorVote = readCouponCheckVotes()[pollId];
  if (priorVote) {
    showCouponCheckStatus("Thanks — we already have your answer.");
    updateCouponCheckButtons(pollId);
    renderCouponCheckTally();
    return;
  }

  hideCouponCheckStatus();
  couponCheckPending = true;
  updateCouponCheckButtons(pollId);

  const option = couponCheckOptionsById.get(optionId);
  if (option) {
    option.voteCount += 1;
    renderCouponCheckTally();
  }

  try {
    await voteCouponCheckOption(optionId);
    markCouponCheckVoted(pollId, optionId);
    showCouponCheckStatus("Thanks — that helps us see how personalized this one is.");
  } catch (error) {
    if (option) {
      option.voteCount = Math.max(0, option.voteCount - 1);
      renderCouponCheckTally();
    }
    showCouponCheckStatus(formatCouponCheckError(error), true);
  } finally {
    couponCheckPending = false;
    updateCouponCheckButtons(pollId);
    renderCouponCheckTally();
  }
}

async function initCouponCheckModule() {
  const module = document.getElementById("coupon-check-module");
  if (!module) return;

  const pollId = module.dataset.pollId?.trim();
  if (!pollId) return;

  module.querySelectorAll(".hub-coupon-check-btn").forEach((button) => {
    button.addEventListener("click", () => {
      void handleCouponCheckVote(button);
    });
  });

  // Seed local labels before fetch so buttons still have base text.
  module.querySelectorAll(".hub-coupon-check-btn").forEach((button) => {
    const optionId = button.dataset.optionId;
    if (!optionId) return;
    couponCheckOptionsById.set(optionId, {
      id: optionId,
      label: button.textContent?.trim() || "Vote",
      voteCount: 0,
    });
  });
  updateCouponCheckButtons(pollId);

  try {
    await fetchCouponCheckOptions(pollId);
    updateCouponCheckButtons(pollId);
    renderCouponCheckTally();
    if (readCouponCheckVotes()[pollId]) {
      showCouponCheckStatus("Thanks — we already have your answer.");
    }
  } catch (error) {
    console.error("Failed to load coupon check tallies", error);
    updateCouponCheckButtons(pollId);
  }
}

/* Store vote module (homepage hero) */

/**
 * @typedef {{
 *   id: string,
 *   voteCount: number,
 *   label: string,
 *   normalizedName: string,
 *   createdAt: string | null,
 *   approvedAt: string | null,
 * }} StoreVoteItem
 */

let supabaseClient = null;
/** @type {Map<string, StoreVoteItem>} keyed by store id */
let storeVotesById = new Map();
/** @type {Map<string, StoreVoteItem>} keyed by normalized_name */
let storeVotesByNormalized = new Map();
let storeVoteLoading = true;
let storeVoteListReady = false;
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
  el.classList.remove("price-tracker-vote-status--success", "price-tracker-vote-status--error");
  el.classList.add(isError ? "price-tracker-vote-status--error" : "price-tracker-vote-status--success");
}

function hideStoreStatus() {
  const el = document.getElementById("store-suggest-status");
  if (!el) return;
  el.hidden = true;
  el.textContent = "";
  el.classList.remove("price-tracker-vote-status--success", "price-tracker-vote-status--error");
}

function setStoreVoteListStatus(message) {
  const el = document.getElementById("store-vote-list-status");
  if (!el) return;
  if (message) {
    el.textContent = message;
    el.hidden = false;
  } else {
    el.textContent = "";
    el.hidden = true;
  }
}

function setChipVoteNote(chip, text) {
  let note = chip.querySelector(".price-tracker-vote-card-note");
  if (text) {
    if (!note) {
      note = document.createElement("span");
      note.className = "price-tracker-vote-card-note";
      chip.appendChild(note);
    }
    note.textContent = text;
  } else if (note) {
    note.remove();
  }
}

function rebuildStoreVoteIndexes(items) {
  const byId = new Map();
  const byNormalized = new Map();
  for (const item of items) {
    if (!item?.id) continue;
    byId.set(item.id, item);
    if (item.normalizedName) {
      byNormalized.set(item.normalizedName, item);
    }
  }
  storeVotesById = byId;
  storeVotesByNormalized = byNormalized;
}

function compareStoreVoteItems(a, b) {
  const voteDiff = (b.voteCount ?? 0) - (a.voteCount ?? 0);
  if (voteDiff !== 0) return voteDiff;

  const aApproved = a.approvedAt || "";
  const bApproved = b.approvedAt || "";
  if (aApproved !== bApproved) {
    if (!aApproved) return 1;
    if (!bApproved) return -1;
    return aApproved < bApproved ? -1 : 1;
  }

  const aCreated = a.createdAt || "";
  const bCreated = b.createdAt || "";
  if (aCreated !== bCreated) {
    if (!aCreated) return 1;
    if (!bCreated) return -1;
    return aCreated < bCreated ? -1 : 1;
  }

  return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

function sortedStoreVoteItems() {
  return [...storeVotesById.values()].sort(compareStoreVoteItems);
}

function upsertStoreVoteItem(item) {
  if (!item?.id) return;
  storeVotesById.set(item.id, item);
  if (item.normalizedName) {
    storeVotesByNormalized.set(item.normalizedName, item);
  }
}

function bumpStoreVoteCountById(itemId) {
  const entry = storeVotesById.get(itemId);
  if (!entry) return null;
  entry.voteCount += 1;
  upsertStoreVoteItem(entry);
  return entry;
}

function updateChipStates(votedStores) {
  document.querySelectorAll(".hub-store-chip").forEach((chip) => {
    const storeId = chip.dataset.storeId;
    const item = storeId ? storeVotesById.get(storeId) : null;
    const normalized = item?.normalizedName || normalizeStoreName(chip.dataset.store || "");
    const voted = Boolean(normalized && votedStores.has(normalized));
    const isPending = storePendingVote === storeId || storePendingVote === normalized;
    chip.classList.toggle("price-tracker-vote-card--voted", voted);
    chip.setAttribute("aria-pressed", voted ? "true" : "false");
    chip.disabled =
      voted ||
      Boolean(storePendingVote) ||
      storePendingSuggest ||
      storeVoteLoading;
    setChipVoteNote(chip, voted ? "Voted" : isPending ? "Saving…" : null);
  });
}

function formatStoreVoteLabel(name, voteCount) {
  return voteCount > 0 ? `${name} ▲ ${voteCount}` : name;
}

function createStoreChip(item) {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "hub-store-chip price-tracker-vote-card";
  chip.setAttribute("role", "listitem");
  chip.dataset.storeId = item.id;
  chip.dataset.store = item.label;
  chip.setAttribute("aria-pressed", "false");

  const label = document.createElement("span");
  label.className = "price-tracker-vote-card-label";
  label.textContent = formatStoreVoteLabel(item.label, item.voteCount);
  chip.appendChild(label);

  chip.addEventListener("click", () => {
    void handleStoreChipVote(chip);
  });

  return chip;
}

function renderStoreChips() {
  const strip = document.getElementById("store-vote-strip");
  if (!strip) return;

  strip.setAttribute("aria-busy", storeVoteLoading ? "true" : "false");
  strip.replaceChildren();

  if (storeVoteListReady) {
    for (const item of sortedStoreVoteItems()) {
      strip.appendChild(createStoreChip(item));
    }
  }

  updateChipStates(readVotedStores());
}

async function fetchStoreVoteItems() {
  const supabase = getSupabase();
  if (!supabase) {
    throw new Error("store_vote_items unavailable");
  }

  const { data, error } = await supabase
    .from("store_vote_items")
    .select("id, public_name, raw_text, normalized_name, vote_count, created_at, approved_at")
    .eq("status", "approved");

  if (error) {
    throw error;
  }

  const items = [];
  for (const row of data ?? []) {
    if (!row?.id) continue;
    const label = (row.public_name?.trim() || row.raw_text || "").trim();
    if (!label) continue;
    items.push({
      id: row.id,
      voteCount: row.vote_count ?? 0,
      label,
      normalizedName: row.normalized_name || normalizeStoreName(label),
      createdAt: row.created_at ?? null,
      approvedAt: row.approved_at ?? null,
    });
  }

  rebuildStoreVoteIndexes(items);
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
  const storeId = chip.dataset.storeId?.trim();
  const store = chip.dataset.store?.trim();
  if (!storeId || !store || storePendingVote || storePendingSuggest || storeVoteLoading) {
    return;
  }

  const item = storeVotesById.get(storeId);
  if (!item) {
    showStoreStatus("This store isn't available for voting right now.", true);
    return;
  }

  const normalized = item.normalizedName || normalizeStoreName(store);
  const votedStores = readVotedStores();
  if (votedStores.has(normalized)) {
    showStoreStatus("You already voted for this store.");
    return;
  }

  hideStoreStatus();
  storePendingVote = storeId;
  updateChipStates(votedStores);
  bumpStoreVoteCountById(storeId);
  renderStoreChips();

  try {
    await voteOnStoreItem(storeId);
    markStoreVoted(normalized);
    showStoreStatus(`Vote counted for ${item.label}. Thanks!`);
  } catch (error) {
    const entry = storeVotesById.get(storeId);
    if (entry) {
      entry.voteCount = Math.max(0, entry.voteCount - 1);
      upsertStoreVoteItem(entry);
      renderStoreChips();
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
      if (storeVoteListReady) {
        const existing =
          (result.item_id && storeVotesById.get(result.item_id)) ||
          storeVotesByNormalized.get(normalized);
        if (existing) {
          bumpStoreVoteCountById(existing.id);
        } else if (result.item_id) {
          upsertStoreVoteItem({
            id: result.item_id,
            voteCount: 1,
            label: store,
            normalizedName: normalized,
            createdAt: null,
            approvedAt: null,
          });
        }
        renderStoreChips();
      }
      form.reset();
      showStoreStatus("Vote counted. Thanks!");
      return;
    }

    form.reset();
    showStoreStatus("Thanks. We'll review this before adding it to the voting list.");
  } catch (error) {
    showStoreStatus(formatStoreVoteError(error), true);
  } finally {
    storePendingSuggest = false;
    updateChipStates(readVotedStores());
  }
}

async function initStoreSuggestModule() {
  const module = document.getElementById("store-suggest-module");
  if (!module) return;

  const form = document.getElementById("store-custom-form");
  form?.addEventListener("submit", handleStoreFormSubmit);

  setStoreVoteListStatus("");
  renderStoreChips();

  try {
    await fetchStoreVoteItems();
    storeVoteListReady = true;
    setStoreVoteListStatus("");
    renderStoreChips();
  } catch (error) {
    storeVoteListReady = false;
    rebuildStoreVoteIndexes([]);
    console.error("Failed to load approved store vote items", error);
    setStoreVoteListStatus("Store votes couldn't load right now. You can still suggest a store below.");
    renderStoreChips();
  } finally {
    storeVoteLoading = false;
    renderStoreChips();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  void initHomepage();
});
