/**
 * Highlights width-layout exploration orchestrator.
 * Isolated. Delete homepage-picks-width-explore/ and unlink from index.html /
 * homepage.js to remove after choosing a direction.
 */

import { LAYOUT_VERSIONS, VERSION_MAX_WIDTH } from "./shared.js";
import { renderVersion1 } from "./versions/v1-breakout.js";
import { renderVersion2 } from "./versions/v2-newspaper.js";
import { renderVersion3 } from "./versions/v3-lead-index.js";
import { renderVersion4 } from "./versions/v4-bands.js";
import { bindVersion5, renderVersion5 } from "./versions/v5-ledger.js";
import { renderVersion6 } from "./versions/v6-mosaic.js";

const STORAGE_KEY = "sta_picks_width_explore_v";
const VERSION_COUNT = LAYOUT_VERSIONS.length;

const RENDERERS = {
  1: renderVersion1,
  2: renderVersion2,
  3: renderVersion3,
  4: renderVersion4,
  5: renderVersion5,
  6: renderVersion6,
};

let activeVersion = readStoredVersion();

function readStoredVersion() {
  try {
    const n = Number(sessionStorage.getItem(STORAGE_KEY));
    if (Number.isInteger(n) && n >= 1 && n <= VERSION_COUNT) return n;
  } catch {
    /* ignore */
  }
  return 1;
}

function persistVersion(version) {
  try {
    sessionStorage.setItem(STORAGE_KEY, String(version));
  } catch {
    /* ignore */
  }
}

function metaFor(version) {
  return LAYOUT_VERSIONS.find((v) => v.id === version) || LAYOUT_VERSIONS[0];
}

function ensureSectionBreakout() {
  const section = document.getElementById("picks-section");
  if (!section) return;
  section.classList.add("wx-explore-section");
  section.style.setProperty(
    "--wx-max",
    VERSION_MAX_WIDTH[activeVersion] || "1000px",
  );
  section.dataset.wxVersion = String(activeVersion);
}

function ensureSwitcher() {
  const section = document.getElementById("picks-section");
  if (!section || document.getElementById("wx-explore-switcher")) return;

  const switcher = document.createElement("div");
  switcher.id = "wx-explore-switcher";
  switcher.className = "wx-switcher";
  switcher.setAttribute("role", "region");
  switcher.setAttribute("aria-label", "Layout exploration controls");

  switcher.innerHTML = `
    <div class="wx-switcher__meta">
      <span class="wx-switcher__label">Layout exploration</span>
      <span class="wx-switcher__name" id="wx-switcher-name"></span>
      <span class="wx-switcher__counter" id="wx-switcher-counter">1 of 6</span>
    </div>
    <div class="wx-switcher__controls">
      <button type="button" class="wx-switcher__arrow" data-wx-prev aria-label="Previous layout version">←</button>
      <div class="wx-switcher__versions" role="tablist" aria-label="Layout versions">
        ${LAYOUT_VERSIONS.map(
          (v) => `
          <button type="button" class="wx-switcher__version" role="tab"
            data-wx-version="${v.id}" aria-selected="false" id="wx-tab-v${v.id}">${v.id}</button>`,
        ).join("")}
      </div>
      <button type="button" class="wx-switcher__arrow" data-wx-next aria-label="Next layout version">→</button>
    </div>
  `;

  const toggle = section.querySelector(".hub-picks-toggle");
  if (toggle) toggle.insertAdjacentElement("beforebegin", switcher);
  else {
    const header = section.querySelector(".hub-section-header");
    if (header) header.insertAdjacentElement("afterend", switcher);
    else section.prepend(switcher);
  }

  switcher.querySelector("[data-wx-prev]")?.addEventListener("click", () => {
    setVersion(activeVersion <= 1 ? VERSION_COUNT : activeVersion - 1);
  });
  switcher.querySelector("[data-wx-next]")?.addEventListener("click", () => {
    setVersion(activeVersion >= VERSION_COUNT ? 1 : activeVersion + 1);
  });
  switcher.querySelectorAll("[data-wx-version]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const n = Number(btn.getAttribute("data-wx-version"));
      if (Number.isInteger(n)) setVersion(n);
    });
  });

  updateSwitcherUI();
}

function updateSwitcherUI() {
  const meta = metaFor(activeVersion);
  const nameEl = document.getElementById("wx-switcher-name");
  const counterEl = document.getElementById("wx-switcher-counter");
  if (nameEl) nameEl.textContent = `${meta.label}: ${meta.name}`;
  if (counterEl) counterEl.textContent = `${activeVersion} of ${VERSION_COUNT}`;

  document.querySelectorAll("[data-wx-version]").forEach((btn) => {
    const n = Number(btn.getAttribute("data-wx-version"));
    const selected = n === activeVersion;
    btn.classList.toggle("is-active", selected);
    btn.setAttribute("aria-selected", selected ? "true" : "false");
  });

  ensureSectionBreakout();
}

function setVersion(version) {
  if (version < 1 || version > VERSION_COUNT) return;
  activeVersion = version;
  persistVersion(version);
  updateSwitcherUI();
  if (typeof window.STAHomepagePicks?.rerender === "function") {
    window.STAHomepagePicks.rerender();
  }
}

function renderInto(container, picks, helpers) {
  ensureSectionBreakout();
  ensureSwitcher();
  updateSwitcherUI();

  container.className = "wx-host hub-picks-report";
  container.dataset.wxLayout = String(activeVersion);
  container.innerHTML = (RENDERERS[activeVersion] || renderVersion1)(
    picks,
    helpers,
  );

  if (activeVersion === 5) bindVersion5(container);
}

window.STAPicksWidthExplore = {
  renderInto,
  getActiveVersion: () => activeVersion,
  setVersion,
  LAYOUT_VERSIONS,
};

ensureSectionBreakout();
ensureSwitcher();

if (typeof window.STAHomepagePicks?.rerender === "function") {
  window.STAHomepagePicks.rerender();
}
