import assert from "node:assert/strict";
import { test } from "node:test";
import type { Catalog, CatalogLayer } from "./catalog.ts";
import { buildStyle, DRAW_FROM } from "./style.ts";

const BASE = new URL("https://example.test/geojson/");
const layer = (id: string, geometry: CatalogLayer["geometry"], resolutions: [string, number, number][]): CatalogLayer => ({
  id,
  title: { ja: id, en: id },
  geometry,
  credit: { ja: "", en: "" },
  license: "CC0-1.0",
  metadata: `latest/${id}/metadata.json`,
  resolutions: resolutions.map(([res, minzoom, maxzoom]) => ({ id: res, minzoom, maxzoom, pmtiles: `latest/${id}/${res}.pmtiles` })),
});
const CATALOG: Catalog = {
  layers: [
    layer("world/countries", "polygon", [["50m", 2, 6], ["110m", 0, 3]]),
    layer("japan/municipalities", "polygon", [["medium", 7, 10], ["low", 5, 8]]),
    layer("japan/islands", "point", [["medium", 2, 8]]),
  ],
};

test("外部の背景地図タイルや字形を読まず、データはサイトの PMTiles だけを読む", () => {
  const style = buildStyle(CATALOG, BASE, { choices: {} });
  assert.equal(style.glyphs, undefined);
  assert.equal(style.sprite, undefined);
  for (const [id, source] of Object.entries(style.sources)) {
    if (source.type === "geojson") continue;
    assert.ok("url" in source && source.url?.startsWith("pmtiles://https://example.test/geojson/latest/"), id);
  }
});

test("市区町村境は、決めたズームより低いところでは描かない", () => {
  const style = buildStyle(CATALOG, BASE, { choices: {} });
  const own = style.layers.filter((l) => l.id.startsWith("japan/municipalities@"));
  assert.ok(own.length > 0);
  for (const l of own) {
    if (l.layout?.visibility === "none") continue;
    assert.ok((l.minzoom ?? 0) >= (DRAW_FROM["japan/municipalities"] as number), l.id);
  }
});

test("描かない解像度のレイヤーは隠す", () => {
  const style = buildStyle(CATALOG, BASE, { choices: { "world/countries": "110m" } });
  const fine = style.layers.filter((l) => l.id.startsWith("world/countries@50m:"));
  assert.ok(fine.length > 0 && fine.every((l) => l.layout?.visibility === "none"));
});
