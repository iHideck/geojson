import { defineConfig, devices } from "@playwright/test";

const PORT = 4173;

// make build で作ったデータ（dist/pages）と、make build-site で作ったビューア（site/dist）を使う
export default defineConfig({
  testDir: "tests",
  timeout: 90_000,
  expect: { timeout: 30_000, toHaveScreenshot: { maxDiffPixelRatio: 0.01 } },
  fullyParallel: false,
  workers: 1,
  reporter: process.env.CI ? [["list"], ["html", { open: "never", outputFolder: "../playwright-report" }]] : "list",
  outputDir: "../test-results",
  use: {
    baseURL: `http://localhost:${PORT}/geojson/`,
    locale: "ja-JP",
    timezoneId: "Asia/Tokyo",
    // ヘッドレスのブラウザで WebGL を使う。GPU の無い環境では、画面の合成まで CPU 描画の WebGL を待って
    // 最初の描画が数秒遅れるので、合成は CPU で行う（lighthouserc.*.json も同じ）
    launchOptions: {
      args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-gpu-compositing"],
    },
  },
  webServer: {
    command: `npx vite preview --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}/geojson/`,
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: "pc", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } } },
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
});
