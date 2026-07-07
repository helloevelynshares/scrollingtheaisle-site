import type { WeeklyAdWeek } from "./weeklyAdPrices.generated";

/** ISO date string (YYYY-MM-DD) for local calendar day. */
export function isoDateOnly(value: Date = new Date()): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function isPreviewWeek(weekStart: string, asOf: Date = new Date()): boolean {
  return isoDateOnly(asOf) < weekStart;
}

export function isActiveAdWeek(
  weekStart: string,
  weekEnd: string,
  asOf: Date = new Date(),
): boolean {
  const today = isoDateOnly(asOf);
  return today >= weekStart && today <= weekEnd;
}

export function getLatestAdWeek(weeks: WeeklyAdWeek[]): WeeklyAdWeek | null {
  if (weeks.length === 0) {
    return null;
  }
  return [...weeks].sort((a, b) => a.weekStart.localeCompare(b.weekStart)).at(-1) ?? null;
}

export type FeedAdPreviewState = {
  isPreview: boolean;
  weekStart: string;
  weekEnd: string;
  sourceLabel: string;
};

export function getFeedAdPreviewState(
  weeks: WeeklyAdWeek[],
  asOf: Date = new Date(),
): FeedAdPreviewState | null {
  const latest = getLatestAdWeek(weeks);
  if (!latest) {
    return null;
  }
  return {
    isPreview: isPreviewWeek(latest.weekStart, asOf),
    weekStart: latest.weekStart,
    weekEnd: latest.weekEnd,
    sourceLabel: latest.sourceLabel,
  };
}

/** User-facing relative start label, e.g. "tomorrow" or "Jul 8". */
export function formatPreviewStartLabel(
  weekStart: string,
  asOf: Date = new Date(),
): string {
  const tomorrow = new Date(asOf);
  tomorrow.setDate(tomorrow.getDate() + 1);
  if (isoDateOnly(tomorrow) === weekStart) {
    return "tomorrow";
  }
  const start = new Date(`${weekStart}T12:00:00`);
  return start.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function formatPreviewBannerMessage(
  feedLabel: string,
  weekStart: string,
  asOf: Date = new Date(),
): string {
  const startLabel = formatPreviewStartLabel(weekStart, asOf);
  if (startLabel === "tomorrow") {
    return `Preview prices from the upcoming ${feedLabel} weekly ad — deals start tomorrow (${formatAdWeekStartDate(weekStart)}).`;
  }
  return `Preview prices from the upcoming ${feedLabel} weekly ad — deals start ${startLabel}.`;
}

export function formatAdWeekStartDate(weekStart: string): string {
  const start = new Date(`${weekStart}T12:00:00`);
  return start.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

export function formatPreviewPriceLabel(
  priceLabel: string,
  weekStart: string,
  asOf: Date = new Date(),
): string {
  const startLabel = formatPreviewStartLabel(weekStart, asOf);
  return `Preview: ${priceLabel} starting ${startLabel}`;
}
