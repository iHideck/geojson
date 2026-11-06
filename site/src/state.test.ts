import assert from "node:assert/strict";
import { test } from "node:test";
import type { Catalog, CatalogLayer } from "./catalog.ts";
import { initialState, readHash, writeHash } from "./state.ts";

const layer = (id: string, resolutions: string[]): CatalogLayer => ({
  id,
  title: { ja: id, en: id },
  geometry: "polygon",
  outlined: false,
  credit: { ja: "", en: "" },
  license: "CC0-1.0",
  metadata: "",
  resolutions: resolutions.map((r) => ({ id: r, minzoom: 0, maxzoom: 6, pmtiles: "" })),
});
const CATALOG: Catalog = {
  layers: [layer("world/countries", ["50m", "110m"]), layer("japan/municipalities", ["medium", "low"])],
};

test("初めの状態のままなら、地図の位置のほかは何も書かない", () => {
  assert.equal(writeHash("#map=4/36/138", initialState(CATALOG, "ja"), CATALOG, "ja"), "#map=4/36/138");
});

test("書いた状態を読むと、同じ状態に戻る", () => {
  const state = {
    ...initialState(CATALOG, "ja"),
    hidden: new Set(["world/countries"]),
    choices: { "japan/municipalities": "low" },
    lang: "en" as const,
    selected: { layer: "japan/municipalities", index: 12 },
  };
  const hash = writeHash("#map=7/35.6/139.7", state, CATALOG, "ja");
  assert.equal(hash, "#map=7/35.6/139.7&layers=japan/municipalities&res=japan/municipalities:low&lang=en&sel=japan/municipalities:12");
  const read = readHash(hash, CATALOG);
  assert.deepEqual(read.hidden, new Set(["world/countries"]));
  assert.deepEqual(read.choices, { "japan/municipalities": "low" });
  assert.equal(read.lang, "en");
  assert.deepEqual(read.selected, { layer: "japan/municipalities", index: 12 });
});

test("知らないレイヤー・解像度・値は捨てる", () => {
  const read = readHash("#layers=world/eez,world/countries&res=world/countries:10m&lang=fr&sel=world/eez:1", CATALOG);
  assert.deepEqual(read.hidden, new Set(["japan/municipalities"]));
  assert.deepEqual(read.choices, {});
  assert.equal(read.lang, undefined);
  assert.equal(read.selected, undefined);
});
