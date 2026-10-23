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
  const started = Date.now();
  const events: Array<{ atSeconds: number; event: string }> = [];
  const responses: unknown[] = [];
  page.on("response", async (response) => {
    if (response.url().endsWith("/api/v1/solve") && response.ok()) responses.push(await response.json());
  });
  const snapshot = async (name: string, event: string) => {
    events.push({ atSeconds: Number(((Date.now() - started) / 1000).toFixed(2)), event });
    await page.screenshot({ path: path.join(out, `${name}.png`), fullPage: true });
  };
  try {
    await page.goto("http://127.0.0.1:5173/");
    await expect(page.getByRole("heading", { name: "Triangle Solver" })).toBeVisible();
    await snapshot("01-giao-dien", "Giao diện local, chưa nhập dữ kiện");
    await page.waitForTimeout(5_000);
    for (const [variable, value] of Object.entries({ a: "3", b: "4", c: "5" })) {
      await page.locator(`#input-${variable}`).pressSequentially(value, { delay: 200 });
      await page.waitForTimeout(1_500);
    }
    for (const name of ["Area", "Altitude to c", "Circumradius"]) {
      await page.getByRole("button", { name: `Find ${name}`, exact: true }).click();
      await page.waitForTimeout(1_500);
    }
    await snapshot("02-du-kien-muc-tieu", "Nhập a=3, b=4, c=5; chọn S, hc, R");
    await page.waitForTimeout(6_000);
    await page.getByRole("button", { name: "Solve selected" }).click();
    await expect(page.getByTestId("status-badge")).toHaveText("SOLVED");
    await expect(page.getByTestId("value-S")).toHaveText("6");
    await expect(page.getByTestId("value-hc")).toHaveText("2.4");
    await expect(page.getByTestId("value-R")).toHaveText("2.5");
    await expect(page.getByTestId("triangle-svg")).toBeVisible();
    await snapshot("03-ket-qua-tam-giac", "Kết quả thật từ API và tam giác SVG");
    await page.waitForTimeout(10_000);
    await page.getByTestId("result-hc").click();
    await expect(page.getByTestId("altitude-hc")).toBeVisible();
    await snapshot("04-duong-cao", "Chọn hc để tô đường cao và chuỗi luật liên quan");
    await page.waitForTimeout(8_000);
    await page.getByRole("button", { name: "Full trace" }).click();
    await page.getByTestId("step-2").scrollIntoViewIfNeeded();
    await page.getByTestId("step-2").click();
    await snapshot("05-cac-buoc-suy-luan", "Mở trace đầy đủ; chọn bước suy luận");
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
    await snapshot("06-tam-giac-khong-hop-le", "Ba cạnh 1,2,3 bị từ chối bởi validator");
    await page.waitForTimeout(10_000);
    await page.getByRole("button", { name: "Reset", exact: true }).click();
    await page.locator("#example-select").selectOption("insufficient");
    await page.getByRole("button", { name: "Solve selected" }).click();
    await expect(page.getByTestId("status-badge")).toHaveText("UNRESOLVED");
    await snapshot("07-thieu-du-kien", "Thiếu dữ kiện trả UNRESOLVED");
    await page.waitForTimeout(8_000);
    expect(responses).toHaveLength(3);
  } finally {
    await context.close();
  }
  await video.saveAs(path.join(out, "triangle-solver-demo.webm"));
  await fs.writeFile(path.join(out, "recording.json"), JSON.stringify({
    recordedAt: new Date().toISOString(),
    browser: await browser.version(), viewport: { width: 1440, height: 1000 },
    source: "Real local Vite and FastAPI application; Chromium viewport recording, no audio",
    durationSeconds: Number(((Date.now() - started) / 1000).toFixed(2)),
    events, responses,
  }, null, 2));
});
