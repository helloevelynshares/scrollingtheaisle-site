import { useState } from "react";

const STORAGE_KEY = "sta_socal_notice_dismissed";

function readDismissed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function SocalNoticeBanner() {
  const [dismissed, setDismissed] = useState(readDismissed);

  if (dismissed) {
    return null;
  }

  const dismiss = () => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // Ignore quota / private-mode failures; still hide for this session.
    }
    setDismissed(true);
  };

  return (
    <aside
      className="socal-notice-banner"
      role="status"
      aria-label="Southern California update"
    >
      <div className="socal-notice-banner__inner">
        <span className="socal-notice-banner__icon" aria-hidden="true">
          <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle cx="9" cy="9" r="8" stroke="currentColor" strokeWidth="1.5" />
            <path
              d="M9 8v4.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
            <circle cx="9" cy="5.5" r="1" fill="currentColor" />
          </svg>
        </span>
        <div className="socal-notice-banner__body">
          <p className="socal-notice-banner__title">Southern California Update</p>
          <p className="socal-notice-banner__text">
            Weekly price trackers on this page will continue to update
            automatically every week. However, our new videos, deal breakdowns,
            and editorial content are currently focused on the Bay Area while we
            continue improving Scrolling the Aisle.
          </p>
        </div>
        <button
          type="button"
          className="socal-notice-banner__dismiss"
          onClick={dismiss}
          aria-label="Dismiss Southern California update"
        >
          <span aria-hidden="true">×</span>
        </button>
      </div>
    </aside>
  );
}
