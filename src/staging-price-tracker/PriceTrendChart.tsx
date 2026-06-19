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
  getAllPricePoints,
  getEffectiveBaseline,
} from "../data/priceTrackerUtils";
import type { FeedProductView } from "../data/priceTrackerTypes";
import { useCompactLayout } from "./useCompactLayout";

type Props = {
  product: FeedProductView;
};

type ChartRow = {
  weekStart: string;
  label: string;
  price: number;
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
}: TooltipProps<number, string> & { compact: boolean }) {
  if (!active || !payload?.length) {
    return null;
  }

  const row = payload[0].payload as ChartRow;

  return (
    <div
      className={`price-tracker-chart-tooltip${
        compact ? " price-tracker-chart-tooltip--compact" : ""
      }`}
    >
      <div className="price-tracker-chart-tooltip-date">{row.label}</div>
      <div className="price-tracker-chart-tooltip-price">
        {formatPrice(row.price)}
      </div>
      <div className="price-tracker-chart-tooltip-status">
        {getTooltipStatus(row)}
      </div>
    </div>
  );
}

export function PriceTrendChart({ product }: Props) {
  const compact = useCompactLayout();
  const points = getAllPricePoints(product);
  const baseline = getEffectiveBaseline(product);

  const chartData: ChartRow[] = points.map((point) => ({
    weekStart: point.weekStart,
    label: point.label ?? point.weekStart,
    price: point.price,
    priceType: point.priceType,
    isBaselineFallback: point.isBaselineFallback,
  }));

  const yMin = Math.min(...chartData.map((row) => row.price));
  const yMax = Math.max(...chartData.map((row) => row.price));
  const padding = Math.max(0.5, (yMax - yMin) * 0.12 || 0.5);

  return (
    <div
      className={`price-tracker-chart${
        compact ? " price-tracker-chart--compact" : ""
      }`}
    >
      <div className="price-tracker-chart-plot">
        <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={
            compact
              ? { top: 4, right: 2, left: 0, bottom: 0 }
              : { top: 8, right: 8, left: 0, bottom: 8 }
          }
        >
          {!compact ? (
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          ) : null}
          {!compact ? (
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: "#6b6b6b" }}
              interval="preserveStartEnd"
            />
          ) : null}
          {compact ? (
            <YAxis hide domain={[yMin - padding, yMax + padding]} width={0} />
          ) : (
            <YAxis
              domain={[yMin - padding, yMax + padding]}
              tick={{ fontSize: 11, fill: "#6b6b6b" }}
              tickFormatter={(value) => `$${Number(value).toFixed(2)}`}
              width={48}
            />
          )}
          <Tooltip content={<PriceChartTooltip compact={compact} />} />
          {baseline != null ? (
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
          <Line
            type="monotone"
            dataKey="price"
            stroke="#222"
            strokeWidth={compact ? 1.5 : 2}
            dot={(props) => {
              const { cx, cy, payload } = props;
              const row = payload as ChartRow;
              const fill =
                row.weekStart === "baseline"
                  ? "#ff385c"
                  : row.isBaselineFallback
                    ? "#bbb"
                    : "#222";
              const radius = compact
                ? row.weekStart === "baseline"
                  ? 3.5
                  : 2.5
                : row.weekStart === "baseline"
                  ? 5
                  : 4;
              return (
                <circle
                  cx={cx}
                  cy={cy}
                  r={radius}
                  fill={fill}
                  stroke="#fff"
                  strokeWidth={compact ? 1 : 1.5}
                />
              );
            }}
            activeDot={{ r: compact ? 4 : 6 }}
            connectNulls
          />
        </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="price-tracker-chart-legend price-tracker-desktop-only">
        <span className="price-tracker-chart-legend-item">
          <span className="price-tracker-chart-dot price-tracker-chart-dot--ad" />
          Weekly ad match
        </span>
        <span className="price-tracker-chart-legend-item">
          <span className="price-tracker-chart-dot price-tracker-chart-dot--baseline" />
          Baseline / no ad match
        </span>
      </p>
    </div>
  );
}
