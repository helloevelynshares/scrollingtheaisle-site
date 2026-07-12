#!/usr/bin/env node
/** Copy Vite build output into grocery-price-tracker/ for GitHub Pages. */
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from "fs";
import { join } from "path";

const root = new URL("..", import.meta.url).pathname;
const dist = join(root, "price-tracker-dist");
const target = join(root, "grocery-price-tracker");
const assetsTarget = join(target, "assets");

const indexCandidates = [
  join(dist, "index.html"),
  join(dist, "grocery-price-tracker", "index.html"),
  join(dist, "src/staging-price-tracker", "index.html"),
];
const builtIndex = indexCandidates.find((p) => existsSync(p));

if (!builtIndex) {
  console.error("Build index.html not found under price-tracker-dist/");
  process.exit(1);
}

rmSync(join(target, "grocery-price-tracker"), { recursive: true, force: true });
rmSync(assetsTarget, { recursive: true, force: true });
mkdirSync(assetsTarget, { recursive: true });

const distAssets = join(dist, "assets");
if (existsSync(distAssets)) {
  for (const file of readdirSync(distAssets)) {
    cpSync(join(distAssets, file), join(assetsTarget, file), { force: true });
  }
}

cpSync(builtIndex, join(target, "index.html"), { force: true });

rmSync(dist, { recursive: true, force: true });
console.log("Synced price-tracker-dist → grocery-price-tracker/");
