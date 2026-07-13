/**
 * Shared helpers for homepage highlights width exploration.
 * Consumes PopularPick objects from homepage.js / homepage-preview.generated.json.
 */

export const LAYOUT_VERSIONS = [
  {
    id: 1,
    label: "Version 1",
    name: "Balanced editorial breakout",
    widthHint: "≈1000px",
  },
  {
    id: 2,
    label: "Version 2",
    name: "Two-column weekly newspaper",
    widthHint: "≈900px",
  },
  {
    id: 3,
    label: "Version 3",
    name: "Lead column + compact index",
    widthHint: "≈1020px",
  },
  {
    id: 4,
    label: "Version 4",
    name: "Full-width category bands",
    widthHint: "≈1000px",
  },
  {
    id: 5,
    label: "Version 5",
    name: "Compact deal ledger",
    widthHint: "≈960px",
  },
  {
    id: 6,
    label: "Version 6",
    name: "Responsive magazine mosaic",
    widthHint: "≈1050px",
  },
];

/** Max content width per version (inner shell, not full viewport). */
export const VERSION_MAX_WIDTH = {
  1: "1280px",
  2: "1120px",
  3: "1280px",
  4: "1240px",
  5: "1180px",
  6: "1360px",
};

export const CATEGORY_ORDER = [
  "Friday",
  "Produce",
  "Meat",
  "Snacks",
  "Variety",
  "Other Deals",
];

const BADGE_TO_CATEGORY = {
  friday: "Friday",
  produce: "Produce",
  meat: "Meat",
  snacks: "Snacks",
  variety: "Variety",
  deal: "Other Deals",
};

export function escapeHtml(text) {
  if (text == null || text === "") return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function categoryForPick(pick) {
  const raw = String(pick.customBadge || "")
    .trim()
    .toLowerCase();
  return BADGE_TO_CATEGORY[raw] || "Other Deals";
}

export function categorySlug(category) {
  return String(category).toLowerCase().replace(/\s+/g, "-");
}

export function groupPicksByCategory(picks) {
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

export function priceHistoryLink(pick, className = "wx-link") {
  const href = escapeHtml(pick.trackerUrl || "grocery-price-tracker/");
  return `<a href="${href}" class="${className}">See price history →</a>`;
}

export function unitPriceHtml(pick) {
  if (!pick.unitPrice) return "";
  return `<span class="wx-unit">${escapeHtml(pick.unitPrice)}</span>`;
}

export function emptyPicksHtml(trackerUrl = "grocery-price-tracker/") {
  return `<p class="hub-empty">Weekly picks loading soon. Check the <a href="${escapeHtml(trackerUrl)}">price tracker</a>.</p>`;
}

export function placeholderClass(pick, extra = "") {
  return [extra, pick.isPlaceholder ? "is-placeholder" : ""]
    .filter(Boolean)
    .join(" ");
}
