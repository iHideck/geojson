import type { Feature, FeatureCollection } from "geojson";
import type { ExpressionSpecification, LayerSpecification, SourceSpecification, StyleSpecification } from "maplibre-gl";
import type { Catalog, CatalogLayer, Resolution } from "./catalog.ts";
import { FALLBACK_LINE, LINES, type LineLook, PALETTE, POINT } from "./palette.ts";
import { type Choice, type ZoomRange, zoomRanges } from "./resolution.ts";

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

// 地図に何をどう描くか。ビューアの状態はこれだけで、スタイルはここから毎回作る
export type ViewState = {
  // 目録のレイヤーの id ごとの解像度の選び方。無ければ自動
  choices: Readonly<Record<string, Choice>>;
};

export const sourceId = (layer: CatalogLayer, res: Resolution): string => `${layer.id}@${res.id}`;

function width(look: LineLook, factor = 1): ExpressionSpecification {
  const [z3, z6, z9] = look.width.map((w) => w * factor) as [number, number, number];
  return ["interpolate", ["linear"], ["zoom"], 3, z3, 6, z6, 9, z9];
}

function graticule(step: number): FeatureCollection {
  const features: Feature[] = [];
  const line = (coordinates: number[][], major: boolean): Feature => ({
    type: "Feature",
    properties: { major },
    geometry: { type: "LineString", coordinates },
  });
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

function layersFor(layer: CatalogLayer, res: Resolution): LayerSpecification[] {
  const source = sourceId(layer, res);
  const tiles = layer.id.split("/").at(-1) as string;
  const id = (part: string): string => `${source}:${part}`;
  const look = LINES[layer.id] ?? FALLBACK_LINE;
  if (layer.geometry === "point") {
    return [
      {
        id: id("point"),
        type: "circle",
        source,
        "source-layer": tiles,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, POINT.radius[0], 6, POINT.radius[1], 9, POINT.radius[2]],
          "circle-color": PALETTE.ocean,
          "circle-stroke-color": POINT.color,
          "circle-stroke-width": 1.2,
        },
      },
      {
        id: id("label"),
        type: "symbol",
        source,
        "source-layer": tiles,
        minzoom: 4.5,
        layout: {
          "text-field": ["get", "name_ja"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 4.5, 10, 9, 13],
          "text-anchor": "left",
          "text-offset": [0.7, 0],
          "text-padding": 4,
        },
        paint: { "text-color": PALETTE.label, "text-halo-color": PALETTE.halo, "text-halo-width": 1.4 },
      },
    ];
  }
  const out: LayerSpecification[] = [];
  if (layer.id === "world/countries") {
    out.push(
      {
        id: id("land"),
        type: "fill",
        source,
        "source-layer": tiles,
        paint: { "fill-color": ["case", ["==", ["get", "iso_a3"], "JPN"], PALETTE.japan, PALETTE.land] },
      },
      {
        id: id("coast"),
        type: "line",
        source,
        "source-layer": tiles,
        paint: { "line-color": PALETTE.coast, "line-width": 0.7 },
      },
    );
  } else if (layer.geometry === "polygon") {
    // 地物を選べるように、見えない塗りを敷く
    out.push({
      id: id("area"),
      type: "fill",
      source,
      "source-layer": tiles,
      paint: { "fill-color": "#000000", "fill-opacity": 0 },
    });
  }
  const lines = layer.geometry === "polygon" ? "borders" : tiles;
  if (look.glow) {
    out.push({
      id: id("glow"),
      type: "line",
      source,
      "source-layer": lines,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: { "line-color": look.color, "line-width": width(look, 3.5), "line-blur": 4, "line-opacity": look.glow },
    });
  }
  out.push({
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
  });
  return out;
}

function withRange(layer: LayerSpecification, range: ZoomRange | null, from = 0): LayerSpecification {
  if (!range || range[1] <= from) {
    return { ...layer, layout: { ...layer.layout, visibility: "none" } } as LayerSpecification;
  }
  return { ...layer, minzoom: Math.max(layer.minzoom ?? 0, range[0], from), maxzoom: range[1] };
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
      for (const own of layersFor(layer, res)) {
        layers.push(withRange(own, ranges.get(res.id) ?? null, DRAW_FROM[layer.id]));
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
