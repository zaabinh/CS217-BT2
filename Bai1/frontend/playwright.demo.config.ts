import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

export default defineConfig({
  ...base,
  testDir: "demo",
  fullyParallel: false,
  workers: 1,
  timeout: 180_000,
  outputDir: "test-results/demo",
});
