import {
  categoryForPick,
  emptyPicksHtml,
  escapeHtml,
  placeholderClass,
  priceHistoryLink,
} from "../shared.js";

export function renderVersion5(picks, helpers) {
  if (!picks.length) return emptyPicksHtml(helpers.TRACKER_URL);

  const rows = picks
    .map((pick, i) => {
      const detailId = `wx-ledger-${i}`;
      return `
    <tr class="${placeholderClass(pick, "wx-v5-row")}">
      <td class="wx-v5-item">
        <button type="button" class="wx-v5-expand" aria-expanded="false" aria-controls="${detailId}" data-wx-ledger-toggle>
          <span class="wx-deal-name">${escapeHtml(pick.name)}</span>
          <span class="wx-v5-expand-hint">Details</span>
        </button>
        <div class="wx-v5-mobile-price">
          <span class="wx-price">${escapeHtml(pick.price)}</span>
        </div>
      </td>
      <td class="wx-v5-offer">
        <span class="wx-price">${escapeHtml(pick.price)}</span>
        ${pick.unitPrice ? `<span class="wx-unit">${escapeHtml(pick.unitPrice)}</span>` : ""}
      </td>
      <td class="wx-v5-why">
        <p class="wx-deal-note">${escapeHtml(pick.explanation)}</p>
      </td>
      <td class="wx-v5-tag">
        <span class="wx-v3-cat-pill">${escapeHtml(categoryForPick(pick))}</span>
      </td>
      <td class="wx-v5-link">${priceHistoryLink(pick, "wx-link wx-link--quiet")}</td>
    </tr>
    <tr class="wx-v5-detail-row" id="${detailId}" hidden>
      <td colspan="5">
        <div class="wx-v5-detail">
          <p class="wx-deal-note">${escapeHtml(pick.explanation)}</p>
          <div class="wx-v5-detail-meta">
            <span class="wx-v3-cat-pill">${escapeHtml(categoryForPick(pick))}</span>
            ${
              pick.unitPrice
                ? `<span class="wx-unit">${escapeHtml(pick.unitPrice)}</span>`
                : ""
            }
            ${priceHistoryLink(pick)}
          </div>
        </div>
      </td>
    </tr>`;
    })
    .join("");

  return `<div class="wx-layout wx-layout--v5" data-wx-version="5">
    <div class="wx-v5-wrap">
      <table class="wx-v5-table">
        <caption class="visually-hidden">Handpicked deals this week</caption>
        <thead>
          <tr>
            <th scope="col">Item</th>
            <th scope="col">Price</th>
            <th scope="col">Why it matters</th>
            <th scope="col">Category</th>
            <th scope="col"><span class="visually-hidden">Price history</span></th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  </div>`;
}

export function bindVersion5(root) {
  root.querySelectorAll("[data-wx-ledger-toggle]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("aria-controls");
      const detail = id ? document.getElementById(id) : null;
      if (!detail) return;
      const open = detail.hasAttribute("hidden");
      if (open) detail.removeAttribute("hidden");
      else detail.setAttribute("hidden", "");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });
}
