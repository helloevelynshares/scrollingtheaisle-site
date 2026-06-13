import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  base: "/admin/suggestions/",
  build: {
    outDir: "admin-suggestions-dist",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "src/admin/suggestions/index.html"),
    },
  },
});
