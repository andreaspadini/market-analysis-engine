import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      // allow importing from the monorepo root
      allow: [".."],
    },
  },
  resolve: {
    dedupe: ["react", "react-dom", "react-router-dom"],
  },
});
