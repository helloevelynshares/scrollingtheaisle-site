#!/usr/bin/env node
/** Fail if the deployed grocery-price-tracker bundle is missing generated weekly ad data. */
import { readFileSync, readdirSync } from "fs";
import { join } from "path";

const root = new URL("..", import.meta.url).pathname;
const generatedPath = join(root, "src/data/weeklyAdPrices.generated.ts");
const safewayBaselinesPath = join(root, "src/data/priceTrackerFallback.ts");
const vonsBaselinesPath = join(root, "src/data/vonsBaseline.generated.ts");
const assetsDir = join(root, "grocery-price-tracker/assets");
const indexPath = join(root, "grocery-price-tracker/index.html");

const generated = readFileSync(generatedPath, "utf8");
const weekStarts = [
  ...generated.matchAll(/"weekStart": "(\d{4}-\d{2}-\d{2})"/g),
].map((match) => match[1]);

if (weekStarts.length === 0) {
  console.error("No weekStart entries found in weeklyAdPrices.generated.ts");
  process.exit(1);
}

const jsBundle = readdirSync(assetsDir).find(
  (name) => name.startsWith("index-") && name.endsWith(".js"),
);
if (!jsBundle) {
  console.error("No index-*.js bundle found under grocery-price-tracker/assets/");
  process.exit(1);
}

const bundle = readFileSync(join(assetsDir, jsBundle), "utf8");
const indexHtml = readFileSync(indexPath, "utf8");
const latestWeek = weekStarts[weekStarts.length - 1];

const missingWeeks = weekStarts.filter((week) => !bundle.includes(week));
if (missingWeeks.length > 0) {
  console.error(
    `Price tracker bundle ${jsBundle} is missing weekly ad data: ${missingWeeks.join(", ")}`,
  );
  console.error(
    "The Vite entry may be wrong, build from src/staging-price-tracker/index.html, not grocery-price-tracker/index.html.",
  );
  process.exit(1);
}

if (indexHtml.includes("/src/staging-price-tracker/main.tsx")) {
  console.error(
    "grocery-price-tracker/index.html still references main.tsx, sync/deploy output looks wrong.",
  );
  process.exit(1);
}

if (!indexHtml.includes(jsBundle)) {
  console.error(`grocery-price-tracker/index.html does not reference ${jsBundle}`);
  process.exit(1);
}

/** Fail closed when a shipped baseline is <= 0 (renders as Usually $0). */
function collectInvalidBaselines(source, label) {
  const invalid = [];
  const entryRe =
    /["']([a-z0-9_]+)["']\s*:\s*\{[\s\S]*?(?:price|baselinePrice)\s*:\s*(-?\d+(?:\.\d+)?)/g;
  for (const match of source.matchAll(entryRe)) {
    const id = match[1];
    const price = Number(match[2]);
    if (!Number.isFinite(price) || price <= 0) {
      invalid.push(`${label}:${id}=${price}`);
    }
  }
  return invalid;
}

const safewaySource = readFileSync(safewayBaselinesPath, "utf8");
const vonsSource = readFileSync(vonsBaselinesPath, "utf8");
const invalidBaselines = [
  ...collectInvalidBaselines(safewaySource, "SAFEWAY_BASELINES"),
  ...collectInvalidBaselines(vonsSource, "VONS_BASELINE"),
];
if (invalidBaselines.length > 0) {
  console.error(
    `Invalid baseline price(s) <= 0 (would show as Usually $0):\n  ${invalidBaselines.join("\n  ")}`,
  );
  process.exit(1);
}

const laysPartyMatch = safewaySource.match(
  /"lays_party_size"\s*:\s*\{[\s\S]*?price:\s*([0-9.]+)/,
);
if (!laysPartyMatch || Number(laysPartyMatch[1]) !== 5.99) {
  console.error(
    `Expected SAFEWAY_BASELINES.lays_party_size.price === 5.99, got ${laysPartyMatch?.[1] ?? "missing"}`,
  );
  process.exit(1);
}

if (!bundle.includes("lays_party_size") || !bundle.includes("5.99")) {
  console.error(
    `Price tracker bundle ${jsBundle} is missing lays_party_size / $5.99 baseline data.`,
  );
  process.exit(1);
}

console.log(
  `Price tracker build OK: ${weekStarts.length} weeks through ${latestWeek} in ${jsBundle}; baselines > 0; lays_party_size=$5.99`,
);
