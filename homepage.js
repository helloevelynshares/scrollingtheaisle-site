/**
 * Homepage hub — stock-up picks, tracker preview, voting, live finds.
 * Price data: data/homepage-preview.generated.json (npm run generate:homepage-preview)
 */

const SUPABASE_URL = "https://wurmdtqysegytsjcudve.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_8Wt-it-oIHHIkQOi0D9y_g_qMoH51ZX";
const TRACK_VOTE_STORAGE_KEY = "sta_track_votes";
const VISITOR_ID_KEY = "sta_visitor_id";
const PREVIEW_JSON = "data/homepage-preview.generated.json";
const TRACKER_URL = "staging-price-tracker/";
const TRACKER_VOTE_URL = "staging-price-tracker/#track-vote";
const FINDS_URL = "finds.html";
const SUBMIT_URL = "submit.html";

const HOMEPAGE_VOTE_LABELS = [
  "Berries",
  "Grapes",
  "Chicken breast",
  "Oreos",
  "Ritz",
  "Kettle chips",
  "Yogurt",
  "Eggs",
  "Ice cream",
];

const BADGE_CLASS = {
  "Stock up": "hub-badge--stock-up",
  "Good small-pack buy": "hub-badge--good-buy",
  "Costco still wins": "hub-badge--costco",
  Wait: "hub-badge--wait",
  "Lowest seen recently": "hub-badge--low",
  "Beats Costco": "hub-badge--beats",
  "About normal": "hub-badge--normal",
};

const SIGNAL_CLASS = {
  "Stock up": "hub-signal--stock-up",
  "Beats Costco": "hub-signal--beats",
  "About normal": "hub-signal--normal",
  Wait: "hub-signal--wait",
  "Costco wins": "hub-signal--costco",
};

let supabaseClient = null;
let previewData = null;
let trackerRows = [];
let voteItems = [];

function getSupabase() {
  if (!supabaseClient && window.supabase) {
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return supabaseClient;
}

function escapeHtml(text) {
  if (text == null || text === "") return "";
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

function normalizeItemName(name) {
  return String(name)
    .toLowerCase()
    .trim()
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function readVotedItems() {
  try {
    const raw = localStorage.getItem(TRACK_VOTE_STORAGE_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return new Set();
    return new Set(parsed.filter((v) => typeof v === "string"));
  } catch {
    return new Set();
  }
}

function markItemVoted(normalizedItemName) {
  const voted = readVotedItems();
  voted.add(normalizedItemName);
  localStorage.setItem(TRACK_VOTE_STORAGE_KEY, JSON.stringify([...voted]));
}

function formatVoteLabel(itemName, voteCount) {
  return voteCount > 0 ? `${itemName} ▲ ${voteCount}` : itemName;
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

function signalHtml(signal) {
  const cls = SIGNAL_CLASS[signal] || "hub-signal--normal";
  return `<span class="hub-signal ${cls}">${escapeHtml(signal)}</span>`;
}

function renderStockUpSection() {
  const grid = document.getElementById("stock-up-grid");
  const weekNote = document.getElementById("stock-up-week");
  if (!grid) return;

  const picks = previewData?.stockUpPicks ?? [];
  if (weekNote && previewData?.weekLabel) {
    weekNote.textContent = `${previewData.feedLabel ?? "Safeway"} · week of ${previewData.weekLabel}`;
  }

  if (picks.length === 0) {
    grid.innerHTML = `<p class="hub-empty">Weekly picks loading soon — check the <a href="${TRACKER_URL}">price tracker</a>.</p>`;
    return;
  }

  grid.innerHTML = picks
    .map(
      (pick) => `
    <article class="hub-deal-card${pick.isPlaceholder ? " hub-deal-card--placeholder" : ""}">
      <div class="hub-deal-card-top">
        <h3 class="hub-deal-card-title">${escapeHtml(pick.name)}</h3>
        ${badgeHtml(pick.badge)}
      </div>
      <p class="hub-deal-card-price">
        <span class="hub-deal-card-amount">${escapeHtml(pick.price)}</span>
        <span class="hub-deal-card-store">${escapeHtml(pick.store)}</span>
      </p>
      <p class="hub-deal-card-unit">${escapeHtml(pick.unitPrice)}</p>
      <p class="hub-deal-card-note">${escapeHtml(pick.explanation)}</p>
      <a href="${escapeHtml(pick.trackerUrl || TRACKER_URL)}" class="hub-deal-card-link">See price history →</a>
    </article>
  `,
    )
    .join("");
}

function renderTrackerPreview(filter = "") {
  const tbody = document.getElementById("tracker-preview-body");
  const cards = document.getElementById("tracker-preview-cards");
  if (!tbody && !cards) return;

  const query = filter.trim().toLowerCase();
  const rows = trackerRows.filter((row) => {
    if (!query) return true;
    return row.name.toLowerCase().includes(query);
  });

  const emptyMsg = `<p class="hub-empty">No matches — try another item or open the <a href="${TRACKER_URL}">full tracker</a>.</p>`;

  if (rows.length === 0) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="6">${emptyMsg}</td></tr>`;
    if (cards) cards.innerHTML = emptyMsg;
    return;
  }

  if (tbody) {
    tbody.innerHTML = rows
      .map(
        (row) => `
      <tr>
        <td class="hub-tracker-item">${escapeHtml(row.name)}</td>
        <td>${escapeHtml(row.currentPrice)}</td>
        <td>${escapeHtml(row.store)}</td>
        <td>${escapeHtml(row.unitPrice)}</td>
        <td class="hub-tracker-comparison">${escapeHtml(row.comparisonSignal)}</td>
        <td>${signalHtml(row.buySignal)}</td>
      </tr>
    `,
      )
      .join("");
  }

  if (cards) {
    cards.innerHTML = rows
      .map(
        (row) => `
      <article class="hub-tracker-card">
        <div class="hub-tracker-card-head">
          <h3>${escapeHtml(row.name)}</h3>
          ${signalHtml(row.buySignal)}
        </div>
        <p class="hub-tracker-card-price">${escapeHtml(row.currentPrice)} · ${escapeHtml(row.store)}</p>
        <p class="hub-tracker-card-unit">${escapeHtml(row.unitPrice)}</p>
        <p class="hub-tracker-card-comparison">${escapeHtml(row.comparisonSignal)}</p>
      </article>
    `,
      )
      .join("");
  }
}

function initTrackerSearch() {
  const input = document.getElementById("tracker-search");
  if (!input) return;
  input.addEventListener("input", () => {
    renderTrackerPreview(input.value);
  });
}

function renderTikTokSection() {
  const grid = document.getElementById("tiktok-grid");
  if (!grid) return;

  const highlights = previewData?.tiktokHighlights ?? [
    {
      title: "Safeway weekly walk",
      finding: "Strawberries dipped under usual Bay Area pricing",
      why: "We matched the ad price against past weeks and Costco per-pound math.",
      url: "https://www.tiktok.com/@evelynshares/video/7535317556773653773",
      ctaLabel: "Watch the breakdown",
    },
    {
      title: "Costco vs grocery chips",
      finding: "When the big bag wins — and when variety packs do",
      why: "Unit-price comparisons for families like Ritz and snack multipacks.",
      url: "https://www.tiktok.com/@evelynshares/video/7539982330568510734",
      ctaLabel: "Watch the aisle walk",
    },
  ];

  grid.innerHTML = highlights
    .map(
      (item) => `
    <article class="hub-tiktok-card">
      <h3>${escapeHtml(item.title)}</h3>
      <p class="hub-tiktok-finding">${escapeHtml(item.finding)}</p>
      <p class="hub-tiktok-why">${escapeHtml(item.why)}</p>
      <a href="${escapeHtml(item.url)}" class="hub-tiktok-link" target="_blank" rel="noopener noreferrer">${escapeHtml(item.ctaLabel)} →</a>
    </article>
  `,
    )
    .join("");
}

function defaultVoteItems() {
  return HOMEPAGE_VOTE_LABELS.map((itemName) => ({
    id: null,
    itemName,
    normalizedItemName: normalizeItemName(itemName),
    voteCount: 0,
  }));
}

async function fetchVoteItems() {
  const supabase = getSupabase();
  if (!supabase) return defaultVoteItems();

  try {
    const { data, error } = await supabase
      .from("tracker_vote_items")
      .select("id, public_name, raw_text, normalized_name, vote_count")
      .eq("status", "approved")
      .order("vote_count", { ascending: false })
      .order("public_name", { ascending: true });

    if (error) throw error;
    if (!data || data.length === 0) return defaultVoteItems();

    return data.map((row) => ({
      id: row.id,
      itemName: row.public_name?.trim() || row.raw_text,
      normalizedItemName: row.normalized_name,
      voteCount: row.vote_count ?? 0,
    }));
  } catch (err) {
    console.warn("Vote items unavailable, using seed list", err);
    return defaultVoteItems();
  }
}

function renderVoteGrid(items, votedItems, pendingVote) {
  const grid = document.getElementById("vote-grid");
  if (!grid) return;

  const merged = [...items];
  for (const label of HOMEPAGE_VOTE_LABELS) {
    const norm = normalizeItemName(label);
    if (!merged.some((item) => item.normalizedItemName === norm)) {
      merged.push({
        id: null,
        itemName: label,
        normalizedItemName: norm,
        voteCount: 0,
      });
    }
  }

  merged.sort((a, b) => {
    if (b.voteCount !== a.voteCount) return b.voteCount - a.voteCount;
    return a.itemName.localeCompare(b.itemName);
  });

  grid.innerHTML = merged
    .map((item) => {
      const voted = votedItems.has(item.normalizedItemName);
      const pending = pendingVote === item.normalizedItemName;
      const disabled = voted || pending || !item.id;
      return `
      <button
        type="button"
        class="hub-vote-pill${voted ? " hub-vote-pill--voted" : ""}"
        data-normalized="${escapeHtml(item.normalizedItemName)}"
        data-id="${escapeHtml(item.id ?? "")}"
        ${disabled ? "disabled" : ""}
        aria-pressed="${voted}"
      >
        <span class="hub-vote-pill-label">${escapeHtml(formatVoteLabel(item.itemName, item.voteCount))}</span>
        ${voted ? '<span class="hub-vote-pill-note">Voted</span>' : pending ? '<span class="hub-vote-pill-note">Saving…</span>' : '<span class="hub-vote-pill-note">Track this</span>'}
      </button>
    `;
    })
    .join("");

  grid.querySelectorAll(".hub-vote-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      void handleVoteClick(btn);
    });
  });
}

async function handleVoteClick(button) {
  const id = button.dataset.id;
  const normalized = button.dataset.normalized;
  const statusEl = document.getElementById("vote-status");

  if (!id) {
    window.location.href = TRACKER_VOTE_URL;
    return;
  }

  if (readVotedItems().has(normalized)) return;

  const supabase = getSupabase();
  if (!supabase) {
    window.location.href = TRACKER_VOTE_URL;
    return;
  }

  renderVoteGrid(voteItems, readVotedItems(), normalized);
  if (statusEl) {
    statusEl.textContent = "";
    statusEl.className = "hub-vote-status";
  }

  try {
    const { error } = await supabase.rpc("vote_on_item", { p_item_id: id });
    if (error) throw error;
    markItemVoted(normalized);
    voteItems = voteItems.map((item) =>
      item.normalizedItemName === normalized
        ? { ...item, voteCount: item.voteCount + 1 }
        : item,
    );
    renderVoteGrid(voteItems, readVotedItems(), null);
    if (statusEl) {
      statusEl.textContent = "Vote counted — thanks!";
      statusEl.className = "hub-vote-status hub-vote-status--success";
    }
  } catch (err) {
    console.error(err);
    renderVoteGrid(voteItems, readVotedItems(), null);
    if (statusEl) {
      statusEl.textContent = "Could not save your vote — try on the price tracker.";
      statusEl.className = "hub-vote-status hub-vote-status--error";
    }
  }
}

async function initVoteSection() {
  voteItems = await fetchVoteItems();
  renderVoteGrid(voteItems, readVotedItems(), null);

  const form = document.getElementById("vote-suggest-form");
  const input = document.getElementById("vote-suggest-input");
  const statusEl = document.getElementById("vote-status");

  if (!form || !input) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const trimmed = input.value.trim();
    if (!trimmed) return;

    const supabase = getSupabase();
    if (!supabase) {
      window.location.href = TRACKER_VOTE_URL;
      return;
    }

    try {
      const { data, error } = await supabase.rpc("submit_suggestion", {
        p_raw_text: trimmed,
      });
      if (error) throw error;

      input.value = "";
      if (statusEl) {
        const action = data?.action;
        statusEl.textContent =
          action === "voted"
            ? "Vote counted — thanks!"
            : "Thanks — we'll review this before adding it to the voting list.";
        statusEl.className = "hub-vote-status hub-vote-status--success";
      }
    } catch (err) {
      console.error(err);
      if (statusEl) {
        statusEl.textContent = "Could not submit — try on the price tracker.";
        statusEl.className = "hub-vote-status hub-vote-status--error";
      }
    }
  });
}

function formatFindPrice(find) {
  if (find.price_display) return find.price_display;
  if (find.price != null && find.price !== "") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(Number(find.price));
  }
  return "";
}

function timeAgo(dateString) {
  const seconds = Math.floor((Date.now() - new Date(dateString).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "1 day ago" : `${days} days ago`;
}

async function initFindsPreview() {
  const container = document.getElementById("finds-preview");
  if (!container) return;

  const supabase = getSupabase();
  if (!supabase) {
    container.innerHTML = `<p class="hub-empty">Browse <a href="${FINDS_URL}">live finds</a> spotted in-store.</p>`;
    return;
  }

  container.innerHTML = `<p class="hub-loading">Loading fresh finds…</p>`;

  try {
    const { data, error } = await supabase
      .from("finds")
      .select("id, item_name, price, price_display, store_name, location_label, notes, created_at")
      .eq("status", "approved")
      .gt("expires_at", new Date().toISOString())
      .order("created_at", { ascending: false })
      .limit(3);

    if (error) throw error;

    if (!data || data.length === 0) {
      container.innerHTML = `
        <p class="hub-empty">No fresh finds yet — be the first to post one.</p>
        <div class="hub-section-actions">
          <a href="${FINDS_URL}" class="btn btn-secondary">See all live finds</a>
          <a href="${SUBMIT_URL}" class="btn btn-primary">Post a find</a>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="hub-finds-grid">
        ${data
          .map(
            (find) => `
          <article class="hub-find-card">
            <h3>${escapeHtml(find.item_name)}</h3>
            <p class="hub-find-price">${escapeHtml(formatFindPrice(find))}</p>
            <p class="hub-find-meta">${escapeHtml([find.store_name, find.location_label, timeAgo(find.created_at)].filter(Boolean).join(" · "))}</p>
            ${find.notes ? `<p class="hub-find-notes">${escapeHtml(find.notes)}</p>` : ""}
          </article>
        `,
          )
          .join("")}
      </div>
      <div class="hub-section-actions">
        <a href="${FINDS_URL}" class="btn btn-secondary">See all live finds</a>
        <a href="${SUBMIT_URL}" class="btn btn-primary">Post a find</a>
      </div>
    `;
  } catch (err) {
    console.error(err);
    container.innerHTML = `
      <p class="hub-empty">Could not load finds right now — visit the <a href="${FINDS_URL}">finds page</a>.</p>
      <div class="hub-section-actions">
        <a href="${FINDS_URL}" class="btn btn-secondary">See all live finds</a>
      </div>
    `;
  }
}

async function initHomepage() {
  await loadPreviewData();
  trackerRows = previewData?.trackerPreview ?? [];
  renderStockUpSection();
  renderTrackerPreview();
  renderTikTokSection();
  initTrackerSearch();
  await Promise.all([initVoteSection(), initFindsPreview()]);
}

document.addEventListener("DOMContentLoaded", () => {
  void initHomepage();
});
