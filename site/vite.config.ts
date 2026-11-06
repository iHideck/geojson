import { cpSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import sirv from "sirv";
import { defineConfig, type Plugin } from "vite";

const BASE = "/geojson/";
// make build が作る GitHub Pages のデータ（PMTiles・FlatGeobuf・GeoJSON・目録・STAC）
const PAGES = resolve(import.meta.dirname, "../dist/pages");

// 開発中は dist/pages を Range 要求に応じて配り（PMTiles は Range で読む）、ビルドでは出力に入れる
function pagesData(): Plugin {
  return {
    name: "pages-data",
    configureServer(server) {
      const serve = sirv(PAGES, { dev: true });
      server.middlewares.use(BASE.slice(0, -1), (req, res, next) => serve(req, res, next));
    },
    writeBundle(options) {
      if (!existsSync(PAGES)) {
        throw new Error(`${PAGES} が無い。先に make build でデータを作る`);
      }
      cpSync(PAGES, options.dir ?? "dist", { recursive: true });
    },
  };
}

export default defineConfig({
  base: BASE,
  plugins: [pagesData()],
  build: { target: "es2022", sourcemap: false },
});
