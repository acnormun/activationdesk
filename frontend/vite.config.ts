import { fileURLToPath, URL } from "node:url"
import vue from "@vitejs/plugin-vue"
import { defineConfig } from "vitest/config"

// The backend CORS policy allows http://localhost:3000 with credentials
// (backend/app/main.py), so the dev server must keep that port.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 3000,
  },
  test: {
    environment: "node",
    include: ["test/**/*.spec.ts"],
  },
})
