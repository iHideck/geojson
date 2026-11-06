// OGP と、WebGL が無いときに見せる静止画（public/og.jpg）を、ビルドしたビューアから撮る。make capture-site で動かす
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";
import { preview } from "vite";

const root = fileURLToPath(new URL("..", import.meta.url));
const out = fileURLToPath(new URL("../public/og.jpg", import.meta.url));
// 日本の全体と、周りの国が入る位置
const VIEW = "#map=4.35/35.2/135.6";

const server = await preview({ root, preview: { port: 4180, strictPort: true } });
const url = server.resolvedUrls?.local[0];
if (!url) throw new Error("プレビューを起こせない");
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, locale: "ja-JP" });
  await page.goto(`${url}${VIEW}`);
  await page.waitForFunction(() => document.documentElement.dataset.ready === "1", null, { timeout: 60_000 });
  await page.evaluate(() => {
    document.documentElement.dataset.shot = "1";
  });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: out, type: "jpeg", quality: 82 });
  console.log(`撮った: ${out}`);
} finally {
  await browser.close();
  await new Promise<void>((resolve) => server.httpServer.close(() => resolve()));
}
