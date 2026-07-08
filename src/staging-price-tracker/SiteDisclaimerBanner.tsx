export const SITE_DISCLAIMER_TEXT =
  "I'm still manually reviewing content on this site, so you may spot incorrect prices or details. The Scrolling The Aisle videos are fully reviewed and accurate! Improving the site day by day, so check back often.";

export function SiteDisclaimerBanner() {
  return (
    <aside
      className="site-disclaimer"
      role="note"
      aria-label="Content accuracy notice"
    >
      <div className="site-disclaimer__inner">
        <span className="site-disclaimer__badge">Note</span>
        <p className="site-disclaimer__text">{SITE_DISCLAIMER_TEXT}</p>
      </div>
    </aside>
  );
}
