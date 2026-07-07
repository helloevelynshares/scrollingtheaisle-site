import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  base: "/admin/stores/",
  build: {
    outDir: "admin-stores-dist",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "src/admin/stores/index.html"),
    },
  },
});
