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
  buildUnifiedChartRows,
  formatPrice,
  formatPriceRange,
  getAllPricePoints,
  getChartPricePoints,
  getCostcoChartRegionLabel,
  getEffectiveBaseline,
  hasCostcoChartData,
  isCostcoUnavailableOnChart,
  type UnifiedChartRow,
} from "../data/priceTrackerUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { useCompactLayout } from "./useCompactLayout";

type Props = {
  product: FeedProductView;
  variant?: "default" | "sparkline";
};

type RangeChartRow = {
  weekStart: string;
  label: string;
  price: number;
  priceMax?: number;
  priceType: string;
  isBaselineFallback: boolean;
};

function getGroceryTooltipLabel(
  product: FeedProductView,
  row: UnifiedChartRow | RangeChartRow,
): string {
  if (
    row.weekStart === "baseline" ||
    row.isBaselineFallback ||
    row.priceType === "baseline"
  ) {
    return `${product.feedLabel} baseline`;
  }
  return `${product.feedLabel} weekly ad`;
}

function getRangeTooltipLabel(): string {
  return "Sale price range";
}

function PriceChartTooltip({
  active,
  payload,
  compact,
  rangeMode,
  product,
  costcoRegionLabel,
}: TooltipProps<number, string> & {
  compact: boolean;
  rangeMode: boolean;
  product: FeedProductView;
  costcoRegionLabel: string | null;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const entry =
    payload.find(
      (item) =>
        item.value != null &&
        item.dataKey !== "priceMax" &&
        item.dataKey !== "groceryPriceMax",
    ) ?? payload[0];
  const row = entry.payload as UnifiedChartRow | RangeChartRow;
  const dataKey = String(entry.dataKey ?? "price");

  let seriesLabel: string;
  let priceLabel: string;

  if (dataKey === "costcoPrice") {
    const costcoRow = row as UnifiedChartRow;
    seriesLabel = costcoRegionLabel
      ? `Costco (${costcoRegionLabel})`
      : "Costco warehouse";
    priceLabel = formatPrice(costcoRow.costcoPrice);
  } else if (rangeMode && dataKey === "priceMax") {
    seriesLabel = getRangeTooltipLabel();
    const rangeRow = row as RangeChartRow;
    priceLabel =
      rangeRow.priceMax != null &&
      Math.abs(rangeRow.priceMax - rangeRow.price) >= 0.01
        ? formatPriceRange({ min: rangeRow.price, max: rangeRow.priceMax })
        : formatPrice(rangeRow.price);
  } else if (rangeMode) {
    seriesLabel = getRangeTooltipLabel();
    const rangeRow = row as RangeChartRow;
    priceLabel = formatPrice(rangeRow.price);
  } else {
    const groceryRow = row as UnifiedChartRow;
    seriesLabel = getGroceryTooltipLabel(product, groceryRow);
    priceLabel = formatPrice(groceryRow.groceryPrice);
  }

  return (
    <div
      className={`price-tracker-chart-tooltip${
        compact ? " price-tracker-chart-tooltip--compact" : ""
      }`}
    >
      <div className="price-tracker-chart-tooltip-date">{row.label}</div>
      <div className="price-tracker-chart-tooltip-series">{seriesLabel}</div>
      <div className="price-tracker-chart-tooltip-price">{priceLabel}</div>
    </div>
  );
}

export function PriceTrendChart({ product, variant = "default" }: Props) {
  const compact = useCompactLayout();
  const sparkline = variant === "sparkline";
  const minimal = compact || sparkline;
  // rangeMode is driven by chartMode only; brand_family YAML families use
  // chartMode:"single" and should show the baseline + weekly-ad + Costco chart.
  // Only deal_family products with multiple members set chartMode:"range".
  const rangeMode = product.chartMode === "range";
  const showCostcoOverlay = !sparkline && !rangeMode && hasCostcoChartData(product);
  const costcoRegionLabel = getCostcoChartRegionLabel(product);
  const costcoUnavailable = isCostcoUnavailableOnChart(product);
  const baseline = getEffectiveBaseline(product);

  const rangeChartData: RangeChartRow[] = (
    sparkline && rangeMode ? getChartPricePoints(product) : getAllPricePoints(product)
  ).map((point) => ({
    weekStart: point.weekStart,
    label: point.label ?? point.weekStart,
    price: point.price,
    priceMax: point.priceMax ?? point.price,
    priceType: point.priceType,
    isBaselineFallback: point.isBaselineFallback,
  }));

  const unifiedChartData = rangeMode ? [] : buildUnifiedChartRows(product);

  const chartData = rangeMode ? rangeChartData : unifiedChartData;
  const hasCostcoLine =
    showCostcoOverlay && unifiedChartData.some((row) => row.costcoPrice != null);

  const allValues = rangeMode
    ? chartData.flatMap((row) => {
        const rangeRow = row as RangeChartRow;
        return rangeRow.priceMax != null && rangeRow.priceMax !== rangeRow.price
          ? [rangeRow.price, rangeRow.priceMax]
          : [rangeRow.price];
      })
    : (chartData as UnifiedChartRow[]).flatMap((row) => {
        const values = [row.groceryPrice];
        if (row.costcoPrice != null) {
          values.push(row.costcoPrice);
        }
        return values;
      });

  const yMin = allValues.length > 0 ? Math.min(...allValues) : 0;
  const yMax = allValues.length > 0 ? Math.max(...allValues) : 0;
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
              shared={false}
              content={
                <PriceChartTooltip
                  compact={minimal}
                  rangeMode={rangeMode}
                  product={product}
                  costcoRegionLabel={costcoRegionLabel}
                />
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
            {rangeMode ? (
              <Line
                type="monotone"
                dataKey="price"
                stroke={sparkline ? "#b0b0b0" : "#222"}
                strokeWidth={sparkline ? 1 : compact ? 1.5 : 2}
                strokeOpacity={sparkline ? 0.7 : 1}
                dot={(props) => {
                  const { cx, cy, payload } = props;
                  const row = payload as RangeChartRow;
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
            ) : (
              <Line
                type="monotone"
                dataKey="groceryPrice"
                stroke={sparkline ? "#b0b0b0" : "#222"}
                strokeWidth={sparkline ? 1 : compact ? 1.5 : 2}
                strokeOpacity={sparkline ? 0.7 : 1}
                dot={(props) => {
                  const { cx, cy, payload } = props;
                  const row = payload as UnifiedChartRow;
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
            )}
            {!rangeMode && hasCostcoLine ? (
              <Line
                type="monotone"
                dataKey="costcoPrice"
                stroke="#0071ce"
                strokeWidth={compact ? 1.5 : 2}
                strokeDasharray="6 4"
                dot={{ r: compact ? 2.5 : 3.5, fill: "#0071ce", stroke: "#fff" }}
                connectNulls
                isAnimationActive={false}
              />
            ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
      {!sparkline && costcoUnavailable ? (
        <p className="price-tracker-chart-costco-unavailable">
          Not available at Costco
          {costcoRegionLabel ? ` (${costcoRegionLabel} warehouse)` : ""}
        </p>
      ) : null}
    </div>
  );
}
