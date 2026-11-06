// 初めに読む HTML・JS・CSS の大きさ（gzip）を、予算と比べる。make check-site-budget で動かす
import { readdirSync, readFileSync } from "node:fs";
import { gzipSync } from "node:zlib";

const KB = 1024;
const TOTAL_LIMIT = 520 * KB;
const APP_LIMIT = 60 * KB;
const dist = new URL("../dist/", import.meta.url);
const maplibre = new URL("../node_modules/maplibre-gl/dist/", import.meta.url);

const gz = (url: URL): number => gzipSync(readFileSync(url)).length;
const files = ["index.html", ...readdirSync(new URL("assets/", dist)).filter((f) => /\.(m?js|css)$/.test(f)).map((f) => `assets/${f}`)];
const sizes = files.map((file) => [file, gz(new URL(file, dist))] as const);
const total = sizes.reduce((sum, [, size]) => sum + size, 0);
// MapLibre は、配られている最小化済みのファイルの大きさを、アプリから除く
const library = ["maplibre-gl.mjs", "maplibre-gl-worker.mjs", "maplibre-gl.css"].reduce((sum, f) => sum + gz(new URL(f, maplibre)), 0);
const app = total - library;
const kb = (bytes: number): string => `${(bytes / KB).toFixed(1)} KB`;
for (const [file, size] of sizes) console.log(`${kb(size).padStart(10)}  ${file}`);
console.log(`合計 ${kb(total)}（予算 ${kb(TOTAL_LIMIT)}）、うちアプリ ${kb(app)}（予算 ${kb(APP_LIMIT)}）`);
if (total > TOTAL_LIMIT || app > APP_LIMIT) {
  console.error("予算を超えた");
  process.exit(1);
}
