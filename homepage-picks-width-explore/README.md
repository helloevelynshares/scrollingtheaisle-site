# Highlights width layout exploration

Temporary experiment: six wider editorial layouts for the weekly highlights section.

## Structure

`index.html` wraps hero + trust in `.hub-main.hub-narrow` and leaves `#picks-section` as a sibling under `.hub-shell`, so highlights can use ~1120–1360px while the intro stays ~1040px.

## How to remove

1. Delete `homepage-picks-width-explore/`
2. Remove the TEMP `explore.css` / `explore.js` tags from `index.html`
3. Remove the `STAPicksWidthExplore` branch, `picksExploreHelpers()`, and `window.STAHomepagePicks` from `homepage.js`
4. Move `#picks-section` back inside a single `.hub-main` (or keep a chosen wider max-width on the section)
