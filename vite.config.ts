import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  base: "/grocery-price-tracker/",
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: "price-tracker-dist",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "src/staging-price-tracker/index.html"),
    },
  },
});
