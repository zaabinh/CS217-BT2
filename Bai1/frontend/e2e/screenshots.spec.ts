import { expect, test } from "@playwright/test";
import { fill, selectTargets, solve } from "./helpers";

// Captures the delivery screenshots from the real running app into ../docs/screenshots.
const out = (name: string) => `../docs/screenshots/${name}.png`;


test("desktop screenshots", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Triangle Solver" })).toBeVisible();
  await page.screenshot({ path: out("desktop-initial"), fullPage: true });

  await fill(page, { a: "3", b: "4", c: "5" });
  await selectTargets(page, ["Area", "Altitude to c", "Circumradius"]);
  await solve(page);
  await page.getByTestId("result-hc").click();
  await page.mouse.move(0, 0);
  await page.screenshot({ path: out("desktop-solved"), fullPage: true });

  await page.getByTestId("step-1").scrollIntoViewIfNeeded();
  await page.getByRole("button", { name: "Full trace" }).click();
  await page.getByTestId("step-2").click();
  await page.screenshot({ path: out("desktop-inference"), fullPage: true });

  await page.getByRole("button", { name: "Reset", exact: true }).click();
  await page.locator("#example-select").selectOption("invalid");
  await solve(page);
  await page.screenshot({ path: out("desktop-invalid"), fullPage: true });

  await page.getByRole("button", { name: "Reset", exact: true }).click();
  await page.locator("#example-select").selectOption("insufficient");
  await solve(page);
  await page.screenshot({ path: out("desktop-unresolved"), fullPage: true });
});

test("mobile solved", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.locator("#example-select").selectOption("345");
  await solve(page);
  await page.getByTestId("result-S").click();
  await page.screenshot({ path: out("mobile-solved"), fullPage: true });
});

test("tablet layout", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/");
  await page.locator("#example-select").selectOption("sas");
  await solve(page);
  await page.screenshot({ path: out("tablet-layout"), fullPage: true });
});
