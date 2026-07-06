#!/usr/bin/env node
/** Copy Vite build output into family-tracker-lab/ for GitHub Pages (optional local lab deploy). */
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from "fs";
import { join } from "path";

const root = new URL("..", import.meta.url).pathname;
const dist = join(root, "family-tracker-lab-dist");
const target = join(root, "family-tracker-lab");
const assetsTarget = join(target, "assets");

const indexCandidates = [
  join(dist, "index.html"),
  join(dist, "family-tracker-lab", "index.html"),
  join(dist, "src/family-tracker-lab", "index.html"),
];
const builtIndex = indexCandidates.find((p) => existsSync(p));

if (!builtIndex) {
  console.error("Build index.html not found under family-tracker-lab-dist/");
  process.exit(1);
}

rmSync(join(target, "family-tracker-lab"), { recursive: true, force: true });
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
console.log("Synced family-tracker-lab-dist → family-tracker-lab/");
