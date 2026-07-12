import { useCallback, useEffect, useState } from "react";
import { MOCK_FAMILIES } from "./mockData";
import {
  Option1,
  Option2,
  Option3,
  Option4,
  Option5,
  Option6,
  Option7,
  Option8,
  Option9,
} from "./options";

const PREFS_KEY = "family-tracker-lab-prefs";

type OptionPref = "favorite" | "maybe" | null;

type PrefsMap = Record<number, OptionPref>;

const OPTIONS = [
  { num: 1, title: "Minimal family tracker cards", Component: Option1 },
  {
    num: 2,
    title: "Family card with included-varieties drawer",
    Component: Option2,
  },
  { num: 3, title: '"Grouped this week" visual', Component: Option3 },
  { num: 4, title: "Homepage-style compact feed", Component: Option4 },
  { num: 5, title: "Family-first detail page", Component: Option5 },
  { num: 6, title: "Caveat-first but still simple", Component: Option6 },
  { num: 7, title: "Collapsed family rows", Component: Option7 },
  {
    num: 8,
    title: '"What to buy this week" recommendations',
    Component: Option8,
  },
  {
    num: 9,
    title: "Option 2 + price graph (combined)",
    Component: Option9,
  },
] as const;

function loadPrefs(): PrefsMap {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as PrefsMap;
  } catch {
    return {};
  }
}

function savePrefs(prefs: PrefsMap) {
  localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
}

export function FamilyTrackerLabApp() {
  const [prefs, setPrefs] = useState<PrefsMap>(() => loadPrefs());

  useEffect(() => {
    savePrefs(prefs);
  }, [prefs]);

  const setPref = useCallback((num: number, pref: OptionPref) => {
    setPrefs((prev) => {
      const next = { ...prev };
      if (next[num] === pref) {
        delete next[num];
      } else {
        next[num] = pref;
      }
      return next;
    });
  }, []);

  const scrollToOption = (num: number) => {
    document.getElementById(`option-${num}`)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  return (
    <>
      <header className="page-header">
        <a href="/" className="brand">
          SCROLLING THE AISLE
        </a>
        <nav className="site-nav" aria-label="Main">
          <a href="/grocery-price-tracker/" className="site-nav-link">
            Price tracker
          </a>
        </nav>
      </header>

      <main className="page-main ftl-main">
        <section className="ftl-hero">
          <h1>Family Price Tracker UI Lab</h1>
          <p className="ftl-lead">
            These prototypes test family-level tracker cards where flavors/variants
            are grouped unless the price difference matters.
          </p>
          <p className="ftl-lead ftl-lead--secondary">
            Local/staging only — mock Safeway family deals, not connected to
            Supabase or the live price tracker. Delete{" "}
            <code>src/family-tracker-lab/</code> and{" "}
            <code>family-tracker-lab/</code> when done exploring.
          </p>
        </section>

        <section className="ftl-nav-bar" aria-label="Jump to option">
          <p className="ftl-section-label">Jump to option</p>
          <div className="ftl-nav-pills">
            {OPTIONS.map(({ num }) => (
              <button
                key={num}
                type="button"
                className="ftl-jump-btn"
                onClick={() => scrollToOption(num)}
              >
                {num}
                {prefs[num] === "favorite"
                  ? " ★"
                  : prefs[num] === "maybe"
                    ? " ?"
                    : ""}
              </button>
            ))}
          </div>
        </section>

        {OPTIONS.map(({ num, title, Component }) => (
          <section
            key={num}
            id={`option-${num}`}
            className="ftl-option-section"
            aria-labelledby={`option-${num}-heading`}
          >
            <div className="ftl-option-header">
              <div>
                <h2 id={`option-${num}-heading`}>Option {num}</h2>
                <p className="ftl-option-subtitle">{title}</p>
              </div>
              <div className="ftl-pref-buttons">
                <button
                  type="button"
                  className={`ftl-pref-btn${
                    prefs[num] === "favorite" ? " ftl-pref-btn--favorite" : ""
                  }`}
                  onClick={() => setPref(num, "favorite")}
                  aria-pressed={prefs[num] === "favorite"}
                >
                  Favorite
                </button>
                <button
                  type="button"
                  className={`ftl-pref-btn${
                    prefs[num] === "maybe" ? " ftl-pref-btn--maybe" : ""
                  }`}
                  onClick={() => setPref(num, "maybe")}
                  aria-pressed={prefs[num] === "maybe"}
                >
                  Maybe
                </button>
              </div>
            </div>
            <Component families={MOCK_FAMILIES} />
          </section>
        ))}
      </main>
    </>
  );
}
