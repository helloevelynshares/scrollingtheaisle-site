import {
  categorySlug,
  emptyPicksHtml,
  escapeHtml,
  groupPicksByCategory,
  placeholderClass,
  priceHistoryLink,
  unitPriceHtml,
} from "../shared.js";

export function renderVersion4(picks, helpers) {
  if (!picks.length) return emptyPicksHtml(helpers.TRACKER_URL);

  const bands = [];
  for (const [category, items] of groupPicksByCategory(picks)) {
    const slug = categorySlug(category);
    const sparse = items.length === 1 ? " wx-v4-band--sparse" : "";
    bands.push(`
      <section class="wx-v4-band wx-cat--${slug}${sparse}" aria-labelledby="wx-v4-${slug}">
        <header class="wx-v4-rail">
          <h3 id="wx-v4-${slug}" class="wx-cat-title">${escapeHtml(category)}</h3>
          <span class="wx-cat-count">${items.length}</span>
        </header>
        <div class="wx-v4-deals">
          ${items
            .map(
              (pick) => `
            <article class="${placeholderClass(pick, "wx-v4-deal")}">
              <h4 class="wx-deal-name">${escapeHtml(pick.name)}</h4>
              <p class="wx-deal-price">
                <span class="wx-price">${escapeHtml(pick.price)}</span>
                ${unitPriceHtml(pick)}
              </p>
              <p class="wx-deal-note">${escapeHtml(pick.explanation)}</p>
              ${priceHistoryLink(pick, "wx-link wx-link--quiet")}
            </article>`,
            )
            .join("")}
        </div>
      </section>`);
  }

  return `<div class="wx-layout wx-layout--v4" data-wx-version="4">
    <div class="wx-v4-bands">${bands.join("")}</div>
  </div>`;
}
