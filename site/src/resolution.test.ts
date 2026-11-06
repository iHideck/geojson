import assert from "node:assert/strict";
import { test } from "node:test";
import type { Resolution } from "./catalog.ts";
import { MAX_ZOOM, zoomRanges } from "./resolution.ts";

const res = (id: string, minzoom: number, maxzoom: number): Resolution => ({ id, minzoom, maxzoom, pmtiles: "" });
const countries = [res("50m", 2, 6), res("110m", 0, 3)];

test("自動では、粗い解像度のタイルがある最大ズームで細かい解像度に切り替える", () => {
  assert.deepEqual(
    zoomRanges(countries, "auto"),
    new Map([
      ["50m", [3, MAX_ZOOM]],
      ["110m", [0, 3]],
    ]),
  );
});

test("細かい解像度を選ぶと、そのタイルが無い低いズームだけを粗い解像度で埋める", () => {
  assert.deepEqual(
    zoomRanges(countries, "50m"),
    new Map([
      ["50m", [2, MAX_ZOOM]],
      ["110m", [0, 2]],
    ]),
  );
});

test("粗い解像度を選ぶと、細かい解像度は描かない", () => {
  assert.deepEqual(
    zoomRanges(countries, "110m"),
    new Map([
      ["50m", null],
      ["110m", [0, MAX_ZOOM]],
    ]),
  );
});

test("解像度が1つなら、タイルがある最小ズームから先をすべて受け持つ", () => {
  assert.deepEqual(zoomRanges([res("medium", 2, 8)], "auto"), new Map([["medium", [2, MAX_ZOOM]]]));
});

test("最小ズームより低いズームでは、粗い解像度も描かない（市区町村境はズームしたときだけ読む）", () => {
  const municipalities = [res("medium", 7, 10), res("low", 5, 8)];
  assert.deepEqual(
    zoomRanges(municipalities, "auto"),
    new Map([
      ["medium", [8, MAX_ZOOM]],
      ["low", [5, 8]],
    ]),
  );
});
