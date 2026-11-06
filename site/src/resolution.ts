import type { Resolution } from "./catalog.ts";

// 解像度を表示するズームの範囲 [最小, 最大)。地図の最大ズームより先も描く
export type ZoomRange = readonly [number, number];
export type Choice = "auto" | string;

export const MAX_ZOOM = 24;

/**
 * 解像度ごとに、表示するズームの範囲を決める。表示しない解像度は null。
 *
 * 自動では、粗い解像度のタイルがある最大ズームで、細かい解像度に切り替える（データを作る側が、隣どうしの
 * ズームに隙間を作らない）。手動で選んだ解像度は、タイルがある最小ズームから先をすべて受け持つ。
 * タイルより低いズームは拡大して描けないので、そこだけは粗い解像度で埋める。
 */
export function zoomRanges(resolutions: readonly Resolution[], choice: Choice): Map<string, ZoomRange | null> {
  const auto = new Map<string, ZoomRange>();
  resolutions.forEach((res, i) => {
    const coarser = resolutions[i + 1];
    const finer = resolutions[i - 1];
    auto.set(res.id, [coarser ? coarser.maxzoom : res.minzoom, finer ? res.maxzoom : MAX_ZOOM]);
  });
  const chosen = resolutions.findIndex((res) => res.id === choice);
  if (chosen < 0) {
    return new Map(resolutions.map((res) => [res.id, auto.get(res.id) ?? null]));
  }
  const picked = resolutions[chosen] as Resolution;
  return new Map(
    resolutions.map((res, i): [string, ZoomRange | null] => {
      if (i === chosen) return [res.id, [res.minzoom, MAX_ZOOM]];
      if (i < chosen) return [res.id, null];
      const [min, max] = auto.get(res.id) as ZoomRange;
      const top = Math.min(max, picked.minzoom);
      return [res.id, min < top ? [min, top] : null];
    }),
  );
}
