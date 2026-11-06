import { expect, type Page, test } from "@playwright/test";

// 演出を省いて開く位置（共有の URL と同じ形）
const JAPAN = "#map=4.85/36.4/138.2";

type MapHandle = {
  loaded(): boolean;
  getZoom(): number;
  jumpTo(options: { center: [number, number]; zoom: number }): void;
  querySourceFeatures(source: string, options: { sourceLayer: string }): { id?: number; properties: Record<string, unknown> }[];
  queryRenderedFeatures(options: { layers: string[] }): { id?: number; properties: Record<string, unknown>; geometry: { coordinates: [number, number] } }[];
  project(lngLat: [number, number]): { x: number; y: number };
};

declare global {
  interface Window {
    __map: MapHandle;
    __state: () => { revealed: number; selected: { layer: string; index: number } | null };
  }
}

async function ready(page: Page): Promise<void> {
  await page.waitForFunction(() => document.documentElement.dataset.ready === "1");
}

test("PMTiles を Range 要求で読み、国境と島を描く", async ({ page }) => {
  const ranges: number[] = [];
  page.on("response", (response) => {
    if (response.url().endsWith(".pmtiles")) ranges.push(response.status());
  });
  await page.goto(JAPAN);
  await ready(page);
  const counts = await page.evaluate(() => ({
    countries: window.__map.querySourceFeatures("world/countries@50m", { sourceLayer: "countries" }).length,
    islands: window.__map.querySourceFeatures("japan/islands@medium", { sourceLayer: "islands" }).length,
  }));
  expect(counts.countries).toBeGreaterThan(0);
  expect(counts.islands).toBeGreaterThan(0);
  expect(ranges.length).toBeGreaterThan(0);
  expect(ranges.every((status) => status === 206)).toBe(true);
});

test("外部のサーバーには何も要求しない（背景地図・字形・アクセス解析を読まない）", async ({ page, baseURL }) => {
  const origin = new URL(baseURL as string).origin;
  const outside: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.protocol.startsWith("http") && url.origin !== origin) outside.push(request.url());
  });
  await page.goto(JAPAN);
  await ready(page);
  await page.waitForTimeout(1000);
  expect(outside).toEqual([]);
});

test("地図の上の島を押すと、同じ島の詳細が出る", async ({ page }) => {
  await page.goto("#map=8/26.5/127.9");
  await ready(page);
  // 凡例や上の帯に隠れていない、地図の上に見えている島を選ぶ
  const island = await page.evaluate(() => {
    const canvas = document.querySelector("#map canvas");
    for (const feature of window.__map.queryRenderedFeatures({ layers: ["japan/islands@medium:point"] })) {
      const point = window.__map.project(feature.geometry.coordinates);
      if (document.elementFromPoint(point.x, point.y) === canvas) {
        return { name: String(feature.properties.name_ja), x: point.x, y: point.y };
      }
    }
    return null;
  });
  expect(island).not.toBeNull();
  if (!island) return;
  await page.mouse.click(island.x, island.y);
  await expect(page.locator("#card-name")).toHaveText(island.name);
  expect(page.url()).toContain("sel=japan/islands:");
});

test("検索で島を選ぶと、その島へ移って詳細を出す", async ({ page }) => {
  await page.goto(JAPAN);
  await ready(page);
  const search = page.locator("#search");
  if (!(await search.isVisible())) await page.locator(".menu-button").click();
  await search.fill("さど");
  await expect(page.locator("#search-results li").first()).toContainText("佐渡島");
  await search.press("Enter");
  await expect(page.locator("#card-name")).toHaveText("佐渡島");
});

test("演出は Esc で飛ばせ、すべてのレイヤーを見せる", async ({ page }) => {
  await page.goto("");
  await expect(page.locator("#skip")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect.poll(() => page.evaluate(() => window.__state().revealed)).toBe(4);
  await expect(page.locator("#skip")).toBeHidden();
});

test("英語に切り替えると、画面と地図のラベルが英語になる", async ({ page }) => {
  await page.goto(JAPAN);
  await ready(page);
  if (!(await page.locator('[data-lang="en"]').isVisible())) await page.locator(".menu-button").click();
  await page.locator('[data-lang="en"]').click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator(".disclaimer")).toContainText(/legal/);
  expect(page.url()).toContain("lang=en");
});

test("見た目が変わっていない", async ({ page }) => {
  await page.goto(JAPAN);
  await ready(page);
  await page.waitForTimeout(1500);
  await expect(page).toHaveScreenshot("japan.png", { animations: "disabled" });
});
