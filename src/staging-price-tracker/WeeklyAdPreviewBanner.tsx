import {
  formatPreviewBannerMessage,
  getFeedAdPreviewState,
} from "../data/weeklyAdPreview";
import { WEEKLY_AD_WEEKS } from "../data/weeklyAdPrices.generated";
import { VONS_WEEKLY_AD_WEEKS } from "../data/vonsWeeklyAdPrices.generated";

type Props = {
  feedStore: "safeway" | "vons";
};

export function WeeklyAdPreviewBanner({ feedStore }: Props) {
  const weeks = feedStore === "vons" ? VONS_WEEKLY_AD_WEEKS : WEEKLY_AD_WEEKS;
  const feedLabel = feedStore === "vons" ? "Vons" : "Safeway";
  const state = getFeedAdPreviewState(weeks);

  if (!state?.isPreview) {
    return null;
  }

  return (
    <div className="weekly-ad-preview-banner" role="status">
      <span className="weekly-ad-preview-banner__badge">Preview</span>
      <p className="weekly-ad-preview-banner__text">
        {formatPreviewBannerMessage(feedLabel, state.weekStart)}
      </p>
    </div>
  );
}
