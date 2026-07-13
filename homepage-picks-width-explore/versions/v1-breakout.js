import {
  categorySlug,
  emptyPicksHtml,
  escapeHtml,
  groupPicksByCategory,
  placeholderClass,
  priceHistoryLink,
  unitPriceHtml,
} from "../shared.js";

export function renderVersion1(picks, helpers) {
  if (!picks.length) return emptyPicksHtml(helpers.TRACKER_URL);

  const sections = [];
  for (const [category, items] of groupPicksByCategory(picks)) {
    const slug = categorySlug(category);
    sections.push(`
      <section class="wx-v1-section wx-cat--${slug}" aria-labelledby="wx-v1-${slug}">
        <header class="wx-v1-head">
          <h3 id="wx-v1-${slug}" class="wx-cat-title">${escapeHtml(category)}</h3>
          <span class="wx-cat-count">${items.length}</span>
        </header>
        <div class="wx-v1-items">
          ${items
            .map(
              (pick) => `
            <article class="${placeholderClass(pick, "wx-v1-item")}">
              <div class="wx-v1-item-top">
                <h4 class="wx-deal-name">${escapeHtml(pick.name)}</h4>
                <p class="wx-deal-price">
                  <span class="wx-price">${escapeHtml(pick.price)}</span>
                  ${unitPriceHtml(pick)}
                </p>
              </div>
              <p class="wx-deal-note">${escapeHtml(pick.explanation)}</p>
              ${priceHistoryLink(pick, "wx-link wx-link--quiet")}
            </article>`,
            )
            .join("")}
        </div>
      </section>`);
  }

  return `<div class="wx-layout wx-layout--v1" data-wx-version="1">
    <div class="wx-v1-columns">${sections.join("")}</div>
  </div>`;
}
