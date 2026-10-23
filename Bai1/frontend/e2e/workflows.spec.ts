import { expect, test } from "@playwright/test";
import { fill, selectTargets, solve } from "./helpers";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("E2E-01 basic 3-4-5 triangle", async ({ page }) => {
  await fill(page, { a: "3", b: "4", c: "5" });
  await selectTargets(page, ["Area", "Altitude to c", "Circumradius"]);
  await solve(page);
  await expect(page.getByTestId("status-badge")).toHaveText("SOLVED");
  await expect(page.getByTestId("value-S")).toHaveText("6");
  await expect(page.getByTestId("value-hc")).toHaveText("2.4");
  await expect(page.getByTestId("value-R")).toHaveText("2.5");
  await expect(page.getByTestId("triangle-svg")).toBeVisible();
  await page.getByRole("button", { name: /Solution steps/ }).click();
  await expect(page.getByTestId("step-1")).toContainText("R04");
});

test("E2E-02 SAS builds a right triangle", async ({ page }) => {
  await fill(page, { b: "3", c: "4", A: "90" });
  await selectTargets(page, ["Side a", "Area"]);
  await solve(page);
  await expect(page.getByTestId("value-a")).toHaveText("5");
  await expect(page.getByTestId("value-S")).toHaveText("6");
  // The drawn sides must be proportional to 5:3:4 with the right angle at A.
  const lengths = await page.getByTestId("triangle-svg").evaluate((svg) => {
    const len = (id: string) => {
      const line = svg.querySelector(`[data-testid="side-${id}"] line`)!;
      const [x1, y1, x2, y2] = ["x1", "y1", "x2", "y2"].map((k) => Number(line.getAttribute(k)));
      return Math.hypot(x2 - x1, y2 - y1);
    };
    return { a: len("a"), b: len("b"), c: len("c") };
  });
  expect(lengths.b / lengths.a).toBeCloseTo(0.6, 3);
  expect(lengths.c / lengths.a).toBeCloseTo(0.8, 3);
  expect(lengths.b ** 2 + lengths.c ** 2).toBeCloseTo(lengths.a ** 2, 0);
});

test("E2E-03 insufficient information stays unresolved", async ({ page }) => {
  await fill(page, { a: "3" });
  await selectTargets(page, ["Area"]);
  await solve(page);
  await expect(page.getByTestId("status-badge")).toHaveText("UNRESOLVED");
  await expect(page.getByTestId("value-S")).toHaveText("—");
  await expect(page.getByTestId("triangle-svg")).toHaveCount(0);
  await expect(page.getByTestId("viz-message")).toHaveText("Enter sufficient parameters to construct a triangle.");
});

test("E2E-04 invalid triangle", async ({ page }) => {
  await fill(page, { a: "1", b: "2", c: "3" });
  await selectTargets(page, ["Area"]);
  await solve(page);
  await expect(page.getByTestId("status-badge")).toHaveText("INVALID");
  await expect(page.getByText(/These side lengths cannot form a valid triangle/)).toBeVisible();
  await expect(page.getByTestId("triangle-svg")).toHaveCount(0);
});

test("E2E-05 inconsistent data is not shown as success", async ({ page }) => {
  await fill(page, { a: "3", b: "4", c: "5", S: "7" });
  await selectTargets(page, ["Area"]);
  await solve(page);
  await expect(page.getByTestId("status-badge")).toHaveText("INCONSISTENT");
  await expect(page.getByText("Solved", { exact: true })).toHaveCount(0);
  await expect(page.getByTestId("result-S")).toHaveCount(0);
  await expect(page.getByText(/R20 Heron/)).toBeVisible();
  await expect(page.getByTestId("triangle-svg")).toHaveCount(0);
});

for (const [name, width, height, columns] of [["desktop", 1440, 900, 2], ["tablet", 768, 1024, 1], ["mobile", 390, 844, 1]] as const) {
  test(`E2E-06 responsive layout: ${name}`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await page.locator("#example-select").selectOption("345");
    await solve(page);
    const inputs = await page.getByRole("region", { name: "Known parameters" }).boundingBox();
    const viz = await page.getByRole("region", { name: "Triangle" }).boundingBox();
    if (columns === 2) expect(viz!.x).toBeGreaterThan(inputs!.x + inputs!.width - 1);
    else expect(viz!.y).toBeGreaterThan(inputs!.y + inputs!.height - 1);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(0);
    const svg = await page.getByTestId("triangle-svg").boundingBox();
    expect(svg!.x + svg!.width).toBeLessThanOrEqual(width);
  });
}

test("E2E-07 modifying a fact marks results stale", async ({ page }) => {
  await page.locator("#example-select").selectOption("345");
  await solve(page);
  await expect(page.getByTestId("stale-banner")).toHaveCount(0);
  await page.locator("#input-a").fill("3.5");
  await expect(page.getByTestId("stale-banner")).toBeVisible();
  await expect(page.getByTestId("triangle-svg")).toHaveCount(0);
  await page.getByRole("button", { name: "Solve selected" }).click();
  await expect(page.getByTestId("stale-banner")).toHaveCount(0);
  await expect(page.getByTestId("value-S")).not.toHaveText("6");
});

test("E2E-08 selecting a result highlights geometry and steps", async ({ page }) => {
  await page.locator("#example-select").selectOption("345");
  await solve(page);
  await page.getByTestId("result-hc").click();
  await expect(page.getByTestId("altitude-hc")).toBeVisible();
  await expect(page.getByTestId("step-1")).toBeVisible();
  await expect(page.getByRole("button", { name: /Steps for/ })).toHaveAttribute("aria-pressed", "true");
  await page.getByTestId("result-R").click();
  await expect(page.getByTestId("circumcircle")).toBeVisible();
  // Keyboard access on the drawing itself.
  await page.getByTestId("side-b").focus();
  await expect(page.getByText("b = 4: Side b, given", { exact: true })).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("side-b")).toHaveAttribute("data-highlight", "primary");
});
