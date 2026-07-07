#!/usr/bin/env node
/** Build data/homepage-preview.generated.json from price tracker modules (via Vite SSR). */
import { mkdirSync, writeFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { createServer } from "vite";

const root = join(fileURLToPath(new URL("..", import.meta.url)));
const outPath = join(root, "data/homepage-preview.generated.json");

const server = await createServer({
  root,
  configFile: false,
  server: { middlewareMode: true },
  logLevel: "error",
});

try {
  const mod = await server.ssrLoadModule("/src/homepage/previewData.ts");
  const data = mod.buildHomepagePreview();
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(data, null, 2)}\n`);
  console.log(
    `Wrote ${outPath} (${data.popularPicksSafeway.length} Safeway popular, ${data.popularPicksVons.length} Vons popular)`,
  );
} finally {
  await server.close();
}
