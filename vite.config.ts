import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  base: "/staging-price-tracker/",
  build: {
    outDir: "price-tracker-dist",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "staging-price-tracker/index.html"),
    },
  },
});
