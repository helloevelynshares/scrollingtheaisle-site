import {
  POPULAR_THIS_WEEK_WEEK,
  type PopularThisWeekStore,
} from "./canonicalTrackerFamilies";
import { WEEKLY_AD_WEEKS } from "./weeklyAdPrices.generated";

const STORE_LEAD: Record<PopularThisWeekStore, string> = {
  safeway: "Hand-picked deals I'm watching at Safeway this week",
  vons: "Hand-picked deals I'm watching at Vons this week",
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

/** Combined subtitle — matches homepage `leadLineForView()` in homepage.js. */
export function leadLineForStore(store: PopularThisWeekStore): string {
  const lead = STORE_LEAD[store];
  const week = getPopularWeekLabel();
  const curated = week
    ? `Curated by Scrolling the Aisle · week of ${week}`
    : "Curated by Scrolling the Aisle";
  return `${lead} · ${curated}`;
}
