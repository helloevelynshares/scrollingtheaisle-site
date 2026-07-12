import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  base: "/admin/finds/",
  build: {
    outDir: "admin-finds-dist",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "src/admin/finds/index.html"),
    },
  },
});
