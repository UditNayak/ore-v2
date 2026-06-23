import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server runs on 5173; API base URL is supplied via VITE_API_URL.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
  },
});
