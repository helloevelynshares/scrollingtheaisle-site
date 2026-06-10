import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  formatPrice,
  getAllPricePoints,
  type TrackedProduct,
} from "../data/priceTrackerV1";
import { useCompactLayout } from "./useCompactLayout";

type Props = {
  product: TrackedProduct;
};

type ChartRow = {
  weekStart: string;
  label: string;
  price: number;
  priceType: string;
  isBaselineFallback: boolean;
  sourceLabel: string;
  offerText?: string;
};

export function PriceTrendChart({ product }: Props) {
  const compact = useCompactLayout();
  const points = getAllPricePoints(product);

  const chartData: ChartRow[] = points.map((point) => ({
    weekStart: point.weekStart,
    label: point.label ?? point.weekStart,
    price: point.price,
    priceType: point.priceType,
    isBaselineFallback: point.isBaselineFallback,
    sourceLabel: point.sourceLabel ?? "",
    offerText: point.offerText,
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
          <Tooltip
            formatter={(value: number, _name, item) => {
              const row = item.payload as ChartRow;
              const kind = row.isBaselineFallback
                ? "Baseline (not in weekly ad)"
                : "Weekly ad";
              return [formatPrice(value), kind];
            }}
            labelFormatter={(_, payload) => {
              const row = payload?.[0]?.payload as ChartRow | undefined;
              if (!row) {
                return "";
              }
              if (row.weekStart === "baseline") {
                return product.baselineSource;
              }
              const parts = [row.sourceLabel];
              if (row.offerText) {
                parts.push(row.offerText);
              }
              return parts.filter(Boolean).join(" · ");
            }}
            contentStyle={{
              borderRadius: 8,
              border: "1px solid #eee",
              fontSize: compact ? 12 : 13,
              maxWidth: 280,
            }}
          />
          <ReferenceLine
            y={product.baselinePrice}
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
