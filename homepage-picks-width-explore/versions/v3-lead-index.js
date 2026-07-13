import {
  categoryForPick,
  emptyPicksHtml,
  escapeHtml,
  placeholderClass,
  priceHistoryLink,
  unitPriceHtml,
} from "../shared.js";

export function renderVersion3(picks, helpers) {
  if (!picks.length) return emptyPicksHtml(helpers.TRACKER_URL);

  const leadCount = picks.length >= 8 ? 4 : Math.min(3, picks.length);
  const leads = picks.slice(0, leadCount);
  const rest = picks.slice(leadCount);

  const leadsHtml = leads
    .map(
      (pick, i) => `
    <article class="${placeholderClass(pick, "wx-v3-lead")}">
      <div class="wx-v3-lead-kicker">
        <span class="wx-v3-kicker-label">${i === 0 ? "Lead" : "Featured"}</span>
        <span class="wx-v3-cat-pill">${escapeHtml(categoryForPick(pick))}</span>
      </div>
      <h3 class="wx-v3-lead-title">${escapeHtml(pick.name)}</h3>
      <p class="wx-deal-price">
        <span class="wx-price wx-price--lg">${escapeHtml(pick.price)}</span>
        ${unitPriceHtml(pick)}
      </p>
      <p class="wx-deal-note">${escapeHtml(pick.explanation)}</p>
      ${priceHistoryLink(pick)}
    </article>`,
    )
    .join("");

  const indexHtml = rest
    .map(
      (pick) => `
    <article class="${placeholderClass(pick, "wx-v3-index-row")}">
      <div class="wx-v3-index-main">
        <h4 class="wx-deal-name">${escapeHtml(pick.name)}</h4>
        <span class="wx-price">${escapeHtml(pick.price)}</span>
      </div>
      <p class="wx-deal-note">${escapeHtml(pick.explanation)}</p>
      <div class="wx-v3-index-meta">
        <span class="wx-v3-cat-pill">${escapeHtml(categoryForPick(pick))}</span>
        ${priceHistoryLink(pick, "wx-link wx-link--quiet")}
      </div>
    </article>`,
    )
    .join("");

  return `<div class="wx-layout wx-layout--v3" data-wx-version="3">
    <div class="wx-v3-split">
      <div class="wx-v3-leads">
        <h3 class="wx-v3-side-label">This week's leads</h3>
        ${leadsHtml}
      </div>
      <div class="wx-v3-index">
        <h3 class="wx-v3-side-label">Also watching</h3>
        <div class="wx-v3-index-list">${indexHtml}</div>
      </div>
    </div>
  </div>`;
}
