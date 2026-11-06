import assert from "node:assert/strict";
import { test } from "node:test";
import type { Catalog, CatalogLayer } from "./catalog.ts";
import { initialState, STAGES, type ViewState } from "./state.ts";
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
const shown = (over: Partial<ViewState> = {}): ViewState => ({ ...initialState(CATALOG, "ja"), hidden: new Set(), revealed: STAGES, ...over });
const CATALOG: Catalog = {
  layers: [
    layer("world/countries", "polygon", [["50m", 2, 6], ["110m", 0, 3]]),
    layer("japan/municipalities", "polygon", [["medium", 7, 10], ["low", 5, 8]]),
    layer("japan/islands", "point", [["medium", 2, 8]]),
  ],
};

test("外部の背景地図タイルや字形を読まず、データはサイトの PMTiles だけを読む", () => {
  const style = buildStyle(CATALOG, BASE, shown());
  assert.equal(style.glyphs, undefined);
  assert.equal(style.sprite, undefined);
  for (const [id, source] of Object.entries(style.sources)) {
    if (source.type === "geojson") continue;
    assert.ok("url" in source && source.url?.startsWith("pmtiles://https://example.test/geojson/latest/"), id);
  }
});

test("市区町村境は、決めたズームより低いところでは描かない", () => {
  const style = buildStyle(CATALOG, BASE, shown());
  const own = style.layers.filter((l) => l.id.startsWith("japan/municipalities@"));
  assert.ok(own.length > 0);
  for (const l of own) {
    if (l.layout?.visibility === "none") continue;
    assert.ok((l.minzoom ?? 0) >= (DRAW_FROM["japan/municipalities"] as number), l.id);
  }
});

test("描かない解像度のレイヤーは隠す", () => {
  const style = buildStyle(CATALOG, BASE, shown({ choices: { "world/countries": "110m" } }));
  const fine = style.layers.filter((l) => l.id.startsWith("world/countries@50m:"));
  assert.ok(fine.length > 0 && fine.every((l) => l.layout?.visibility === "none"));
});

test("隠したレイヤーと、演出でまだ見せていない段階の線は描かない", () => {
  const hidden = buildStyle(CATALOG, BASE, shown({ hidden: new Set(["japan/islands"]) }));
  assert.ok(hidden.layers.filter((l) => l.id.startsWith("japan/islands@")).every((l) => l.layout?.visibility === "none"));
  const intro = buildStyle(CATALOG, BASE, shown({ revealed: 1 }));
  const border = intro.layers.find((l) => l.id === "world/countries@110m:line");
  assert.equal((border?.paint as Record<string, unknown>)["line-opacity"], 0);
  const land = intro.layers.find((l) => l.id === "world/countries@110m:land");
  assert.equal((land?.paint as Record<string, unknown>)["fill-opacity"], 1);
});

test("選んだ地物だけを強調し、英語ではラベルに英語名を使う", () => {
  const style = buildStyle(CATALOG, BASE, shown({ selected: { layer: "japan/islands", index: 7 }, lang: "en" }));
  const selected = style.layers.find((l) => l.id === "japan/islands@medium:selected");
  // PMTiles の地物の番号は 1 から、索引の行は 0 から
  assert.deepEqual((selected as { filter?: unknown }).filter, ["==", ["id"], 8]);
  const other = style.layers.find((l) => l.id === "world/countries@50m:selected");
  assert.deepEqual((other as { filter?: unknown }).filter, ["==", ["id"], -1]);
  const label = style.layers.find((l) => l.id === "japan/islands@medium:label");
  assert.deepEqual((label?.layout as Record<string, unknown>)["text-field"], ["coalesce", ["get", "name_en"], ["get", "name_ja"]]);
});
