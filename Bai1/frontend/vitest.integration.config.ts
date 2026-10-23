import { defineConfig } from "vitest/config";

// Runs against a live FastAPI server (see README); no mocks, no jsdom.
export default defineConfig({
  test: { environment: "node", include: ["src/**/*.integration.test.ts"] },
});
