#!/usr/bin/env node
/** Copy admin stores build output into admin/stores/ for GitHub Pages. */
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from "fs";
import { join } from "path";

const root = new URL("..", import.meta.url).pathname;
const dist = join(root, "admin-stores-dist");
const target = join(root, "admin", "stores");
const assetsTarget = join(target, "assets");

const indexCandidates = [
  join(dist, "index.html"),
  join(dist, "admin", "stores", "index.html"),
  join(dist, "src/admin/stores", "index.html"),
];
const builtIndex = indexCandidates.find((p) => existsSync(p));

if (!builtIndex) {
  console.error("Admin stores index.html not found under admin-stores-dist/");
  process.exit(1);
}

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
console.log("Synced admin-stores-dist → admin/stores/");
