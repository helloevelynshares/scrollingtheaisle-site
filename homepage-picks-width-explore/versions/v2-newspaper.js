import {
  categorySlug,
  emptyPicksHtml,
  escapeHtml,
  groupPicksByCategory,
  placeholderClass,
  priceHistoryLink,
  unitPriceHtml,
} from "../shared.js";

export function renderVersion2(picks, helpers) {
  if (!picks.length) return emptyPicksHtml(helpers.TRACKER_URL);

  const groups = [...groupPicksByCategory(picks).entries()];
  const mid = Math.ceil(groups.length / 2);
  const left = groups.slice(0, mid);
  const right = groups.slice(mid);

  const colHtml = (entries, side) =>
    entries
      .map(([category, items]) => {
        const slug = categorySlug(category);
        return `
        <section class="wx-v2-section wx-cat--${slug}" aria-labelledby="wx-v2-${side}-${slug}">
          <h3 id="wx-v2-${side}-${slug}" class="wx-cat-title">${escapeHtml(category)}</h3>
          <div class="wx-v2-items">
            ${items
              .map(
                (pick) => `
              <article class="${placeholderClass(pick, "wx-v2-item")}">
                <div class="wx-v2-row">
                  <h4 class="wx-deal-name">${escapeHtml(pick.name)}</h4>
                  <span class="wx-price">${escapeHtml(pick.price)}</span>
                </div>
                ${unitPriceHtml(pick)}
                <p class="wx-deal-note">${escapeHtml(pick.explanation)}</p>
                ${priceHistoryLink(pick, "wx-link wx-link--quiet")}
              </article>`,
              )
              .join("")}
          </div>
        </section>`;
      })
      .join("");

  return `<div class="wx-layout wx-layout--v2" data-wx-version="2">
    <div class="wx-v2-paper">
      <div class="wx-v2-col">${colHtml(left, "l")}</div>
      <div class="wx-v2-rule" aria-hidden="true"></div>
      <div class="wx-v2-col">${colHtml(right, "r")}</div>
    </div>
  </div>`;
}
