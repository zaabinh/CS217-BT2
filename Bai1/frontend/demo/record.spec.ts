import fs from "node:fs/promises";
import path from "node:path";
import { expect, test } from "@playwright/test";

// Records a real Chromium viewport against the running Vite/FastAPI application.
// Kept outside e2e/ so routine tests do not include the intentional viewing pauses.
test("record the local triangle solver walkthrough", async ({ browser }) => {
  const out = path.resolve("../Demo");
  await fs.mkdir(out, { recursive: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    recordVideo: { dir: "test-results/demo-video", size: { width: 1440, height: 1000 } },
  });
  const page = await context.newPage();
  const video = page.video()!;
  try {
    await page.goto("http://127.0.0.1:5173/");
    await expect(page.getByRole("heading", { name: "Triangle Solver" })).toBeVisible();
    await page.waitForTimeout(5_000);
    for (const [variable, value] of Object.entries({ a: "3", b: "4", c: "5" })) {
      await page.locator(`#input-${variable}`).pressSequentially(value, { delay: 200 });
      await page.waitForTimeout(1_500);
    }
    for (const name of ["Area", "Altitude to c", "Circumradius"]) {
      await page.getByRole("button", { name: `Find ${name}`, exact: true }).click();
      await page.waitForTimeout(1_500);
    }
    await page.waitForTimeout(6_000);
    await page.getByRole("button", { name: "Solve selected" }).click();
    await expect(page.getByTestId("status-badge")).toHaveText("SOLVED");
    await expect(page.getByTestId("value-S")).toHaveText("6");
    await expect(page.getByTestId("value-hc")).toHaveText("2.4");
    await expect(page.getByTestId("value-R")).toHaveText("2.5");
    await expect(page.getByTestId("triangle-svg")).toBeVisible();
    await page.waitForTimeout(10_000);
    await page.getByTestId("result-hc").click();
    await expect(page.getByTestId("altitude-hc")).toBeVisible();
    await page.waitForTimeout(8_000);
    await page.getByRole("button", { name: "Full trace" }).click();
    await page.getByTestId("step-2").scrollIntoViewIfNeeded();
    await page.getByTestId("step-2").click();
    await page.waitForTimeout(12_000);
    await page.getByTestId("result-R").click();
    await expect(page.getByTestId("circumcircle")).toBeVisible();
    await page.getByTestId("triangle-svg").scrollIntoViewIfNeeded();
    await page.waitForTimeout(8_000);
    await page.getByRole("button", { name: "Reset", exact: true }).click();
    await page.locator("#example-select").selectOption("invalid");
    await page.waitForTimeout(4_000);
    await page.getByRole("button", { name: "Solve selected" }).click();
    await expect(page.getByTestId("status-badge")).toHaveText("INVALID");
    await expect(page.getByTestId("triangle-svg")).toHaveCount(0);
    await page.waitForTimeout(10_000);
    await page.getByRole("button", { name: "Reset", exact: true }).click();
    await page.locator("#example-select").selectOption("insufficient");
    await page.getByRole("button", { name: "Solve selected" }).click();
    await expect(page.getByTestId("status-badge")).toHaveText("UNRESOLVED");
    await page.waitForTimeout(8_000);
  } finally {
    await context.close();
  }
  await video.saveAs(path.join(out, "triangle-solver-demo.webm"));
});
