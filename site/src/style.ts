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
import { type ZoomRange, zoomRanges } from "./resolution.ts";
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

// 海域は、隣と接する線だけでなく、外側の線（200 海里などの限界）も描く。名前は出さない
const OUTLINED = new Set(["world/eez", "world/territorial-seas", "world/contiguous-zones", "world/high-seas"]);

// 名前を出し始めるズーム
const LABEL_FROM: Readonly<Record<string, number>> = { "japan/prefectures": 5, "japan/municipalities": 9 };

// 演出で見せる順番。0 は最初から見せる
const STAGE = { land: 0, graticule: 1, borders: 2, japan: 3, labels: 4 } as const;
const FADE = { duration: 1000, delay: 0 };

// 地図の上で選べる部分。前にあるものを先に選ぶ
export const PICK_PARTS = ["point", "area", "land"] as const;

type Part = {
  spec: LayerSpecification;
  stage: number;
  // 不透明度を持つ描き方の名前と、レイヤーの不透明度が 1 のときの値
  opacity: [string, number][];
};

export const sourceId = (layer: CatalogLayer, res: Resolution): string => `${layer.id}@${res.id}`;

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
  const tiles = layer.id.split("/").at(-1) as string;
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
  if (layer.id === "world/countries") {
    parts.push(
      {
        spec: {
          id: id("land"),
          type: "fill",
          source,
          "source-layer": tiles,
          paint: { "fill-color": ["case", ["==", ["get", "iso_a3"], "JPN"], PALETTE.japan, PALETTE.land] },
        },
        stage: STAGE.land,
        opacity: [["fill-opacity", 1]],
      },
      {
        spec: {
          id: id("coast"),
          type: "line",
          source,
          "source-layer": tiles,
          paint: { "line-color": PALETTE.coast, "line-width": 0.7 },
        },
        stage: STAGE.land,
        opacity: [["line-opacity", 1]],
      },
    );
  } else if (layer.geometry === "polygon") {
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
  const lines = layer.geometry === "polygon" && !OUTLINED.has(layer.id) ? "borders" : tiles;
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
  if (layer.geometry === "polygon" && !OUTLINED.has(layer.id)) {
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

function place(layer: CatalogLayer, part: Part, range: ZoomRange | null, state: ViewState): LayerSpecification {
  const spec = part.spec;
  const from = DRAW_FROM[layer.id] ?? 0;
  if (state.hidden.has(layer.id) || !range || range[1] <= from) {
    return { ...spec, layout: { ...spec.layout, visibility: "none" } } as LayerSpecification;
  }
  const revealed = state.revealed >= part.stage;
  const layerOpacity = state.opacity[layer.id] ?? 1;
  const paint: Record<string, unknown> = { ...spec.paint };
  for (const [property, base] of part.opacity) {
    paint[property] = revealed ? base * layerOpacity : 0;
    paint[`${property}-transition`] = FADE;
  }
  return {
    ...spec,
    minzoom: Math.max(spec.minzoom ?? 0, range[0], from),
    maxzoom: Math.min(spec.maxzoom ?? range[1], range[1]),
    paint,
  } as LayerSpecification;
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
  ];
  const rank = (layer: CatalogLayer): number => {
    const i = DRAW_ORDER.indexOf(layer.id);
    return i < 0 ? DRAW_ORDER.length : i;
  };
  for (const layer of [...catalog.layers].sort((a, b) => rank(a) - rank(b))) {
    const ranges = zoomRanges(layer.resolutions, state.choices[layer.id] ?? "auto");
    for (const res of layer.resolutions) {
      sources[sourceId(layer, res)] = { type: "vector", url: `pmtiles://${new URL(res.pmtiles, base).href}` };
      for (const part of partsFor(layer, res, state)) {
        layers.push(place(layer, part, ranges.get(res.id) ?? null, state));
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

