import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

const labRoot = resolve(__dirname, "src/family-tracker-lab");

export default defineConfig({
  plugins: [react()],
  root: labRoot,
  publicDir: resolve(__dirname, "public"),
  base: "/family-tracker-lab/",
  build: {
    outDir: resolve(__dirname, "family-tracker-lab-dist"),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(labRoot, "index.html"),
    },
  },
});
