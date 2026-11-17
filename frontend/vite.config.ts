import { fileURLToPath, URL } from "node:url"
import vue from "@vitejs/plugin-vue"
import { defineConfig } from "vitest/config"

// The frontend calls the API on the same origin; in local dev the Vite server
// proxies those paths to the backend (http://localhost:8000).
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/auth": "http://localhost:8000",
      "/accounts": "http://localhost:8000",
      "/plan": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
  test: {
    environment: "node",
    include: ["test/**/*.spec.ts"],
  },
})
