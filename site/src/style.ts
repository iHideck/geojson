import type { Feature, FeatureCollection } from "geojson";
import type {
  ExpressionSpecification,
  FilterSpecification,
  LayerSpecification,
  SourceSpecification,
  StyleSpecification,
} from "maplibre-gl";
import { type Catalog, type CatalogLayer, featureId, type Resolution } from "./catalog.ts";
import { FALLBACK_LINE, LINES, type LineLook, PALETTE, POINT } from "./palette.ts";
import { MAX_ZOOM, type ZoomRange, zoomRanges } from "./resolution.ts";
import type { ViewState } from "./state.ts";

// 下から順に描く。目録にあって、ここに無いレイヤーは最後に描く
const DRAW_ORDER = [
  "world/countries",
  "world/high-seas",
  "world/eez",
  "world/contiguous-zones",
  "world/territorial-seas",
  "world/baselines",
  "japan/municipalities",
  "japan/prefectures",
  "japan/islands",
];

// タイルがあっても、このズームより低いところでは描かない（読み込みもしない）。市区町村境を全国で一度に描くと見づらく、重い
export const DRAW_FROM: Readonly<Record<string, number>> = { "japan/municipalities": 7 };

// 名前を出す国・地域。日本の周りと、世界地図で目印になる国
const LABELLED = ["JPN", "CHN", "KOR", "PRK", "RUS", "TWN", "PHL", "MNG", "USA", "CAN", "AUS", "IDN", "IND", "BRA"];

const JAPAN: ExpressionSpecification = ["==", ["get", "iso_a3"], "JPN"];

// 名前を出し始めるズーム
const LABEL_FROM: Readonly<Record<string, number>> = { "japan/prefectures": 5, "japan/municipalities": 9 };

// 演出で見せる順番。0 は最初から見せる
const STAGE = { land: 0, graticule: 1, borders: 2, japan: 3, labels: 4 } as const;
const FADE = { duration: 1000, delay: 0 };

// 地図の上で選べる部分。前にあるものを先に選ぶ
export const PICK_PARTS = ["point", "area"] as const;

type Part = {
  spec: LayerSpecification;
  stage: number;
  // 不透明度を持つ描き方の名前と、レイヤーの不透明度が 1 のときの値
  opacity: [string, number][];
};

type Owner = { hidden: boolean; opacity: number; from: number };
const GROUND: Owner = { hidden: false, opacity: 1, from: 0 };
const ownerOf = (layer: CatalogLayer, state: ViewState): Owner => ({
  hidden: state.hidden.has(layer.id),
  opacity: state.opacity[layer.id] ?? 1,
  from: DRAW_FROM[layer.id] ?? 0,
});

export const sourceId = (layer: CatalogLayer, res: Resolution): string => `${layer.id}@${res.id}`;
const tilesOf = (layer: CatalogLayer): string => layer.id.split("/").at(-1) as string;

function width(look: LineLook, factor = 1): ExpressionSpecification {
  const [z3, z6, z9] = look.width.map((w) => w * factor) as [number, number, number];
  return ["interpolate", ["linear"], ["zoom"], 3, z3, 6, z6, 9, z9];
}

function graticule(step: number): FeatureCollection {
  const line = (coordinates: number[][], major: boolean): Feature => ({
    type: "Feature",
    properties: { major },
    geometry: { type: "LineString", coordinates },
  });
  const features: Feature[] = [];
  for (let lon = -180; lon <= 180; lon += step) {
    const coords = [];
    for (let lat = -80; lat <= 80; lat += 2) coords.push([lon, lat]);
    features.push(line(coords, lon % 30 === 0));
  }
  for (let lat = -80; lat <= 80; lat += step) {
    const coords = [];
    for (let lon = -180; lon <= 180; lon += 2) coords.push([lon, lat]);
    features.push(line(coords, lat % 30 === 0));
  }
  return { type: "FeatureCollection", features };
}

function name(lang: ViewState["lang"]): ExpressionSpecification {
  return lang === "en" ? ["coalesce", ["get", "name_en"], ["get", "name_ja"]] : ["get", "name_ja"];
}

function partsFor(layer: CatalogLayer, res: Resolution, state: ViewState): Part[] {
  const source = sourceId(layer, res);
  const tiles = tilesOf(layer);
  const id = (part: string): string => `${source}:${part}`;
  const look = LINES[layer.id] ?? FALLBACK_LINE;
  const selected: FilterSpecification = ["==", ["id"], state.selected?.layer === layer.id ? featureId(state.selected.index) : -1];
  if (layer.geometry === "point") {
    const radius = (add: number): ExpressionSpecification => [
      "interpolate", ["linear"], ["zoom"], 3, POINT.radius[0] + add, 6, POINT.radius[1] + add, 9, POINT.radius[2] + add,
    ]; // prettier-ignore
    return [
      {
        spec: {
          id: id("point"),
          type: "circle",
          source,
          "source-layer": tiles,
          paint: {
            "circle-radius": radius(0),
            "circle-color": PALETTE.ocean,
            "circle-stroke-color": POINT.color,
            "circle-stroke-width": 1.2,
          },
        },
        stage: STAGE.japan,
        opacity: [
          ["circle-opacity", 1],
          ["circle-stroke-opacity", 1],
        ],
      },
      {
        spec: {
          id: id("selected"),
          type: "circle",
          source,
          "source-layer": tiles,
          filter: selected,
          paint: {
            "circle-radius": radius(3),
            "circle-color": "rgba(0,0,0,0)",
            "circle-stroke-color": PALETTE.highlight,
            "circle-stroke-width": 2,
          },
        },
        stage: 0,
        opacity: [],
      },
      {
        spec: {
          id: id("label"),
          type: "symbol",
          source,
          "source-layer": tiles,
          minzoom: 4.5,
          layout: {
            "text-field": name(state.lang),
            "text-size": ["interpolate", ["linear"], ["zoom"], 4.5, 10, 9, 13],
            "text-anchor": "left",
            "text-offset": [0.7, 0],
            "text-padding": 4,
          },
          paint: { "text-color": PALETTE.label, "text-halo-color": PALETTE.halo, "text-halo-width": 1.4 },
        },
        stage: STAGE.labels,
        opacity: [["text-opacity", 1]],
      },
    ];
  }
  const parts: Part[] = [];
  if (layer.geometry === "polygon") {
    // 地物を選べるように、見えない塗りを敷く
    parts.push({
      spec: {
        id: id("area"),
        type: "fill",
        source,
        "source-layer": tiles,
        paint: { "fill-color": "#000000", "fill-opacity": 0 },
      },
      stage: 0,
      opacity: [],
    });
  }
  const lines = layer.geometry === "polygon" ? "borders" : tiles;
  const stage = layer.id === "world/countries" ? STAGE.borders : STAGE.japan;
  if (look.glow) {
    parts.push({
      spec: {
        id: id("glow"),
        type: "line",
        source,
        "source-layer": lines,
        layout: { "line-join": "round", "line-cap": "round" },
        paint: { "line-color": look.color, "line-width": width(look, 3.5), "line-blur": 4 },
      },
      stage,
      opacity: [["line-opacity", look.glow]],
    });
  }
  parts.push({
    spec: {
      id: id("line"),
      type: "line",
      source,
      "source-layer": lines,
      layout: { "line-join": "round" },
      paint: {
        "line-color": look.color,
        "line-width": width(look),
        ...(look.dash ? { "line-dasharray": [...look.dash] } : {}),
      },
    },
    stage,
    opacity: [["line-opacity", 1]],
  });
  if (layer.geometry === "polygon") {
    parts.push({
      spec: {
        id: id("selected"),
        type: "line",
        source,
        "source-layer": tiles,
        filter: selected,
        layout: { "line-join": "round" },
        paint: { "line-color": PALETTE.highlight, "line-width": 2.2 },
      },
      stage: 0,
      opacity: [],
    });
  }
  // 海域（outlined）には名前を出さない。区域が重なり、どの区域の名前かが分からないため
  if (layer.geometry === "polygon" && !layer.outlined) {
    // 名前は、データの側が地物ごとに1つ作った点（labels）に置く。面に置くと、タイルや島ごとに何度も出る
    const countries = layer.id === "world/countries";
    parts.push({
      spec: {
        id: id("label"),
        type: "symbol",
        source,
        "source-layer": "labels",
        minzoom: countries ? 0 : (LABEL_FROM[layer.id] ?? 0),
        ...(countries ? { maxzoom: 6, filter: ["in", ["get", "iso_a3"], ["literal", LABELLED]] as FilterSpecification } : {}),
        layout: {
          "text-field": name(state.lang),
          "text-size": countries ? 11 : 12,
          "text-letter-spacing": countries ? 0.2 : 0.08,
          "text-padding": 8,
        },
        paint: { "text-color": PALETTE.label, "text-halo-color": PALETTE.halo, "text-halo-width": 1.2 },
      },
      stage: STAGE.labels,
      opacity: [["text-opacity", countries ? 0.8 : 0.9]],
    });
  }
  return parts;
}

function place(owner: Owner, part: Part, range: ZoomRange | null, revealed: number): LayerSpecification {
  const spec = part.spec;
  const minzoom = Math.max(spec.minzoom ?? 0, range?.[0] ?? 0, owner.from);
  const maxzoom = Math.min(spec.maxzoom ?? MAX_ZOOM, range?.[1] ?? 0);
  if (owner.hidden || minzoom >= maxzoom) {
    return { ...spec, layout: { ...spec.layout, visibility: "none" } } as LayerSpecification;
  }
  const paint: Record<string, unknown> = { ...spec.paint };
  for (const [property, base] of part.opacity) {
    paint[property] = revealed >= part.stage ? base * owner.opacity : 0;
    paint[`${property}-transition`] = FADE;
  }
  return { ...spec, minzoom, maxzoom, paint } as LayerSpecification;
}

function ground(catalog: Catalog, state: ViewState): LayerSpecification[] {
  const countries = catalog.layers.find((l) => l.id === "world/countries");
  if (!countries) return [];
  const prefectures = catalog.layers.find((l) => l.id === "japan/prefectures");
  const fine = zoomRanges(prefectures?.resolutions ?? [], state.choices["japan/prefectures"] ?? "auto");
  const prefecturesFrom = Math.min(MAX_ZOOM, ...[...fine.values()].flatMap((range) => (range ? [range[0]] : [])));
  const coasts: LayerSpecification[] = [];
  const fills: LayerSpecification[] = [];
  type Piece = { id: string; source: string; "source-layer": string; filter?: FilterSpecification; maxzoom?: number };
  const add = (piece: Piece, color: string, range: ZoomRange | null): void => {
    const placed = (spec: LayerSpecification): LayerSpecification => place(GROUND, { spec, stage: STAGE.land, opacity: [] }, range, state.revealed);
    const coast = { "line-color": PALETTE.coast, "line-width": 1.4 };
    coasts.push(placed({ ...piece, id: `${piece.id}-coast`, type: "line", layout: { "line-join": "round" }, paint: coast }));
    fills.push(placed({ ...piece, type: "fill", paint: { "fill-color": color } }));
  };
  const coarse = zoomRanges(countries.resolutions, state.choices[countries.id] ?? "auto");
  for (const res of countries.resolutions) {
    const at = { source: sourceId(countries, res), "source-layer": tilesOf(countries) };
    const range = coarse.get(res.id) ?? null;
    add({ id: `${at.source}:land`, ...at, filter: ["!", JAPAN] }, PALETTE.land, range);
    add({ id: `${at.source}:japan`, ...at, filter: JAPAN, maxzoom: prefecturesFrom }, PALETTE.japan, range);
  }
  if (prefectures) {
    for (const res of prefectures.resolutions) {
      const source = sourceId(prefectures, res);
      add({ id: `${source}:land`, source, "source-layer": tilesOf(prefectures) }, PALETTE.japan, fine.get(res.id) ?? null);
    }
  }
  // 海岸は、面の輪郭を塗りより下に引き、海の側の半分だけを見せる。隣の国や都道府県と接する輪郭は、両側の塗りに隠れる
  return [...coasts, ...fills];
}

export function buildStyle(catalog: Catalog, base: URL, state: ViewState): StyleSpecification {
  const sources: Record<string, SourceSpecification> = { graticule: { type: "geojson", data: graticule(5) } };
  const layers: LayerSpecification[] = [
    { id: "ocean", type: "background", paint: { "background-color": PALETTE.ocean } },
    {
      id: "graticule",
      type: "line",
      source: "graticule",
      paint: {
        "line-color": ["case", ["get", "major"], PALETTE.graticuleMajor, PALETTE.graticule],
        "line-width": ["case", ["get", "major"], 0.9, 0.5],
        "line-opacity": state.revealed >= STAGE.graticule ? 0.9 : 0,
        "line-opacity-transition": FADE,
      },
    },
    ...ground(catalog, state),
  ];
  const rank = (layer: CatalogLayer): number => {
    const i = DRAW_ORDER.indexOf(layer.id);
    return i < 0 ? DRAW_ORDER.length : i;
  };
  for (const layer of [...catalog.layers].sort((a, b) => rank(a) - rank(b))) {
    const ranges = zoomRanges(layer.resolutions, state.choices[layer.id] ?? "auto");
    const owner = ownerOf(layer, state);
    for (const res of layer.resolutions) {
      sources[sourceId(layer, res)] = { type: "vector", url: `pmtiles://${new URL(res.pmtiles, base).href}` };
      for (const part of partsFor(layer, res, state)) {
        layers.push(place(owner, part, ranges.get(res.id) ?? null, state.revealed));
      }
    }
  }
  return {
    version: 8,
    projection: { type: "globe" },
    sky: {
      "sky-color": PALETTE.sky,
      "horizon-color": PALETTE.horizon,
      "sky-horizon-blend": 0.6,
      "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 0.9, 4, 0.7, 6, 0],
    },
    sources,
    layers,
  };
}

