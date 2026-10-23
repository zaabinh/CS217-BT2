import { expect, type Page } from "@playwright/test";

export async function fill(page: Page, facts: Record<string, string>) {
  for (const [v, value] of Object.entries(facts)) {
    if (["S", "p", "ha", "hb", "hc", "r", "R"].includes(v) && !(await page.locator(`#input-${v}`).isVisible())) {
      await page.getByRole("button", { name: /Advanced parameters/ }).click();
    }
    await page.locator(`#input-${v}`).fill(value);
  }
}

export async function selectTargets(page: Page, names: string[]) {
  for (const name of names) await page.getByRole("button", { name: `Find ${name}`, exact: true }).click();
}

export async function solve(page: Page) {
  await page.getByRole("button", { name: "Solve selected" }).click();
  await expect(page.getByTestId("status-badge")).toBeVisible();
}
