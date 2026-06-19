import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from "recharts";
import {
  formatPrice,
  formatPriceRange,
  getAllPricePoints,
  getChartPricePoints,
  getCostcoChartPricePoints,
  getEffectiveBaseline,
  isDealFamily,
} from "../data/priceTrackerUtils";
import { getCostcoComparisonLocationNote } from "../data/costcoRegions";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { useCompactLayout } from "./useCompactLayout";

type Props = {
  product: FeedProductView;
  variant?: "default" | "sparkline";
};

type ChartRow = {
  weekStart: string;
  label: string;
  price: number;
  priceMax?: number;
  priceType: string;
  isBaselineFallback: boolean;
};

function getTooltipStatus(row: ChartRow): "Weekly deal" | "Regular price" {
  if (
    row.weekStart === "baseline" ||
    row.isBaselineFallback ||
    row.priceType === "baseline"
  ) {
    return "Regular price";
  }
  return "Weekly deal";
}

function PriceChartTooltip({
  active,
  payload,
  compact,
  rangeMode,
}: TooltipProps<number, string> & { compact: boolean; rangeMode: boolean }) {
  if (!active || !payload?.length) {
    return null;
  }

  const row = payload[0].payload as ChartRow;
  const priceLabel =
    rangeMode &&
    row.priceMax != null &&
    Math.abs(row.priceMax - row.price) >= 0.01
      ? formatPriceRange({ min: row.price, max: row.priceMax })
      : formatPrice(row.price);

  return (
    <div
      className={`price-tracker-chart-tooltip${
        compact ? " price-tracker-chart-tooltip--compact" : ""
      }`}
    >
      <div className="price-tracker-chart-tooltip-date">{row.label}</div>
      <div className="price-tracker-chart-tooltip-price">{priceLabel}</div>
      <div className="price-tracker-chart-tooltip-status">
        {getTooltipStatus(row)}
      </div>
    </div>
  );
}

export function PriceTrendChart({ product, variant = "default" }: Props) {
  const compact = useCompactLayout();
  const sparkline = variant === "sparkline";
  const minimal = compact || sparkline;
  const rangeMode =
    product.chartMode === "range" || isDealFamily(product);
  const points =
    sparkline && rangeMode
      ? getChartPricePoints(product)
      : getAllPricePoints(product);
  const costcoPoints =
    sparkline || rangeMode ? [] : getCostcoChartPricePoints(product);
  const costcoLocationNote = getCostcoComparisonLocationNote(product.feedId);
  const baseline = getEffectiveBaseline(product);

  const chartData: ChartRow[] = points.map((point) => ({
    weekStart: point.weekStart,
    label: point.label ?? point.weekStart,
    price: point.price,
    priceMax: point.priceMax ?? point.price,
    priceType: point.priceType,
    isBaselineFallback: point.isBaselineFallback,
  }));

  const allValues = chartData.flatMap((row) =>
    row.priceMax != null && row.priceMax !== row.price
      ? [row.price, row.priceMax]
      : [row.price],
  );
  const costcoValues = costcoPoints.map((point) => point.price);
  const combinedValues =
    costcoValues.length > 0 ? [...allValues, ...costcoValues] : allValues;
  const yMin = combinedValues.length > 0 ? Math.min(...combinedValues) : 0;
  const yMax = combinedValues.length > 0 ? Math.max(...combinedValues) : 0;
  const padding = Math.max(0.5, (yMax - yMin) * 0.12 || 0.5);

  return (
    <div
      className={`price-tracker-chart${
        compact ? " price-tracker-chart--compact" : ""
      }${sparkline ? " price-tracker-chart--sparkline" : ""}${
        rangeMode ? " price-tracker-chart--range" : ""
      }`}
    >
      <div className="price-tracker-chart-plot">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={
              sparkline
                ? { top: 2, right: 0, left: 0, bottom: 0 }
                : compact
                  ? { top: 4, right: 2, left: 0, bottom: 0 }
                  : { top: 8, right: 8, left: 0, bottom: 8 }
            }
          >
            {!minimal ? (
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            ) : null}
            {!minimal ? (
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: "#6b6b6b" }}
                interval="preserveStartEnd"
              />
            ) : null}
            {minimal ? (
              <YAxis hide domain={[yMin - padding, yMax + padding]} width={0} />
            ) : (
              <YAxis
                domain={[yMin - padding, yMax + padding]}
                tick={{ fontSize: 11, fill: "#6b6b6b" }}
                tickFormatter={(value) => `$${Number(value).toFixed(2)}`}
                width={48}
              />
            )}
            <Tooltip
              content={
                <PriceChartTooltip compact={minimal} rangeMode={rangeMode} />
              }
            />
            {baseline != null && !rangeMode && !sparkline ? (
              <ReferenceLine
                y={baseline}
                stroke="#ff385c"
                strokeDasharray="4 4"
                strokeWidth={compact ? 1 : 1.5}
                label={
                  compact
                    ? undefined
                    : {
                        value: "Baseline",
                        position: "insideTopRight",
                        fill: "#ff385c",
                        fontSize: 11,
                      }
                }
              />
            ) : null}
            {rangeMode ? (
              <Line
                type="monotone"
                dataKey="priceMax"
                stroke={sparkline ? "#d8d8d8" : "#bbb"}
                strokeWidth={sparkline ? 0.75 : compact ? 1 : 1.5}
                strokeDasharray="4 3"
                strokeOpacity={sparkline ? 0.55 : 1}
                dot={false}
                connectNulls
                activeDot={false}
              />
            ) : null}
            <Line
              type="monotone"
              dataKey="price"
              stroke={sparkline ? "#b0b0b0" : "#222"}
              strokeWidth={sparkline ? 1 : compact ? 1.5 : 2}
              strokeOpacity={sparkline ? 0.7 : 1}
              dot={(props) => {
                const { cx, cy, payload } = props;
                const row = payload as ChartRow;
                const fill = sparkline
                  ? row.isBaselineFallback
                    ? "#d0d0d0"
                    : "#b8b8b8"
                  : row.weekStart === "baseline"
                    ? "#ff385c"
                    : row.isBaselineFallback
                      ? "#bbb"
                      : "#222";
                const radius = sparkline
                  ? 1.5
                  : compact
                    ? row.weekStart === "baseline"
                      ? 3.5
                      : 2.5
                    : row.weekStart === "baseline"
                      ? 5
                      : 4;
                if (sparkline && cx == null) {
                  return <circle r={0} />;
                }
                return (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={radius}
                    fill={fill}
                    stroke={sparkline ? "none" : "#fff"}
                    strokeWidth={sparkline ? 0 : compact ? 1 : 1.5}
                    opacity={sparkline ? 0.75 : 1}
                  />
                );
              }}
              activeDot={
                sparkline ? { r: 3, fill: "#999" } : { r: compact ? 4 : 6 }
              }
              connectNulls
            />
            {costcoPoints.length > 0 ? (
              <Line
                type="monotone"
                data={costcoPoints.map((point) => ({
                  weekStart: point.weekStart,
                  label: point.label ?? point.weekStart,
                  price: point.price,
                  priceType: point.priceType,
                  isBaselineFallback: point.isBaselineFallback,
                }))}
                dataKey="price"
                stroke="#0071ce"
                strokeWidth={compact ? 1.5 : 2}
                strokeDasharray="6 4"
                dot={{ r: compact ? 2.5 : 3.5, fill: "#0071ce", stroke: "#fff" }}
                connectNulls
                name="Costco"
              />
            ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
      {!sparkline ? (
        <>
          <p className="price-tracker-chart-legend price-tracker-desktop-only">
            {rangeMode ? (
              <span className="price-tracker-chart-legend-item">
                <span className="price-tracker-chart-dot price-tracker-chart-dot--range" />
                Sale price range across formats
              </span>
            ) : (
              <>
                <span className="price-tracker-chart-legend-item">
                  <span className="price-tracker-chart-dot price-tracker-chart-dot--ad" />
                  Weekly ad match
                </span>
                <span className="price-tracker-chart-legend-item">
                  <span className="price-tracker-chart-dot price-tracker-chart-dot--baseline" />
                  Baseline / no ad match
                </span>
                {costcoPoints.length > 0 ? (
                  <span className="price-tracker-chart-legend-item">
                    <span className="price-tracker-chart-dot price-tracker-chart-dot--costco" />
                    Costco warehouse
                  </span>
                ) : null}
              </>
            )}
          </p>
          {costcoPoints.length > 0 && costcoLocationNote ? (
            <p className="price-tracker-chart-costco-note">{costcoLocationNote}</p>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
