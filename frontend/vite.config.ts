import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API port can be overridden without editing code:
//   VITE_API_TARGET=http://127.0.0.1:8001 npm run dev -- --port 5174
const apiTarget = process.env.VITE_API_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: apiTarget, changeOrigin: true },
    },
  },
  build: { outDir: "dist" },
});