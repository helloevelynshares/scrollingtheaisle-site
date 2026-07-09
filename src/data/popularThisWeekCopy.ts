import {
  POPULAR_THIS_WEEK_WEEK,
  type PopularThisWeekStore,
} from "./canonicalTrackerFamilies";
import { isPreviewWeek } from "./weeklyAdPreview";
import { WEEKLY_AD_WEEKS } from "./weeklyAdPrices.generated";

const STORE_LEAD: Record<PopularThisWeekStore, string> = {
  safeway: "Hand-picked deals I'm watching at Safeway this week",
  vons: "Hand-picked deals I'm watching at Vons this week",
};

/** Optional weekly shopping strategy blurb shown under the section lead. */
const STORE_STRATEGY: Partial<Record<PopularThisWeekStore, string>> = {
  vons:
    "This week's Vons strategy: start with $5 Friday, especially Cheez-Its and Post cereal; use Buy 4 Mix & Match for Ritz if you want smaller boxes near Costco pricing; then grab the clear Costco-beaters like blueberries, cantaloupe, and Chobani. For the Game Time Favorites promo, make sure you hit $20 so the extra $5 comes off — Nature Valley is the cleanest example.",
};

function formatWeekRange(weekStart: string, weekEnd?: string): string {
  const start = new Date(`${weekStart}T12:00:00`);
  if (!weekEnd) {
    return start.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
  const end = new Date(`${weekEnd}T12:00:00`);
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${fmt(start)}–${fmt(end)}`;
}

function latestWeekLabel(): string {
  const latest = WEEKLY_AD_WEEKS[WEEKLY_AD_WEEKS.length - 1];
  if (!latest) {
    return "This week";
  }
  return formatWeekRange(latest.weekStart, latest.weekEnd);
}

/** Human-readable week range for Popular this week (from YAML week or latest ad week). */
export function getPopularWeekLabel(): string {
  if (!POPULAR_THIS_WEEK_WEEK) {
    return latestWeekLabel();
  }
  const week = WEEKLY_AD_WEEKS.find(
    (entry) => entry.weekStart === POPULAR_THIS_WEEK_WEEK,
  );
  if (week) {
    return formatWeekRange(week.weekStart, week.weekEnd);
  }
  return formatWeekRange(POPULAR_THIS_WEEK_WEEK);
}

/** Whether the curated Popular this week ad week is still a preview (not yet started). */
export function isPopularWeekPreview(asOf: Date = new Date()): boolean {
  if (!POPULAR_THIS_WEEK_WEEK) {
    return false;
  }
  return isPreviewWeek(POPULAR_THIS_WEEK_WEEK, asOf);
}

/** Combined subtitle — matches homepage `leadLineForView()` in homepage.js. */
export function leadLineForStore(store: PopularThisWeekStore): string {
  const lead = STORE_LEAD[store];
  const week = getPopularWeekLabel();
  const curated = week
    ? `Curated by Scrolling the Aisle · week of ${week}`
    : "Curated by Scrolling the Aisle";
  return `${lead} · ${curated}`;
}

export function strategyLineForStore(store: PopularThisWeekStore): string | undefined {
  return STORE_STRATEGY[store];
}
