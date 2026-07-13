import {
  categorySlug,
  emptyPicksHtml,
  escapeHtml,
  groupPicksByCategory,
  placeholderClass,
  priceHistoryLink,
  unitPriceHtml,
} from "../shared.js";

export function renderVersion6(picks, helpers) {
  if (!picks.length) return emptyPicksHtml(helpers.TRACKER_URL);

  const blocks = [];
  for (const [category, items] of groupPicksByCategory(picks)) {
    const slug = categorySlug(category);
    const [feature, ...briefs] = items;

    blocks.push(`
      <div class="wx-v6-anchor wx-cat--${slug}">
        <h3 class="wx-cat-title">${escapeHtml(category)}</h3>
      </div>`);

    if (feature) {
      blocks.push(`
        <article class="${placeholderClass(feature, "wx-v6-feature")}">
          <h4 class="wx-v6-feature-title">${escapeHtml(feature.name)}</h4>
          <p class="wx-deal-price">
            <span class="wx-price wx-price--lg">${escapeHtml(feature.price)}</span>
            ${unitPriceHtml(feature)}
          </p>
          <p class="wx-deal-note">${escapeHtml(feature.explanation)}</p>
          ${priceHistoryLink(feature)}
        </article>`);
    }

    for (const pick of briefs) {
      blocks.push(`
        <article class="${placeholderClass(pick, "wx-v6-brief")}">
          <h4 class="wx-deal-name">${escapeHtml(pick.name)}</h4>
          <span class="wx-price">${escapeHtml(pick.price)}</span>
          <p class="wx-deal-note">${escapeHtml(pick.explanation)}</p>
          ${priceHistoryLink(pick, "wx-link wx-link--quiet")}
        </article>`);
    }
  }

  return `<div class="wx-layout wx-layout--v6" data-wx-version="6">
    <div class="wx-v6-mosaic">${blocks.join("")}</div>
  </div>`;
}
