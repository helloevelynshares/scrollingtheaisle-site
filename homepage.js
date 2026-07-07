/**
 * Homepage hub — curated popular picks (Safeway / Vons toggle).
 * Price data: data/homepage-preview.generated.json (npm run generate:homepage-preview)
 */

const PREVIEW_JSON = "data/homepage-preview.generated.json";
const TRACKER_URL = "staging-price-tracker/";
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

function metaForView(view) {
  if (!previewData) return "";
  const config = VIEW_CONFIG[view];
  if (!config) return "";
  const week = previewData.popularWeekLabel;
  return week
    ? `Curated by Scrolling the Aisle · week of ${week}`
    : "Curated by Scrolling the Aisle";
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
  const metaEl = document.getElementById("picks-meta");
  if (!grid) return;

  const config = VIEW_CONFIG[activeView] ?? VIEW_CONFIG.safeway;
  const picks = picksForView(activeView);

  if (titleEl) titleEl.textContent = config.title;
  if (leadEl) leadEl.textContent = config.lead;
  if (metaEl) metaEl.textContent = metaForView(activeView);

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
}

document.addEventListener("DOMContentLoaded", () => {
  void initHomepage();
});
