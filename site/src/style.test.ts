import assert from "node:assert/strict";
import { test } from "node:test";
import {
  featureFilter,
  latest,
  normalizePropertyExpression,
  type PropertyValueSpecification,
  type StylePropertySpecification,
} from "@maplibre/maplibre-gl-style-spec";
import type { FillLayerSpecification, FilterSpecification, LayerSpecification } from "maplibre-gl";
import type { Catalog, CatalogLayer } from "./catalog.ts";
import { initialState, STAGES, type ViewState } from "./state.ts";
import { buildStyle, DRAW_FROM, PICK_PARTS } from "./style.ts";

const BASE = new URL("https://example.test/geojson/");
const layer = (id: string, geometry: CatalogLayer["geometry"], resolutions: [string, number, number][], outlined = false): CatalogLayer => ({
  id,
  title: { ja: id, en: id },
  geometry,
  outlined,
  credit: { ja: "", en: "" },
  license: "CC0-1.0",
  metadata: `latest/${id}/metadata.json`,
  resolutions: resolutions.map(([res, minzoom, maxzoom]) => ({ id: res, minzoom, maxzoom, pmtiles: `latest/${id}/${res}.pmtiles` })),
});
const shown = (over: Partial<ViewState> = {}): ViewState => ({ ...initialState(CATALOG, "ja"), hidden: new Set(), revealed: STAGES, ...over });
const CATALOG: Catalog = {
  layers: [
    layer("world/countries", "polygon", [["50m", 2, 6], ["110m", 0, 3]]),
    layer("japan/prefectures", "polygon", [["medium", 6, 10], ["low", 3, 7]]),
    layer("japan/municipalities", "polygon", [["medium", 7, 10], ["low", 5, 8]]),
    layer("japan/islands", "point", [["medium", 2, 8]]),
    layer("world/eez", "polygon", [["50m", 2, 6], ["110m", 0, 3]], true),
  ],
};
const sourceLayer = (style: ReturnType<typeof buildStyle>, id: string): unknown =>
  (style.layers.find((l) => l.id === id) as { "source-layer"?: string } | undefined)?.["source-layer"];

type Probe = Record<string, Record<string, string>>;
const JAPAN_LAND: Probe = { "world/countries": { iso_a3: "JPN" }, "japan/prefectures": { pref_code: "43" } };
const PREFECTURE_TILES_FROM = Math.min(...(CATALOG.layers.find((l) => l.id === "japan/prefectures") as CatalogLayer).resolutions.map((r) => r.minzoom));

function drawing(style: ReturnType<typeof buildStyle>, zoom: number, probe: Probe): LayerSpecification[] {
  return style.layers.filter((l) => {
    const { source, filter } = l as { source?: unknown; filter?: FilterSpecification };
    if (typeof source !== "string" || l.layout?.visibility === "none") return false;
    if (zoom < (l.minzoom ?? 0) || zoom >= (l.maxzoom ?? 24)) return false;
    const properties = probe[source.split("@")[0] as string];
    return properties !== undefined && featureFilter(filter, `layers.${l.id}.filter`).filter({ zoom }, { type: 3, properties });
  });
}

function painters(style: ReturnType<typeof buildStyle>, zoom: number, probe: Probe): string[] {
  return drawing(style, zoom, probe)
    .filter((l): l is FillLayerSpecification => l.type === "fill")
    .filter((l) => {
      const properties = probe[l.source.split("@")[0] as string] as Record<string, string>;
      const evaluate = (property: "fill-color" | "fill-opacity"): unknown => {
        const spec = latest.paint_fill[property] as StylePropertySpecification;
        const value = (l.paint?.[property] ?? spec.default) as PropertyValueSpecification<unknown>;
        return normalizePropertyExpression(value, `layers.${l.id}.paint.${property}`, spec).evaluate({ zoom }, { type: 3, properties });
      };
      return (evaluate("fill-color") as { a: number }).a * (evaluate("fill-opacity") as number) > 0;
    })
    .map((l) => l.id);
}

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

test("面のレイヤーは境界の線を borders で引き、海域（outlined）には名前を出さない", () => {
  const style = buildStyle(CATALOG, BASE, shown());
  assert.equal(sourceLayer(style, "world/countries@50m:line"), "borders");
  assert.equal(sourceLayer(style, "world/eez@50m:line"), "borders");
  assert.ok(style.layers.some((l) => l.id === "world/countries@50m:label"));
  assert.ok(!style.layers.some((l) => l.id.startsWith("world/eez@") && l.id.endsWith(":label")));
});

test("日本の陸は、都道府県のタイルがあるズームから都道府県の形で塗り、ほかの国は国境の形で塗る", () => {
  for (const choice of ["auto", "medium", "low"]) {
    const style = buildStyle(CATALOG, BASE, shown({ choices: { "japan/prefectures": choice } }));
    for (const zoom of [0, 2, 2.99, 3, 4.85, 6.5, 8.3, 12]) {
      const japan = painters(style, zoom, JAPAN_LAND);
      assert.equal(japan.length, 1, `${choice} ${zoom}: ${japan}`);
      assert.equal(japan[0]?.startsWith("japan/prefectures@"), zoom >= PREFECTURE_TILES_FROM, `${choice} ${zoom}: ${japan}`);
      const korea = painters(style, zoom, { "world/countries": { iso_a3: "KOR" } });
      assert.equal(korea.length, 1, `${choice} ${zoom}: ${korea}`);
    }
  }
});

test("日本を都道府県の形で塗るズームでは、国境の形の日本の海岸を引かない", () => {
  const style = buildStyle(CATALOG, BASE, shown());
  const coasts = (zoom: number, iso_a3: string): number =>
    drawing(style, zoom, { "world/countries": { iso_a3 } }).filter((l) => l.type === "line" && l["source-layer"] === "countries").length;
  assert.equal(coasts(PREFECTURE_TILES_FROM - 0.5, "JPN"), 1);
  assert.equal(coasts(8.3, "JPN"), 0);
  assert.equal(coasts(8.3, "KOR"), 1);
});

test("日本の陸は、都道府県を隠しても都道府県の形で塗り、国境のレイヤーの表示と不透明度に従う", () => {
  const noPrefectures = buildStyle(CATALOG, BASE, shown({ hidden: new Set(["japan/prefectures"]) }));
  assert.deepEqual(painters(noPrefectures, 8.3, JAPAN_LAND).map((id) => id.split("@")[0]), ["japan/prefectures"]);
  const noCountries = buildStyle(CATALOG, BASE, shown({ hidden: new Set(["world/countries"]) }));
  assert.deepEqual([1, 8.3].flatMap((zoom) => painters(noCountries, zoom, JAPAN_LAND)), []);
  const faded = buildStyle(CATALOG, BASE, shown({ opacity: { "world/countries": 0.4 } }));
  const [id] = painters(faded, 8.3, JAPAN_LAND);
  const land = faded.layers.find((l) => l.id === id) as FillLayerSpecification;
  assert.equal(land.paint?.["fill-opacity"], 0.4);
});

test("陸の塗りは、境界の線・名前・点より下に描く", () => {
  const style = buildStyle(CATALOG, BASE, shown());
  const at = (match: (l: LayerSpecification) => boolean): number[] => style.layers.flatMap((l, i) => (match(l) ? [i] : []));
  const fills = at((l) => l.type === "fill" && (l.paint?.["fill-opacity"] ?? 1) !== 0);
  const above = at((l) => l.type === "symbol" || l.type === "circle" || (l.type === "line" && l["source-layer"] === "borders"));
  assert.ok(fills.length > 0 && above.length > 0);
  assert.ok(Math.max(...fills) < Math.min(...above));
});

test("日本を都道府県の形で塗るズームでも、日本を押すと国境の地物を選べる", () => {
  const style = buildStyle(CATALOG, BASE, shown({ hidden: new Set(["japan/prefectures"]) }));
  const pickable = drawing(style, 8.3, { "world/countries": { iso_a3: "JPN" } }).filter((l) =>
    PICK_PARTS.some((part) => l.id.endsWith(`:${part}`)),
  );
  assert.equal(pickable.length, 1);
});
