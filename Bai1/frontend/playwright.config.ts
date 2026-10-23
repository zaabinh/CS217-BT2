import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const python = path.resolve(import.meta.dirname, "..", ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");

export default defineConfig({
  testDir: "e2e",
  fullyParallel: true,
  reporter: [["list"]],
  use: { baseURL: "http://127.0.0.1:5173", ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } },
  webServer: [
    {
      command: `"${python}" -m uvicorn triangle_knowledge_base.app.api.main:app --host 127.0.0.1 --port 8000`,
      cwd: "..",
      url: "http://127.0.0.1:8000/api/v1/variables",
      reuseExistingServer: true,
    },
    { command: "npm run dev -- --host 127.0.0.1", url: "http://127.0.0.1:5173", reuseExistingServer: true },
  ],
});
