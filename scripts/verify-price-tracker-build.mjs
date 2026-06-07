#!/usr/bin/env node
/** Fail if the deployed price-tracker bundle is missing generated weekly ad data. */
import { readFileSync, readdirSync } from "fs";
import { join } from "path";

const root = new URL("..", import.meta.url).pathname;
const generatedPath = join(root, "src/data/weeklyAdPrices.generated.ts");
const assetsDir = join(root, "staging-price-tracker/assets");
const indexPath = join(root, "staging-price-tracker/index.html");

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
  console.error("No index-*.js bundle found under staging-price-tracker/assets/");
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
    "The Vite entry may be wrong — build from src/staging-price-tracker/index.html, not staging-price-tracker/index.html.",
  );
  process.exit(1);
}

if (indexHtml.includes("/src/staging-price-tracker/main.tsx")) {
  console.error(
    "staging-price-tracker/index.html still references main.tsx — sync/deploy output looks wrong.",
  );
  process.exit(1);
}

if (!indexHtml.includes(jsBundle)) {
  console.error(`staging-price-tracker/index.html does not reference ${jsBundle}`);
  process.exit(1);
}

console.log(
  `Price tracker build OK: ${weekStarts.length} weeks through ${latestWeek} in ${jsBundle}`,
);
