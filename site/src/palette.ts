// Midnight Chart（夜の海図）の配色
export const PALETTE = {
  ocean: "#0b1733",
  land: "#18254a",
  japan: "#1f3160",
  coast: "#33487a",
  graticule: "#1c2d57",
  graticuleMajor: "#2a3f72",
  label: "#d6e0f5",
  halo: "#0b1733",
  highlight: "#ffe3ad",
  sky: "#050b1c",
  horizon: "#20447f",
} as const;

export type LineLook = {
  color: string;
  // ズーム 3・6・9 での太さ（px）
  width: readonly [number, number, number];
  // 線の太さを単位にした破線の並び
  dash?: readonly number[];
  glow?: number;
};

// レイヤーごとの線の描き方。境界の線は、PMTiles の borders を使う
export const LINES: Record<string, LineLook> = {
  "world/countries": { color: "#f4b35e", width: [1, 1.8, 2.4], glow: 0.34 },
  "japan/prefectures": { color: "#86d6f7", width: [0.7, 1.3, 1.8], dash: [4, 2], glow: 0.16 },
  "japan/municipalities": { color: "#a4b4d6", width: [0.5, 0.9, 1.2], dash: [1, 1.6] },
  "world/territorial-seas": { color: "#ea9bd2", width: [0.8, 1.4, 1.8], dash: [3, 2] },
  "world/contiguous-zones": { color: "#5fd4ab", width: [0.7, 1.2, 1.6], dash: [5, 2, 1, 2] },
  "world/eez": { color: "#efe27e", width: [0.9, 1.7, 2.2], dash: [8, 3] },
  "world/baselines": { color: "#f2f5fb", width: [0.6, 1, 1.4], dash: [1, 1.5] },
  "world/high-seas": { color: "#efe27e", width: [0.4, 0.6, 0.8] },
};

export const FALLBACK_LINE: LineLook = { color: "#d6e0f5", width: [0.6, 1, 1.4] };

export const POINT = { color: "#d6e0f5", radius: [1.6, 2.6, 3.4] } as const;
